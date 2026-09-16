"""
etl_comun.py — Utilidades compartidas de los ETL
====================================================
Etapa del pipeline : soporte (módulo común, no se ejecuta directo)
Entradas           : —
Salidas            : — (lo importan los ETL de src/)

Localización de entradas y validación defensiva compartida de paneles.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from config_siepac import ANIOS_ANALISIS, PAISES_SIEPAC

log = logging.getLogger(Path(__file__).stem)


def fallar_validacion(contexto: str, detalle: str) -> None:
    """Interrumpe el pipeline antes de escribir una salida inválida."""
    mensaje = f"VALIDACIÓN FALLIDA — {contexto}: {detalle}"
    log.error(mensaje)
    sys.exit(mensaje)


def validar_columnas(df: pd.DataFrame, columnas, contexto: str) -> None:
    faltantes = sorted(set(columnas) - set(df.columns))
    if faltantes:
        fallar_validacion(contexto, f"columnas faltantes: {faltantes}")


def validar_panel(df: pd.DataFrame, contexto: str,
                  anios=ANIOS_ANALISIS) -> None:
    """Exige claves únicas y cobertura explícita, sin alterar los datos.

    anios=None permite historia irregular previa a una imputación autorizada;
    mantiene unicidad, años enteros y la cobertura de los seis países.
    """
    validar_columnas(df, ["pais", "anio"], contexto)
    nulas = df[["pais", "anio"]].isna().any(axis=1)
    if nulas.any():
        fallar_validacion(contexto, "claves nulas: " +
                          str(df.loc[nulas, ["pais", "anio"]].to_dict("records")))
    anos_numericos = pd.to_numeric(df["anio"], errors="coerce")
    validos = (anos_numericos.notna() & np.isfinite(anos_numericos)
               & (anos_numericos % 1 == 0))
    if not validos.all():
        fallar_validacion(contexto, "años inválidos: " +
                          str(df.loc[~validos, ["pais", "anio"]].to_dict("records")))
    # ENV3 guarda años como texto. Comparar sus claves numéricas sin cambiar
    # las celdas de origen; también detecta 2020 y "2020" como duplicados.
    claves = df[["pais", "anio"]].assign(anio=anos_numericos)
    duplicadas = claves.duplicated(["pais", "anio"], keep=False)
    if duplicadas.any():
        repetidas = claves.loc[duplicadas].drop_duplicates()
        fallar_validacion(contexto, f"claves país-año duplicadas: {repetidas.to_dict('records')}")
    paises = set(df["pais"])
    faltan = set(PAISES_SIEPAC) - paises
    sobran = paises - set(PAISES_SIEPAC)
    if faltan or sobran:
        fallar_validacion(contexto, f"países faltantes: {sorted(faltan)}; "
                          f"países inesperados: {sorted(sobran, key=str)}")
    if anios is not None:
        faltan_anios = set(anios) - set(anos_numericos)
        sobran_anios = set(anos_numericos) - set(anios)
        if faltan_anios or sobran_anios:
            fallar_validacion(contexto, f"años faltantes: {sorted(faltan_anios)}; "
                              f"años inesperados: {sorted(sobran_anios)}")
        esperado = {(p, a) for p in PAISES_SIEPAC for a in anios}
        presentes = set(claves.itertuples(index=False, name=None))
        if esperado - presentes:
            fallar_validacion(contexto, f"claves país-año faltantes: {sorted(esperado - presentes)}")


def validar_numericos(df: pd.DataFrame, columnas, contexto: str,
                      positivos: bool = False) -> None:
    """Rechaza nulos/no finitos; exige positividad solo para denominadores."""
    validar_columnas(df, columnas, contexto)
    for columna in columnas:
        valores = pd.to_numeric(df[columna], errors="coerce")
        invalidos = ~np.isfinite(valores.to_numpy(dtype=float, na_value=np.nan))
        if positivos:
            invalidos |= (valores <= 0).fillna(True).to_numpy(dtype=bool)
        if invalidos.any():
            claves = [c for c in ("pais", "anio") if c in df]
            detalle = df.loc[invalidos, claves + [columna]].to_dict("records")
            regla = "denominador no positivo o no finito" if positivos else "valor nulo, no numérico o no finito"
            fallar_validacion(contexto, f"{columna}: {regla}; {detalle}")


def encontrar_archivo_entrada(raw_dir: Path, patron: str = "*.xlsx") -> Path:
    """Busca el primer archivo que cumpla el patrón dentro de raw_dir
    (ignora archivos temporales de Excel tipo ~$).

    Falla con mensaje claro si la carpeta no existe o no hay candidatos;
    si hay más de uno, avisa y usa el primero en orden alfabético.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"La carpeta no existe:\n{raw_dir}")

    candidatos = [f for f in sorted(raw_dir.glob(patron))
                  if not f.name.startswith("~$")]

    if not candidatos:
        contenido = list(raw_dir.iterdir())
        raise FileNotFoundError(
            f"No se encontró ningún '{patron}' en:\n{raw_dir}\n"
            f"Contenido actual de la carpeta: "
            f"{contenido if contenido else '(vacía)'}"
        )

    if len(candidatos) > 1:
        log.warning("Hay %d archivos '%s', se usará: %s",
                    len(candidatos), patron, candidatos[0].name)

    return candidatos[0]
