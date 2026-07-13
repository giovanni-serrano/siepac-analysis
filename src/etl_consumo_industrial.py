"""
etl_consumo_industrial.py — Consumo eléctrico del sector industrial
====================================================
Etapa del pipeline : ETL
Entradas           : data/raw/consumo_industrial/*.xlsx (hoja "1.Industrial")
Salidas            : data/processed/consumo_industrial.csv (tidy)
Alimenta           : ECO6
Fuente de datos    : SIELAC-OLADE (Series de oferta y demanda)

Uso:  python src/etl_consumo_industrial.py   (ejecutar desde la raíz del proyecto)

Notas metodológicas:
  - La hoja viene en bloques verticales por año ("Industrial - AAAA");
    se detectan por regex y se filtran solo los 6 países del SIEPAC.
  - Conversión GWh -> kWh (unidad base de energía del proyecto).
  - Validación estricta: nulos en el valor o países inesperados abortan
    sin escribir el CSV.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
import re
import sys
from pathlib import Path

import pandas as pd

from config_siepac import GWH_A_KWH, PAISES_SIEPAC, DIR_RAW, DIR_PROCESSED
from etl_comun import encontrar_archivo_entrada

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

# --- 1. Rutas (relativas a la raiz del proyecto, funcionan en Windows y Mac/Linux) ---
RAW_DIR = DIR_RAW / "consumo_industrial"
PROCESSED_DIR = DIR_PROCESSED

ARCHIVO_SALIDA = PROCESSED_DIR / "consumo_industrial.csv"

HOJA = "1.Industrial"

PAISES_VALIDOS = set(PAISES_SIEPAC)
YEAR_PATTERN = re.compile(r"Industrial - (\d{4})")


def extraer_datos(path_excel: Path, hoja: str) -> pd.DataFrame:
    """Lee la hoja en bloques verticales por año y devuelve un DataFrame tidy."""
    df_raw = pd.read_excel(path_excel, sheet_name=hoja, header=None)

    registros = []
    anio_actual = None

    for _, fila in df_raw.iterrows():
        col_a = fila[0]
        col_b = fila[1]

        if isinstance(col_a, str):
            match = YEAR_PATTERN.search(col_a)
            if match:
                anio_actual = int(match.group(1))
                continue

        if col_a in PAISES_VALIDOS and anio_actual is not None:
            registros.append({
                "pais": col_a,
                "anio": anio_actual,
                "valor_gwh": col_b,
            })

    return pd.DataFrame(registros)


def transformar(df_tidy: pd.DataFrame) -> pd.DataFrame:
    """Aplica la regla de unidades del proyecto: GWh -> kWh (unidad base)."""
    df_tidy = df_tidy.copy()
    df_tidy["valor_kwh"] = df_tidy["valor_gwh"] * GWH_A_KWH
    df_tidy["fuente"] = "SIELAC-OLADE"
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
                    "Revisar bloques faltantes.", n_esperado, len(df_tidy))

    faltantes = df_tidy["valor_gwh"].isna().sum()
    if faltantes:
        errores_graves.append(f"Hay {faltantes} valores nulos en valor_gwh.")

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