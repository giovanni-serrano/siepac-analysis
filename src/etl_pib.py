"""
etl_pib.py — PIB real (USD constantes 2015)
====================================================
Etapa del pipeline : ETL
Entradas           : data/raw/pib/API_*.csv (export del Banco Mundial)
Salidas            : data/processed/pib.csv (tidy)
Alimenta           : ECO2 y, de forma indirecta, ECO6 (reconstrucción del VAI)
Fuente de datos    : Banco Mundial — NY.GDP.MKTP.KD (US$ constantes de 2015)

Uso:  python src/etl_pib.py   (ejecutar desde la raíz del proyecto)

Notas metodológicas:
  - Se filtra por código ISO3 y no por nombre: la grafía del nombre cambia
    entre fuentes ("Panamá" con o sin tilde); el código es estable.
  - El script verifica que el indicador del archivo sea NY.GDP.MKTP.KD y
    se detiene si trae otra serie (evita procesar la equivocada).
  - Recorte a la ventana de análisis 2020-2024; valores en USD absolutos
    como número entero.
  - Validación estricta: nulos, PIB no positivo o de magnitud implausible
    y años fuera de rango abortan sin escribir el CSV.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
import sys
from pathlib import Path

import pandas as pd

from config_siepac import ANIOS_ANALISIS, CODIGOS_ISO3, DIR_RAW, DIR_PROCESSED
from etl_comun import encontrar_archivo_entrada

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)


# ======================================================================
# CONFIGURACIÓN
# Todo lo que podría cambiar está aquí arriba, en un solo lugar.
# ======================================================================

# Indicador que ESPERAMOS encontrar. Si el archivo trae otro, el script
# se detiene en vez de procesar una serie equivocada por accidente.
INDICADOR_ESPERADO = "NY.GDP.MKTP.KD"

# Los 6 países del SIEPAC, identificados por su código ISO3.
# Filtramos por CÓDIGO y no por nombre a propósito: el nombre cambia de
# grafía entre fuentes (el Banco Mundial en español escribe "Panamá" CON
# tilde; otras fuentes escriben "Panama" sin tilde). El código ISO3 es
# estable y no sufre ese problema. El valor de este diccionario es el que
# queda en la columna 'pais' del CSV de salida (grafía canónica del
# proyecto, definida en config_siepac).
CODIGOS_SIEPAC = CODIGOS_ISO3

# Ventana de análisis de la tesis (definida una sola vez en config_siepac).
ANIO_INICIO = ANIOS_ANALISIS[0]
ANIO_FIN = ANIOS_ANALISIS[-1]

# Los export del Banco Mundial traen 4 filas de metadatos ("Data Source",
# "Last Updated Date", etc.) ANTES de la tabla real. Hay que saltarlas.
FILAS_METADATOS = 4

# Etiqueta de fuente para trazabilidad (la "Ficha de Registro Documental"
# del protocolo: de dónde salió el dato y en qué unidad original).
FUENTE = ("Banco Mundial - Indicadores del Desarrollo Mundial - "
          "NY.GDP.MKTP.KD (PIB US$ constantes 2015)")


# ======================================================================
# 1. EXTRAER
# ======================================================================

def extraer_datos(ruta_csv: Path) -> pd.DataFrame:
    """Lee el CSV crudo del Banco Mundial y devuelve el DataFrame completo.

    Dos detalles del formato del Banco Mundial que hay que respetar:
      1) skiprows=FILAS_METADATOS  -> las 4 primeras líneas son metadatos.
      2) encoding='utf-8-sig'      -> el archivo trae un BOM invisible al
         inicio; sin 'utf-8-sig' la primera columna se llamaría
         '\\ufeffCountry Name' y rompería los filtros por nombre de columna.
    """
    df = pd.read_csv(ruta_csv, skiprows=FILAS_METADATOS, encoding="utf-8-sig")
    log.info("Archivo leído: %d filas, %d columnas (%s)",
             df.shape[0], df.shape[1], ruta_csv.name)
    return df


# ======================================================================
# 2. TRANSFORMAR
# ======================================================================

def transformar(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra, valida el indicador, pasa a formato tidy y aplica moneda."""

    # --- 2.1 Verificar que el indicador es el correcto -----------------
    # Si el archivo tuviera otra serie (PIB nominal, per cápita, etc.),
    # nos detenemos aquí en vez de procesar la serie equivocada.
    codigos_indicador = list(df["Indicator Code"].dropna().unique())
    if codigos_indicador != [INDICADOR_ESPERADO]:
        raise ValueError(
            f"Indicador inesperado. Esperaba SOLO '{INDICADOR_ESPERADO}' "
            f"pero el archivo contiene: {codigos_indicador}. "
            f"DETENIDO para no procesar la serie equivocada."
        )
    log.info("Indicador verificado: %s", INDICADOR_ESPERADO)

    # --- 2.2 Filtrar a los 6 países SIEPAC por código ISO3 -------------
    df_siepac = df[df["Country Code"].isin(CODIGOS_SIEPAC.keys())].copy()

    # Avisar si falta algún país (nunca inventamos filas).
    faltantes = set(CODIGOS_SIEPAC.keys()) - set(df_siepac["Country Code"])
    if faltantes:
        log.warning("Faltan países SIEPAC en el archivo: %s", faltantes)
    else:
        log.info("Los 6 países SIEPAC están presentes")

    # --- 2.3 Seleccionar solo las columnas de año 2020-2024 ------------
    anios = [str(a) for a in range(ANIO_INICIO, ANIO_FIN + 1)]
    anios_presentes = [a for a in anios if a in df_siepac.columns]
    anios_ausentes = [a for a in anios if a not in df_siepac.columns]
    if anios_ausentes:
        log.warning("Estos años no existen como columna: %s", anios_ausentes)

    df_recorte = df_siepac[["Country Code"] + anios_presentes]

    # --- 2.4 Ancho -> tidy (una fila por país-año) ----------------------
    tidy = df_recorte.melt(
        id_vars="Country Code",
        var_name="anio",
        value_name="valor_bruto",
    )

    # --- 2.5 Limpieza y validación de cada valor ------------------------
    tidy["anio"] = tidy["anio"].astype(int)
    # Forzar a numérico: lo que no sea número (celda vacía, "..") se vuelve
    # NaN. NO se inventa ni se rellena con cero.
    tidy["valor_bruto"] = pd.to_numeric(tidy["valor_bruto"], errors="coerce")

    # Reportar y descartar filas sin dato.
    nulos = tidy["valor_bruto"].isna().sum()
    if nulos > 0:
        detalle = tidy.loc[tidy["valor_bruto"].isna(), ["Country Code", "anio"]]
        log.warning("%d celda(s) sin dato, se descartan:\n%s",
                    nulos, detalle.to_string(index=False))
    tidy = tidy.dropna(subset=["valor_bruto"])

    # --- 2.6 REGLA DE MONEDA del proyecto -------------------------------
    # El PIB es variable macroeconómica: USD constantes 2015, VALOR ENTERO.
    # La regla dice "si el dato viene en millones de USD, multiplicar por
    # 1,000,000". EN LA INSPECCIÓN SE VERIFICÓ que el Banco Mundial ya
    # entrega USD ABSOLUTOS (ej. Costa Rica 2024 ~ 7.6e10 = ~76 mil
    # millones USD = su PIB real). Por lo tanto NO se multiplica por
    # 1,000,000. Solo se redondea a entero.
    tidy["valor_usd"] = tidy["valor_bruto"].round(0).astype("int64")

    # --- 2.7 Formato final tidy del proyecto ----------------------------
    tidy["pais"] = tidy["Country Code"].map(CODIGOS_SIEPAC)
    tidy["fuente"] = FUENTE

    resultado = (
        tidy[["pais", "anio", "valor_usd", "fuente"]]
        .sort_values(["pais", "anio"])
        .reset_index(drop=True)
    )
    log.info("Resultado tidy: %d filas", resultado.shape[0])
    return resultado


# ======================================================================
# 3. VALIDAR
# ======================================================================

def validar(df: pd.DataFrame) -> None:
    """Chequeos de calidad antes de guardar. Los problemas graves (nulos,
    PIB no positivo o de magnitud implausible, años fuera de rango)
    abortan sin escribir el CSV; el conteo de filas distinto al esperado
    solo avisa."""
    errores_graves = []

    # a) No debe haber nulos en el resultado final.
    if df.isna().any().any():
        errores_graves.append("Hay valores nulos en el resultado final.")

    # b) Conteo esperado: 6 países x 5 años = 30 (si todo está completo).
    #    Puede ser normal si falta algún año en la fuente: solo avisa.
    esperado = len(CODIGOS_SIEPAC) * (ANIO_FIN - ANIO_INICIO + 1)
    if df.shape[0] != esperado:
        log.warning("Se esperaban %d filas (6 países x 5 años) pero hay %d. "
                    "Revisar si falta algún año en la fuente.",
                    esperado, df.shape[0])

    # c) El PIB debe ser positivo y de magnitud plausible.
    #    Umbral de mil millones: si algo cae por debajo, sospechar que la
    #    unidad quedó mal (p. ej. millones sin convertir).
    if (df["valor_usd"] <= 0).any():
        errores_graves.append("Hay valores de PIB <= 0, lo cual es imposible.")
    if (df["valor_usd"] < 1_000_000_000).any():
        errores_graves.append(
            "Hay PIB < mil millones USD: sospechoso, revisar la unidad "
            "(posibles millones sin convertir o serie equivocada)."
        )

    # d) Los años deben estar dentro del rango pedido.
    if not df["anio"].between(ANIO_INICIO, ANIO_FIN).all():
        errores_graves.append(
            f"Hay años fuera del rango {ANIO_INICIO}-{ANIO_FIN}.")

    if errores_graves:
        for e in errores_graves:
            log.error(e)
        sys.exit("VALIDACIÓN FALLIDA — el CSV no fue escrito.")

    log.info("Todas las validaciones pasaron correctamente")


# ======================================================================
# 4. MAIN
# ======================================================================

def main():
    carpeta_entrada = DIR_RAW / "pib"
    ruta_salida = DIR_PROCESSED / "pib.csv"

    log.info("=== ETL PIB (NY.GDP.MKTP.KD) — SIEPAC ===")

    # El ZIP del Banco Mundial trae 3 CSVs (datos + 2 de metadatos); el de
    # datos siempre empieza con "API_", por eso se busca por ese patrón.
    ruta_csv = encontrar_archivo_entrada(carpeta_entrada, patron="API_*.csv")
    df_crudo = extraer_datos(ruta_csv)
    df_limpio = transformar(df_crudo)
    validar(df_limpio)

    # Crear carpeta de salida si no existe y escribir el CSV.
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df_limpio.to_csv(ruta_salida, index=False, encoding="utf-8-sig")
    log.info("CSV guardado en: %s", ruta_salida)
    log.info("Vista previa del resultado:\n%s",
             df_limpio.to_string(index=False))


if __name__ == "__main__":
    main()
