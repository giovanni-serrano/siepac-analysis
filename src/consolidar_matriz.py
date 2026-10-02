"""
consolidar_matriz.py — Consolidación de los CSVs procesados
====================================================
Etapa del pipeline : consolidación
Entradas           : los 9 CSVs de data/processed/ (uno por variable,
                     producidos por los ETL)
Salidas            : data/processed/matriz_consolidada_tidy.csv (largo:
                     una fila por pais-anio-variable) y
                     data/processed/matriz_consolidada_wide.csv (ancho:
                     una fila por pais-anio, una columna por variable)
Alimenta           : generar_matriz_indicadores.py (hoja Datos_Base)
Fuente de datos    : agrega las salidas de los ETL (OLADE, CEPAL,
                     Banco Mundial)

Uso:  python src/consolidar_matriz.py   (ejecutar desde la raíz del proyecto)

Notas metodológicas:
  - Unidades base: kWh (energía), USD constantes 2015 (macro),
    USD corrientes/MWh (tarifa), habitantes (población).
  - Valida panel completo (6 países × 5 años), nombres de país canónicos
    y ausencia de celdas vacías en la matriz ancha.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
import sys
from pathlib import Path

import pandas as pd

from config_siepac import PAISES_SIEPAC, DIR_PROCESSED
from etl_comun import (fallar_validacion, validar_columnas, validar_panel,
                       validar_numericos)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

# Normalización defensiva de claves geográficas antes de las uniones.
# Evita separar registros equivalentes por diferencias ortográficas.
MAPEO_PAISES = {
    "Panama": "Panamá",
}

# Mapa de consolidación: para cada CSV de origen, qué columnas de valor
# se extraen y cómo se renombran como 'variable' en la matriz tidy.
# Solo se llevan las columnas en UNIDAD BASE (kWh, USD, habitantes,
# USD/MWh) según las unidades base del proyecto; las columnas redundantes
# en GWh o miles de habitantes se quedan en el CSV de origen como referencia.
MAPA_VARIABLES = {
    "consumo_final_total.csv": {
        "valor_kwh": "consumo_final_total_kwh",
    },
    "consumo_industrial.csv": {
        "valor_kwh": "consumo_industrial_kwh",
    },
    "poblacion_total.csv": {
        "valor_habitantes": "poblacion_habitantes",
    },
    "pib.csv": {
        "valor_usd": "pib_usd_const2015",
    },
    "valor_agregado_industrial.csv": {
        # Se llevan ambas: el USD ya calculado (lo que usa ECO6) y el
        # % del PIB original (trazabilidad del cálculo).
        "valor_usd": "vai_usd_const2015",
        "vai_pct_pib": "vai_pct_pib",
    },
    "produccion_bruta.csv": {
        "valor_kwh": "produccion_bruta_kwh",
    },
    "tarifa_electrica_media.csv": {
        "valor_usd_mwh": "tarifa_usd_mwh",
    },
    "generacion_por_tipo_de_fuente.csv": {
        "hidro_kwh": "gen_hidro_kwh",
        "geotermia_kwh": "gen_geotermia_kwh",
        "eolica_kwh": "gen_eolica_kwh",
        "solar_kwh": "gen_solar_kwh",
        "biomasa_kwh": "gen_biomasa_kwh",
        "renovable_kwh": "gen_renovable_kwh",
        "fosil_kwh": "gen_fosil_kwh",
        "total_kwh": "gen_total_kwh",
    },
    "importaciones_exportaciones.csv": {
        "importaciones_kwh": "importaciones_kwh",
        "exportaciones_kwh": "exportaciones_kwh",
    },
}


# ---------------------------------------------------------------------------
# EXTRACCIÓN
# ---------------------------------------------------------------------------

def extraer_datos(dir_processed: Path) -> dict[str, pd.DataFrame]:
    """Lee los CSVs de data/processed/ definidos en MAPA_VARIABLES.

    Devuelve un diccionario {nombre_archivo: DataFrame}. Todos los insumos
    del mapa son obligatorios para construir la matriz de la tesis.
    """
    datos = {}
    for nombre in MAPA_VARIABLES:
        ruta = dir_processed / nombre
        if not ruta.exists():
            fallar_validacion("consolidación", f"archivo requerido ausente: {ruta}")
        datos[nombre] = pd.read_csv(ruta)
        log.info("Leído: %s (%d filas)", nombre, len(datos[nombre]))
    return datos


def _validar_insumos(datos: dict) -> None:
    faltantes = set(MAPA_VARIABLES) - set(datos)
    inesperados = set(datos) - set(MAPA_VARIABLES)
    if faltantes or inesperados:
        fallar_validacion("consolidación", f"insumos faltantes: {sorted(faltantes)}; "
                          f"inesperados: {sorted(inesperados)}")
    for nombre, df in datos.items():
        validar_columnas(df, ["pais", "anio", "fuente", *MAPA_VARIABLES[nombre]], nombre)
        # El alias permitido debe normalizarse antes de detectar colisiones.
        normalizado = df.assign(pais=df["pais"].replace(MAPEO_PAISES))
        validar_panel(normalizado, nombre)
        validar_numericos(normalizado, list(MAPA_VARIABLES[nombre]), nombre)


# ---------------------------------------------------------------------------
# TRANSFORMACIÓN
# ---------------------------------------------------------------------------

def transformar(datos: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye la matriz tidy (larga) y la matriz wide (ancha).

    Matriz tidy: pais, anio, variable, valor, fuente, fuente_dato.
      - 'fuente_dato' solo aplica a la tarifa eléctrica (valores
        'real' o 'imputado_CAGR'); en las demás variables queda vacía.
    Matriz wide: una fila por pais-anio, una columna por variable.
      - Las celdas sin dato quedan como NaN (vacías). NO se rellenan
        con cero ni se interpolan: un hueco debe verse como hueco.
    """
    _validar_insumos(datos)
    bloques = []

    for nombre, df in datos.items():
        df = df.copy()

        # 1. Normalizar nombres de país ANTES de cualquier unión.
        df["pais"] = df["pais"].replace(MAPEO_PAISES)

        # 2. Pasar de columnas de valor a formato largo (melt).
        columnas_valor = MAPA_VARIABLES[nombre]
        id_vars = ["pais", "anio", "fuente"]
        # 'fuente_dato' existe solo en tarifa_electrica_media.csv
        if "fuente_dato" in df.columns:
            id_vars.append("fuente_dato")

        largo = df.melt(
            id_vars=id_vars,
            value_vars=list(columnas_valor.keys()),
            var_name="columna_origen",
            value_name="valor",
        )
        largo["variable"] = largo["columna_origen"].map(columnas_valor)
        largo = largo.drop(columns="columna_origen")

        if "fuente_dato" not in largo.columns:
            largo["fuente_dato"] = pd.NA

        bloques.append(largo)

    tidy = pd.concat(bloques, ignore_index=True)
    tidy = tidy[["pais", "anio", "variable", "valor", "fuente", "fuente_dato"]]
    tidy = tidy.sort_values(["variable", "pais", "anio"]).reset_index(drop=True)

    # 3. Matriz ancha: pivot pais-anio x variable.
    wide = tidy.pivot(
        index=["pais", "anio"],
        columns="variable",
        values="valor",
    ).reset_index()
    wide.columns.name = None
    # Orden de columnas estable y legible.
    orden = ["pais", "anio"] + sorted(c for c in wide.columns if c not in ("pais", "anio"))
    wide = wide[orden].sort_values(["pais", "anio"]).reset_index(drop=True)

    return tidy, wide


# ---------------------------------------------------------------------------
# VALIDACIÓN
# ---------------------------------------------------------------------------

def validar(tidy: pd.DataFrame, wide: pd.DataFrame, datos: dict) -> None:
    """Reporta conteos esperados vs reales, celdas vacías y cobertura."""
    _validar_insumos(datos)
    esperadas = {v for columnas in MAPA_VARIABLES.values() for v in columnas.values()}
    validar_columnas(tidy, ["pais", "anio", "variable", "valor"], "matriz tidy")
    presentes = set(tidy["variable"])
    if presentes != esperadas:
        fallar_validacion("matriz tidy", f"variables faltantes: {sorted(esperadas - presentes)}; "
                          f"inesperadas: {sorted(presentes - esperadas, key=str)}")
    for variable, grupo in tidy.groupby("variable"):
        validar_panel(grupo, f"matriz tidy / {variable}")
        validar_numericos(grupo, ["valor"], f"matriz tidy / {variable}")
    validar_panel(wide, "matriz wide")
    validar_numericos(wide, sorted(esperadas), "matriz wide")

    # Detalle de imputación en tarifa (transparencia metodológica).
    tarifa = tidy[tidy["variable"] == "tarifa_usd_mwh"]
    if not tarifa.empty:
        n_imp = (tarifa["fuente_dato"] == "imputado_CAGR").sum()
        log.info("Tarifa eléctrica: %d de %d valores imputados vía CAGR "
                 "(ver columna fuente_dato en la tidy)", n_imp, len(tarifa))


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("Carpeta de datos: %s", DIR_PROCESSED)
    log.info("1) Extracción")
    datos = extraer_datos(DIR_PROCESSED)

    log.info("2) Transformación")
    tidy, wide = transformar(datos)
    log.info("Matriz tidy: %d filas x %d columnas", tidy.shape[0], tidy.shape[1])
    log.info("Matriz wide: %d filas x %d columnas", wide.shape[0], wide.shape[1])

    validar(tidy, wide, datos)

    log.info("3) Guardado")
    ruta_tidy = DIR_PROCESSED / "matriz_consolidada_tidy.csv"
    ruta_wide = DIR_PROCESSED / "matriz_consolidada_wide.csv"
    tidy.to_csv(ruta_tidy, index=False, encoding="utf-8-sig")
    wide.to_csv(ruta_wide, index=False, encoding="utf-8-sig")
    log.info("Guardado: %s", ruta_tidy)
    log.info("Guardado: %s", ruta_wide)


if __name__ == "__main__":
    main()
