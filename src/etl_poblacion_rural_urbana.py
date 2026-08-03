"""
etl_poblacion_rural_urbana.py - Población rural y urbana por país
=================================================================
Etapa del pipeline : ETL
Entradas           : data/raw/poblacion_rural_urbana/*.csv
Salidas            : data/processed/poblacion_rural_urbana.csv (tidy)
Alimenta           : SOC3_RURAL y SOC3_URB (ponderadores regionales)
Fuente de datos    : Banco Mundial, Indicadores del Desarrollo Mundial
                     (SP.RUR.TOTL y SP.URB.TOTL)

Uso:  python src/etl_poblacion_rural_urbana.py
      (ejecutar desde la raíz del proyecto)

Notas metodológicas:
  - Las poblaciones se conservan en habitantes, unidad base del proyecto.
  - La población total solo valida que rural + urbana cierre; los agregados
    SOC3 usan directamente la población de cada zona.
  - La cobertura debe ser el panel completo SIEPAC 2020-2024: seis países
    por cinco años, sin duplicados ni valores faltantes.

Autor: Luis Giovanni Serrano Bello - Tesis SIEPAC, UNI Nicaragua
"""

import logging
import sys
from pathlib import Path

import pandas as pd

from config_siepac import (ANIOS_ANALISIS, CODIGOS_ISO3, DIR_PROCESSED,
                           DIR_RAW, PAISES_SIEPAC)
from etl_comun import encontrar_archivo_entrada

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

RAW_DIR = DIR_RAW / "poblacion_rural_urbana"
ARCHIVO_SALIDA = DIR_PROCESSED / "poblacion_rural_urbana.csv"

COLUMNAS = [
    "pais", "codigo_iso3", "anio", "poblacion_rural_hab",
    "poblacion_urbana_hab", "poblacion_total_hab",
]
COLUMNAS_POBLACION = [
    "poblacion_rural_hab", "poblacion_urbana_hab", "poblacion_total_hab",
]
ISO_POR_PAIS = {pais: iso for iso, pais in CODIGOS_ISO3.items()}
FUENTE = ("Banco Mundial - Indicadores del Desarrollo Mundial "
          "(SP.RUR.TOTL; SP.URB.TOTL)")


def extraer_datos(ruta: Path) -> pd.DataFrame:
    """Lee la matriz tidy y normaliza tipos sin alterar magnitudes."""
    df = pd.read_csv(ruta, encoding="utf-8-sig")
    faltantes = [c for c in COLUMNAS if c not in df.columns]
    if faltantes:
        sys.exit("VALIDACIÓN FALLIDA - faltan columnas requeridas: "
                 + ", ".join(faltantes))

    df = df[COLUMNAS].copy()
    df["pais"] = df["pais"].astype(str).str.strip()
    df["codigo_iso3"] = df["codigo_iso3"].astype(str).str.strip()
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce")
    for columna in COLUMNAS_POBLACION:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")
    return df


def validar(df: pd.DataFrame) -> None:
    """Valida el panel y la identidad población rural + urbana = total."""
    errores = []

    if df[COLUMNAS].isna().any().any():
        errores.append("Hay valores vacíos o no numéricos.")

    duplicados = df.duplicated(["pais", "anio"]).sum()
    if duplicados:
        errores.append(f"Hay {duplicados} filas país-año duplicadas.")

    paises = set(df["pais"].dropna())
    if paises != set(PAISES_SIEPAC):
        errores.append(f"Países distintos a los esperados: {sorted(paises)}")

    anios = set(df["anio"].dropna().astype(int))
    if anios != set(ANIOS_ANALISIS):
        errores.append(f"Años distintos a los esperados: {sorted(anios)}")

    esperado = len(PAISES_SIEPAC) * len(ANIOS_ANALISIS)
    if len(df) != esperado:
        errores.append(f"Se esperaban {esperado} filas y hay {len(df)}.")

    for _, fila in df.dropna().iterrows():
        pais, anio = fila["pais"], int(fila["anio"])
        if fila["codigo_iso3"] != ISO_POR_PAIS.get(pais):
            errores.append(
                f"Código ISO3 incorrecto para {pais} {anio}: "
                f"{fila['codigo_iso3']}.")
        if any(fila[c] <= 0 for c in COLUMNAS_POBLACION):
            errores.append(f"Población no positiva en {pais} {anio}.")
        if any(not float(fila[c]).is_integer()
               for c in COLUMNAS_POBLACION):
            errores.append(f"Población no entera en {pais} {anio}.")
        suma_zonas = (fila["poblacion_rural_hab"]
                      + fila["poblacion_urbana_hab"])
        if suma_zonas != fila["poblacion_total_hab"]:
            errores.append(
                f"Rural + urbana no coincide con total en {pais} {anio}.")

    if errores:
        for error in errores:
            log.error(error)
        sys.exit("VALIDACIÓN FALLIDA - el CSV procesado no fue escrito.")


def contrastar_poblacion_total(df: pd.DataFrame) -> None:
    """Advierte si la matriz zonal se aleja de la población total del ETL."""
    ruta_total = DIR_PROCESSED / "poblacion_total.csv"
    if not ruta_total.exists():
        log.warning("Sin %s: se omite el contraste de población total.",
                    ruta_total.name)
        return

    total = pd.read_csv(ruta_total)[["pais", "anio", "valor_habitantes"]]
    cruce = df.merge(total, on=["pais", "anio"], how="left")
    diferencia = ((cruce["poblacion_total_hab"]
                   / cruce["valor_habitantes"] - 1).abs())
    max_pct = float(diferencia.max() * 100)
    if cruce["valor_habitantes"].isna().any() or max_pct > 0.1:
        log.warning("La diferencia máxima frente a poblacion_total.csv es "
                    "%.3f %%, superior a la tolerancia de 0.1 %%.", max_pct)
    else:
        log.info("Cruce con poblacion_total.csv: diferencia máxima %.4f %%.",
                 max_pct)


def transformar(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena el panel, fija enteros y agrega trazabilidad de la matriz."""
    salida = df.copy()
    salida["anio"] = salida["anio"].astype(int)
    for columna in COLUMNAS_POBLACION:
        salida[columna] = salida[columna].astype("int64")
    orden_pais = {pais: i for i, pais in enumerate(PAISES_SIEPAC)}
    salida["_orden_pais"] = salida["pais"].map(orden_pais)
    salida = salida.sort_values(["_orden_pais", "anio"]).drop(
        columns="_orden_pais")
    salida["fuente"] = FUENTE
    return salida.reset_index(drop=True)


def main() -> None:
    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    archivo = encontrar_archivo_entrada(RAW_DIR, "*.csv")
    log.info("Leyendo: %s", archivo.name)

    df = extraer_datos(archivo)
    validar(df)
    contrastar_poblacion_total(df)
    salida = transformar(df)
    salida.to_csv(ARCHIVO_SALIDA, index=False, encoding="utf-8-sig")

    log.info("OK: %d filas guardadas en: %s", len(salida), ARCHIVO_SALIDA)
    log.info("Población rural: %s habitantes; urbana: %s habitantes.",
             f"{salida['poblacion_rural_hab'].sum():,.0f}",
             f"{salida['poblacion_urbana_hab'].sum():,.0f}")


if __name__ == "__main__":
    main()
