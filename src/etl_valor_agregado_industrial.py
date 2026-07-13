"""
etl_valor_agregado_industrial.py — Valor agregado industrial (VAI)
====================================================
Etapa del pipeline : ETL (requiere pib.csv: correr etl_pib.py ANTES)
Entradas           : data/raw/valor_agregado_industrial/*.xlsx (CEPALSTAT
                     ODS 9.2.1, NV_IND_MANF_CD) + data/processed/pib.csv
Salidas            : data/processed/valor_agregado_industrial.csv (tidy)
Alimenta           : ECO6
Fuente de datos    : CEPALSTAT × Banco Mundial (PIB)

Uso:  python src/etl_valor_agregado_industrial.py   (ejecutar desde la raíz)

Notas metodológicas:
  - El VAI viene como PORCENTAJE DEL PIB (tercer caso de la regla de
    moneda del proyecto); se reconstruye el valor absoluto:
    VAI_usd = (VAI% / 100) × PIB_real.
  - La hoja 'metadatos' de CEPAL confirma que la razón MVA/PIB usa ambos
    términos en USD constantes 2015, por lo que multiplicar por el PIB
    real del Banco Mundial es coherente.
  - vai_pct_pib (el % original) se conserva en la salida por trazabilidad.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
import sys
from pathlib import Path

import pandas as pd

from config_siepac import ANIOS_ANALISIS, PAISES_SIEPAC, DIR_RAW, DIR_PROCESSED

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

CARPETA_RAW = DIR_RAW / "valor_agregado_industrial"
RUTA_PIB = DIR_PROCESSED / "pib.csv"
RUTA_SALIDA = DIR_PROCESSED / "valor_agregado_industrial.csv"

# Ventana de análisis de la tesis (definida una sola vez en config_siepac).
ANIO_INICIO, ANIO_FIN = ANIOS_ANALISIS[0], ANIOS_ANALISIS[-1]

HOJA_DATOS = "datos"  # nombre de la hoja relevante en el export de CEPALSTAT

FUENTE = (
    "CEPALSTAT - ODS 9.2.1 NV_IND_MANF_CD (VAI manufacturero % del PIB) "
    "x PIB Banco Mundial NY.GDP.MKTP.KD (USD constantes 2015)"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)


# ---------------------------------------------------------------------------
# Extracción
# ---------------------------------------------------------------------------

def extraer_datos() -> pd.DataFrame:
    """Localiza el .xlsx en la carpeta raw y lee la hoja 'datos'.

    Es defensivo: falla con mensaje claro si no hay archivo, si hay más
    de uno (ambigüedad), o si la hoja esperada no existe.
    """
    archivos = sorted(CARPETA_RAW.glob("*.xlsx"))
    if not archivos:
        log.error("No se encontró ningún .xlsx en %s", CARPETA_RAW)
        sys.exit(1)
    if len(archivos) > 1:
        log.warning(
            "Hay %d archivos .xlsx en la carpeta; se usará el primero: %s",
            len(archivos), archivos[0].name,
        )
    ruta = archivos[0]
    log.info("Leyendo archivo raw: %s", ruta.name)

    # Verificamos que la hoja 'datos' exista antes de leerla.
    hojas = pd.ExcelFile(ruta).sheet_names
    if HOJA_DATOS not in hojas:
        log.error(
            "La hoja '%s' no existe. Hojas disponibles: %s. "
            "Revisa si CEPAL cambió el formato del export.",
            HOJA_DATOS, hojas,
        )
        sys.exit(1)

    df = pd.read_excel(ruta, sheet_name=HOJA_DATOS)
    log.info("Hoja '%s' leída: %d filas, columnas: %s",
             HOJA_DATOS, len(df), list(df.columns))
    return df


def cargar_pib() -> pd.DataFrame:
    """Carga el PIB ya procesado (requisito para reconstruir el VAI en USD)."""
    if not RUTA_PIB.exists():
        log.error(
            "No existe %s. Este ETL NECESITA el PIB procesado para "
            "convertir %% del PIB a USD. Ejecuta primero el ETL del PIB.",
            RUTA_PIB,
        )
        sys.exit(1)
    pib = pd.read_csv(RUTA_PIB)
    columnas_requeridas = {"pais", "anio", "valor_usd"}
    faltantes = columnas_requeridas - set(pib.columns)
    if faltantes:
        log.error("A pib.csv le faltan columnas: %s", faltantes)
        sys.exit(1)
    return pib[["pais", "anio", "valor_usd"]].rename(
        columns={"valor_usd": "pib_usd"}
    )


# ---------------------------------------------------------------------------
# Transformación
# ---------------------------------------------------------------------------

def transformar(df: pd.DataFrame, pib: pd.DataFrame) -> pd.DataFrame:
    """Filtra, valida la unidad y reconstruye el VAI en USD constantes 2015."""

    # 1. Nos quedamos solo con las columnas que necesitamos. Los nombres
    #    con doble guion bajo son así en el export de CEPALSTAT.
    columnas_esperadas = ["País__ESTANDAR", "Años__ESTANDAR", "value", "unit"]
    faltantes = [c for c in columnas_esperadas if c not in df.columns]
    if faltantes:
        log.error("Columnas faltantes en la hoja de datos: %s", faltantes)
        sys.exit(1)

    df = df[columnas_esperadas].rename(columns={
        "País__ESTANDAR": "pais",
        "Años__ESTANDAR": "anio",
        "value": "vai_pct_pib",
    })

    # 2. Tipos: el año puede venir como texto en otros exports de CEPAL,
    #    así que lo forzamos a numérico. Valores no convertibles -> NaN.
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce")
    df["vai_pct_pib"] = pd.to_numeric(df["vai_pct_pib"], errors="coerce")

    no_numericos = df["vai_pct_pib"].isna().sum()
    if no_numericos:
        log.warning(
            "%d filas con valor no numérico o vacío; se descartan:\n%s",
            no_numericos, df[df["vai_pct_pib"].isna()].to_string(index=False),
        )
        df = df.dropna(subset=["vai_pct_pib", "anio"])

    # 3. Filtro a países SIEPAC y rango de años del estudio.
    df = df[
        df["pais"].isin(PAISES_SIEPAC)
        & df["anio"].between(ANIO_INICIO, ANIO_FIN)
    ].copy()
    df["anio"] = df["anio"].astype(int)

    # 4. GUARDIA DE UNIDAD (crítica): este script asume el caso
    #    "porcentaje del PIB". Si la unidad declarada o el rango de
    #    valores no lo confirman, abortamos: aplicar %*PIB a un valor
    #    que ya está en USD produciría cifras absurdas sin aviso.
    unidades = df["unit"].dropna().unique().tolist()
    if unidades != ["Porcentaje"]:
        log.error(
            "Unidad inesperada: %s (se esperaba solo 'Porcentaje'). "
            "Revisa la regla de moneda antes de continuar.", unidades,
        )
        sys.exit(1)
    fuera_de_rango = df[(df["vai_pct_pib"] <= 0) | (df["vai_pct_pib"] >= 100)]
    if not fuera_de_rango.empty:
        log.error(
            "Valores fuera del rango (0, 100)%%; no parecen porcentajes:\n%s",
            fuera_de_rango.to_string(index=False),
        )
        sys.exit(1)
    log.info("Unidad confirmada: Porcentaje del PIB (caso 3 de la regla de moneda)")

    # 5. Merge con el PIB real. how='left' para detectar pares
    #    (pais, anio) sin PIB en vez de perderlos silenciosamente.
    df = df.merge(pib, on=["pais", "anio"], how="left")
    sin_pib = df[df["pib_usd"].isna()]
    if not sin_pib.empty:
        log.warning(
            "%d filas sin PIB en pib.csv; se descartan (nunca se imputa):\n%s",
            len(sin_pib),
            sin_pib[["pais", "anio"]].to_string(index=False),
        )
        df = df.dropna(subset=["pib_usd"])

    # 6. Reconstrucción del valor absoluto (regla de moneda, caso % del PIB):
    #    V2 = (VAI% / 100) * PIB_Real. Redondeamos a entero porque la
    #    unidad base del proyecto es "USD constantes 2015, valor entero".
    df["valor_usd"] = ((df["vai_pct_pib"] / 100) * df["pib_usd"]).round().astype("int64")

    df["fuente"] = FUENTE
    df = df[["pais", "anio", "vai_pct_pib", "valor_usd", "fuente"]]
    return df.sort_values(["pais", "anio"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Validación
# ---------------------------------------------------------------------------

def validar(df: pd.DataFrame) -> None:
    """Chequeos finales: nulos, conteo de filas y cobertura por país."""
    # Sin nulos en ninguna columna.
    nulos = df.isna().sum().sum()
    if nulos:
        log.error("El resultado tiene %d celdas nulas. Abortando.", nulos)
        sys.exit(1)

    # Conteo esperado: 6 países x 5 años = 30 filas. Si hay menos,
    # ya se loggeó el porqué arriba; aquí solo dejamos constancia.
    esperadas = len(PAISES_SIEPAC) * (ANIO_FIN - ANIO_INICIO + 1)
    if len(df) != esperadas:
        log.warning("Filas: %d (se esperaban %d). Revisa los WARNING previos.",
                    len(df), esperadas)
    else:
        log.info("Conteo de filas OK: %d", len(df))

    # Cobertura: qué países SIEPAC faltan por completo.
    faltan = set(PAISES_SIEPAC) - set(df["pais"].unique())
    if faltan:
        log.warning("Países SIEPAC sin datos en la salida: %s", sorted(faltan))

    # Sanidad de magnitudes: el VAI de estos países debe estar en el
    # orden de 10^8 a 10^11 USD. Fuera de eso, algo salió mal.
    if not df["valor_usd"].between(1e8, 1e12).all():
        log.error("Hay valores de VAI fuera del orden de magnitud esperado "
                  "(10^8 - 10^12 USD). Posible error de unidad. Abortando.")
        sys.exit(1)
    log.info("Órdenes de magnitud OK (min=%.3g, max=%.3g USD)",
             df["valor_usd"].min(), df["valor_usd"].max())


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------

def main() -> None:
    df_raw = extraer_datos()
    pib = cargar_pib()
    df = transformar(df_raw, pib)
    validar(df)
    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")
    log.info("CSV generado: %s (%d filas)", RUTA_SALIDA, len(df))
    log.info("Resultado completo:\n%s", df.to_string(index=False))


if __name__ == "__main__":
    main()