"""
etl_tarifa_electrica_media.py — Tarifa eléctrica media regulada
====================================================
Etapa del pipeline : ETL
Entradas           : data/raw/tarifa_electrica_media/*.xlsx (hoja "datos")
Salidas            : data/processed/tarifa_electrica_media.csv (tidy)
Alimenta           : ECO14
Fuente de datos    : CEPAL / SIECA-CRIE

Uso:  python src/etl_tarifa_electrica_media.py   (ejecutar desde la raíz)

Notas metodológicas:
  - La serie histórica completa se utiliza para calcular el CAGR; la salida
    se restringe a la ventana de análisis 2020-2024.
  - Los valores proyectados se identifican con
    fuente_dato=imputado_CAGR.
  - ECO14 se mantiene en USD corrientes/MWh (no constantes), según la
    definición metodológica del proyecto (ver README, Notas metodológicas).

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
import sys
from pathlib import Path

import pandas as pd

from config_siepac import PAISES_SIEPAC, ANIOS_ANALISIS, DIR_RAW, DIR_PROCESSED
from etl_comun import encontrar_archivo_entrada

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

# --- 1. Rutas (relativas a la raiz del proyecto) ---
RAW_DIR = DIR_RAW / "tarifa_electrica_media"
PROCESSED_DIR = DIR_PROCESSED
ARCHIVO_SALIDA = PROCESSED_DIR / "tarifa_electrica_media.csv"

HOJA = "datos"

PAISES_VALIDOS = set(PAISES_SIEPAC)

# --- 2. Ventanas temporales ---

# Ventana de analisis = lo que se exporta (contexto de la monografia);
# viene de config_siepac.ANIOS_ANALISIS (2020-2024).

# El CAGR utiliza todo el intervalo histórico disponible para cada país.


def extraer_datos(path_excel: Path, hoja: str) -> pd.DataFrame:
    """Lee la hoja 'datos' (formato tabular CEPAL) y devuelve un DataFrame tidy.

    La extracción conserva la serie histórica completa para calcular el
    CAGR antes de aplicar la ventana de análisis.
    Se filtra por 'Tipo regulación' == 'Regulado' y 'Sector' == 'Total',
    y se descartan filas sin valor.
    """
    df_raw = pd.read_excel(path_excel, sheet_name=hoja)

    df_filtrado = df_raw[
        (df_raw["País__ESTANDAR"].isin(PAISES_VALIDOS))
        & (df_raw["Tipo regulación"] == "Regulado")
        & (df_raw["Sector"] == "Total")
    ].copy()

    df_tidy = df_filtrado.rename(columns={
        "País__ESTANDAR": "pais",
        "Años__ESTANDAR": "anio",
        "value": "valor_usd_mwh",
    })[["pais", "anio", "valor_usd_mwh"]]

    # Excluir celdas vacías antes del cálculo temporal.
    df_tidy = df_tidy.dropna(subset=["valor_usd_mwh"]).copy()
    df_tidy["anio"] = df_tidy["anio"].astype(int)

    return df_tidy.sort_values(["pais", "anio"]).reset_index(drop=True)


def calcular_cagr(valor_inicial: float, valor_final: float, n_periodos: int) -> float:
    """CAGR = (valor_final / valor_inicial) ** (1 / n_periodos) - 1

    n_periodos = número de años entre los extremos de la serie histórica.
    """
    return (valor_final / valor_inicial) ** (1 / n_periodos) - 1


def proyectar_faltantes(df_tidy: pd.DataFrame) -> pd.DataFrame:
    """Completa la ventana de análisis mediante proyección CAGR.

    Logica por pais:
    1. Se toma la serie histórica disponible.
    2. Se calcula el CAGR entre el primer y el último año.
    3. Se identifican los años por completar en ANIOS_ANALISIS.
    4. Cada año se proyecta desde el último valor histórico:
       valor = valor_ultimo * (1 + CAGR) ** (anio - anio_ultimo)
    5. Cada fila proyectada se marca con fuente_dato = "imputado_CAGR".
    """
    filas_finales = []

    for pais, grupo in df_tidy.groupby("pais"):
        serie = grupo.set_index("anio")["valor_usd_mwh"].sort_index()
        anios_reales = serie.index.tolist()
        primer_anio, ultimo_anio = anios_reales[0], anios_reales[-1]

        faltantes = [a for a in ANIOS_ANALISIS if a not in anios_reales]

        if faltantes:
            n_periodos = ultimo_anio - primer_anio
            if n_periodos == 0:
                log.warning("%s: solo hay 1 anio real, no se puede calcular "
                            "CAGR. Anios faltantes sin proyectar: %s",
                            pais, faltantes)
                cagr = None
            else:
                v_inicial, v_final = serie.loc[primer_anio], serie.loc[ultimo_anio]
                cagr = calcular_cagr(v_inicial, v_final, n_periodos)
                log.info("%s: CAGR = %.4f%% (serie historica %d-%d, %d periodos)",
                         pais, cagr * 100, primer_anio, ultimo_anio, n_periodos)

            v_ultimo = serie.loc[ultimo_anio]
            for anio in faltantes:
                if cagr is None:
                    continue
                delta = anio - ultimo_anio
                valor_proyectado = v_ultimo * (1 + cagr) ** delta
                serie.loc[anio] = valor_proyectado
                log.info("  -> %s %d: proyectado = %.4f (base %d = %.4f, +%d anio/s)",
                         pais, anio, valor_proyectado, ultimo_anio, v_ultimo, delta)

        df_pais = serie.sort_index().reset_index()
        df_pais.columns = ["anio", "valor_usd_mwh"]
        df_pais["pais"] = pais
        df_pais["fuente_dato"] = df_pais["anio"].apply(
            lambda a: "real" if a in anios_reales else "imputado_CAGR"
        )
        filas_finales.append(df_pais)

    return pd.concat(filas_finales, ignore_index=True)


def transformar(df_tidy: pd.DataFrame) -> pd.DataFrame:
    """Recorta a la VENTANA DE ANALISIS (2020-2024) y da formato final.

    Los años anteriores a la ventana se utilizan únicamente para calcular
    el CAGR. ECO14 se mantiene en USD corrientes.
    """
    df_tidy = df_tidy.copy()
    df_tidy = df_tidy[df_tidy["anio"].isin(ANIOS_ANALISIS)]
    df_tidy["fuente"] = "CEPAL-SIECA"
    df_tidy = df_tidy[["pais", "anio", "valor_usd_mwh", "fuente_dato", "fuente"]]
    df_tidy = df_tidy.sort_values(["anio", "pais"]).reset_index(drop=True)
    return df_tidy


def validar(df_tidy: pd.DataFrame) -> None:
    """Valida cobertura, valores y países antes de escribir el CSV."""
    errores_graves = []

    n_esperado = len(PAISES_VALIDOS) * len(ANIOS_ANALISIS)
    if len(df_tidy) != n_esperado:
        log.warning("Se esperaban %d filas (%d paises x %d anios), "
                    "se obtuvieron %d.", n_esperado, len(PAISES_VALIDOS),
                    len(ANIOS_ANALISIS), len(df_tidy))

    faltantes = df_tidy["valor_usd_mwh"].isna().sum()
    if faltantes:
        errores_graves.append(f"Hay {faltantes} valores nulos en "
                              "valor_usd_mwh (no se pudieron proyectar).")

    paises_encontrados = set(df_tidy["pais"].unique())
    if paises_encontrados != PAISES_VALIDOS:
        errores_graves.append(
            f"Paises distintos a los esperados: {paises_encontrados}")

    n_imputados = (df_tidy["fuente_dato"] == "imputado_CAGR").sum()
    n_reales = (df_tidy["fuente_dato"] == "real").sum()
    log.info("%d filas reales y %d proyectadas por CAGR de %d totales.",
             n_reales, n_imputados, len(df_tidy))

    if errores_graves:
        for e in errores_graves:
            log.error(e)
        sys.exit("VALIDACIÓN FALLIDA — el CSV no fue escrito.")


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    archivo_entrada = encontrar_archivo_entrada(RAW_DIR)
    log.info("Leyendo: %s", archivo_entrada.name)

    df_tidy = extraer_datos(archivo_entrada, HOJA)
    df_tidy = proyectar_faltantes(df_tidy)
    df_tidy = transformar(df_tidy)
    validar(df_tidy)

    df_tidy.to_csv(ARCHIVO_SALIDA, index=False, encoding="utf-8-sig")

    log.info("OK: %d filas guardadas en: %s", len(df_tidy), ARCHIVO_SALIDA)
    log.info("Resultado completo:\n%s", df_tidy.to_string(index=False))


if __name__ == "__main__":
    main()
