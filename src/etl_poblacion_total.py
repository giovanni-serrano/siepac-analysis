"""
etl_poblacion_total.py — Población total por país
====================================================
Etapa del pipeline : ETL
Entradas           : data/raw/poblacion_total/*.xlsx (hoja "datos", formato CEPAL)
Salidas            : data/processed/poblacion_total.csv (tidy)
Alimenta           : ECO1 (y denominadores per cápita en general)
Fuente de datos    : CEPAL-CELADE

Uso:  python src/etl_poblacion_total.py   (ejecutar desde la raíz del proyecto)

Notas metodológicas:
  - La hoja "datos" trae la población desagregada por sexo; se filtra
    "Ambos sexos" para quedarse con el total.
  - Conversión miles de habitantes -> habitantes (unidad base).
  - Validación estricta: nulos en el valor o países inesperados abortan
    sin escribir el CSV.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
import sys
from pathlib import Path

import pandas as pd

from config_siepac import PAISES_SIEPAC, DIR_RAW, DIR_PROCESSED
from etl_comun import encontrar_archivo_entrada

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

# --- 1. Rutas (relativas a la raiz del proyecto, funcionan en Windows y Mac/Linux) ---
RAW_DIR = DIR_RAW / "poblacion_total"
PROCESSED_DIR = DIR_PROCESSED

ARCHIVO_SALIDA = PROCESSED_DIR / "poblacion_total.csv"

HOJA = "datos"

PAISES_VALIDOS = set(PAISES_SIEPAC)

# En el formato CEPAL, la hoja "datos" trae la poblacion desagregada por
# sexo (Ambos sexos / Hombres / Mujeres). Para consumo_final_total no existia
# este problema porque el archivo SIELAC-OLADE ya venia sin desagregar.
SEXO_TOTAL = "Ambos sexos"


def extraer_datos(path_excel: Path, hoja: str) -> pd.DataFrame:
    """Lee la hoja 'datos' (formato tabular CEPAL) y devuelve un DataFrame tidy.

    A diferencia de los archivos SIELAC-OLADE (bloques verticales por anio),
    aqui cada fila ya es un registro individual: pais, sexo, anio, valor.
    No hay que iterar detectando encabezados de bloque; solo filtrar y
    renombrar columnas.
    """
    df_raw = pd.read_excel(path_excel, sheet_name=hoja)

    df_filtrado = df_raw[
        (df_raw["País__ESTANDAR"].isin(PAISES_VALIDOS))
        & (df_raw["Sexo"] == SEXO_TOTAL)
    ].copy()

    df_tidy = df_filtrado.rename(columns={
        "País__ESTANDAR": "pais",
        "Años__ESTANDAR": "anio",
        "value": "valor_miles_hab",
    })[["pais", "anio", "valor_miles_hab"]]

    df_tidy["anio"] = df_tidy["anio"].astype(int)

    return df_tidy.reset_index(drop=True)


def transformar(df_tidy: pd.DataFrame) -> pd.DataFrame:
    """Convierte miles de habitantes a habitantes (unidad base) y agrega fuente."""
    df_tidy = df_tidy.copy()
    df_tidy["valor_habitantes"] = df_tidy["valor_miles_hab"] * 1_000
    df_tidy["fuente"] = "CEPAL-CELADE"
    df_tidy = df_tidy.sort_values(["anio", "pais"]).reset_index(drop=True)
    return df_tidy


def validar(df_tidy: pd.DataFrame) -> None:
    """Chequeos antes de guardar. Los problemas graves (nulos en el valor,
    paises inesperados) abortan sin escribir el CSV; el conteo de filas
    distinto al esperado solo avisa."""
    errores_graves = []

    n_esperado = len(PAISES_VALIDOS) * df_tidy["anio"].nunique()
    if len(df_tidy) != n_esperado:
        log.warning("Se esperaban %d filas, se obtuvieron %d. "
                    "Revisar filas faltantes.", n_esperado, len(df_tidy))

    faltantes = df_tidy["valor_habitantes"].isna().sum()
    if faltantes:
        errores_graves.append(
            f"Hay {faltantes} valores nulos en valor_habitantes.")

    paises_encontrados = set(df_tidy["pais"].unique())
    if paises_encontrados != PAISES_VALIDOS:
        errores_graves.append(
            f"Paises distintos a los esperados: {paises_encontrados}")

    if errores_graves:
        for e in errores_graves:
            log.error(e)
        sys.exit("VALIDACIÓN FALLIDA — el CSV no fue escrito.")


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    archivo_entrada = encontrar_archivo_entrada(RAW_DIR)
    log.info("Leyendo: %s", archivo_entrada.name)

    df_tidy = extraer_datos(archivo_entrada, HOJA)
    df_tidy = transformar(df_tidy)
    validar(df_tidy)

    df_tidy.to_csv(ARCHIVO_SALIDA, index=False, encoding="utf-8-sig")

    log.info("OK: %d filas guardadas en: %s", len(df_tidy), ARCHIVO_SALIDA)
    log.info("Vista previa:\n%s", df_tidy.head(10).to_string(index=False))


if __name__ == "__main__":
    main()