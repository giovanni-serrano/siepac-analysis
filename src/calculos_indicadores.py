"""
calculos_indicadores.py — Cálculos científicos comunes del SIEPAC
====================================================
Etapa del pipeline : cálculos y agregación (módulo importable)
Entradas           : tablas y series normalizadas en memoria
Salidas            : valores nacionales, agregados y estadísticos
Alimenta           : libros, resumen, tablas, figuras y visualizador
Fuente de datos    : ETL y matrices del equipo, suministrados por el llamador
Uso                : importar las funciones; no realiza E/S
Notas metodológicas: conserva el orden de operaciones y redondeos existentes.
                     Promedio de países y agregado regional son distintos.
Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""
import math
import pandas as pd
from config_siepac import PAISES_SIEPAC as PAISES, ANIOS_ANALISIS as ANIOS
from etl_comun import (fallar_validacion, validar_columnas, validar_panel,
                       validar_numericos)

CALCULOS_ECO = {
    'ECO1': lambda d: d["consumo_final_total_kwh"] / d["poblacion_habitantes"],
    'ECO2': lambda d: d["consumo_final_total_kwh"] / d["pib_usd_const2015"],
    'ECO3': lambda d: d["consumo_final_total_kwh"]
                          / d["produccion_bruta_kwh"] * 100,
    'ECO6': lambda d: d["consumo_industrial_kwh"] / d["vai_usd_const2015"],
    'ECO11': lambda d: d["gen_fosil_kwh"] / d["gen_total_kwh"] * 100,
    'ECO13': lambda d: (d["gen_hidro_kwh"] + d["gen_geotermia_kwh"]
                           + d["gen_eolica_kwh"] + d["gen_solar_kwh"]
                           + d["gen_biomasa_kwh"]) / d["gen_total_kwh"] * 100,
    'ECO14': lambda d: d["tarifa_usd_mwh"],
    'ECO15': lambda d: (d["importaciones_kwh"] - d["exportaciones_kwh"])
                          / (d["produccion_bruta_kwh"]
                             + d["importaciones_kwh"]
                             - d["exportaciones_kwh"]) * 100,
}

def calcular_valores(wide: pd.DataFrame) -> pd.DataFrame:
    """Evalúa en pandas el `calculo` de cada indicador sobre la matriz wide.

    Devuelve un DataFrame pais | anio | ECO1..ECO15 | tarifa_fuente_dato,
    con los mismos valores que producirían las fórmulas del Excel. Es la
    salida legible por máquina que consumen los visualizadores.
    """
    validar_panel(wide, "indicadores ECO")
    validar_columnas(wide, ["tarifa_fuente_dato"], "ECO14")
    banderas_invalidas = ~wide["tarifa_fuente_dato"].isin(["real", "imputado_CAGR"])
    if banderas_invalidas.any():
        fallar_validacion("ECO14", "tarifa_fuente_dato inválida: " +
                          str(wide.loc[banderas_invalidas, ["pais", "anio", "tarifa_fuente_dato"]].to_dict("records")))
    denominadores = {
        "poblacion_habitantes": "ECO1", "pib_usd_const2015": "ECO2",
        "produccion_bruta_kwh": "ECO3", "vai_usd_const2015": "ECO6",
        "gen_total_kwh": "ECO11/ECO13",
    }
    columnas = [*denominadores, "consumo_final_total_kwh", "consumo_industrial_kwh",
                "gen_fosil_kwh", "gen_hidro_kwh", "gen_geotermia_kwh",
                "gen_eolica_kwh", "gen_solar_kwh", "gen_biomasa_kwh",
                "importaciones_kwh", "exportaciones_kwh", "tarifa_usd_mwh"]
    validar_numericos(wide, columnas, "insumos ECO")
    for columna, codigo in denominadores.items():
        validar_numericos(wide, [columna], codigo, positivos=True)
    # El saldo puede ser negativo; el denominador de energía disponible
    # debe ser positivo. No se altera el signo del numerador de ECO15.
    disponibilidad = wide[["pais", "anio"]].assign(
        disponibilidad_kwh=wide["produccion_bruta_kwh"]
        + wide["importaciones_kwh"] - wide["exportaciones_kwh"])
    validar_numericos(disponibilidad, ["disponibilidad_kwh"], "ECO15", positivos=True)
    valores = wide[["pais", "anio"]].copy()
    for codigo, calculo in CALCULOS_ECO.items():
        valores[codigo] = calculo(wide)
    # Identificador del método aplicado a la tarifa.
    valores["tarifa_fuente_dato"] = wide["tarifa_fuente_dato"]
    validar_numericos(valores, list(CALCULOS_ECO), "resultados ECO")
    return valores


def media_ponderada(valores: dict, pesos: dict) -> list:
    """Σ v·w / Σ w por año sobre {pais: [v_2020..v_2024]}; omite los
    países sin dato ese año. Con el denominador del indicador como peso
    es matemáticamente idéntica a la razón de sumas Σ N_i / Σ D_i."""
    salida = []
    for i in range(len(ANIOS)):
        num = den = 0.0
        for p in PAISES:
            v, w = valores[p][i], pesos[p][i]
            if v is None or w is None:
                continue
            num += v * w
            den += w
        salida.append(round(num / den, 6) if den else None)
    return salida


def agregados_eco(base: pd.DataFrame) -> dict:
    """Agregado regional (razón de sumas) de los indicadores ECO, desde
    la hoja Datos_Base: misma N/D que generar_matriz_indicadores (las
    filas 'Agregado regional' del Excel llevan estas fórmulas en
    paridad; si cambia una, cambia la otra). ECO14 devuelve None porque
    su resumen regional se define mediante la mediana de países."""
    g = (base[base["pais"].isin(PAISES)]
         .groupby("anio").sum(numeric_only=True).sort_index())
    renovables = (g["gen_hidro_kwh"] + g["gen_geotermia_kwh"]
                  + g["gen_eolica_kwh"] + g["gen_solar_kwh"]
                  + g["gen_biomasa_kwh"])
    neto = g["importaciones_kwh"] - g["exportaciones_kwh"]
    series = {
        "ECO1": g["consumo_final_total_kwh"] / g["poblacion_habitantes"],
        "ECO2": g["consumo_final_total_kwh"] / g["pib_usd_const2015"],
        "ECO3": g["consumo_final_total_kwh"] / g["produccion_bruta_kwh"] * 100,
        "ECO6": g["consumo_industrial_kwh"] / g["vai_usd_const2015"],
        "ECO11": g["gen_fosil_kwh"] / g["gen_total_kwh"] * 100,
        "ECO13": renovables / g["gen_total_kwh"] * 100,
        "ECO14": None,
        "ECO15": neto / (g["produccion_bruta_kwh"] + neto) * 100,
    }
    return {cod: (None if s is None
                  else [round(float(s.loc[a]), 6) for a in ANIOS])
            for cod, s in series.items()}


def _mediana(v: list[float]) -> float:
    s = sorted(v)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def _de_poblacional(v: list[float]) -> float:
    """Desviación estándar poblacional (denominador N): los seis países
    son el universo del SIEPAC, no una muestra. Mismo criterio que
    analisis-eco/analisis_descriptivo_eco.py."""
    media = sum(v) / len(v)
    return math.sqrt(sum((x - media) ** 2 for x in v) / len(v))


def _cv_pct(v: list[float]) -> float:
    return _de_poblacional(v) / abs(sum(v) / len(v)) * 100


def _estadisticos_paises(valores: list[float]) -> dict[str, float]:
    """Estadísticos poblacionales del conjunto completo de países."""
    return {
        "n": len(valores),
        "media": sum(valores) / len(valores),
        "mediana": _mediana(valores),
        "de": _de_poblacional(valores),
        "minimo": min(valores),
        "maximo": max(valores),
        "rango": max(valores) - min(valores),
    }

