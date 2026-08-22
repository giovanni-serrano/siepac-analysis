"""
etl_soc2.py — Asequibilidad eléctrica regional (SOC2)
====================================================
Etapa del pipeline : ETL de indicador social
Entradas           : data/raw_equipo/soc2_agregacion_regional/
                     base_integrada.csv
Salidas            : data/processed/soc2_pais_anio.csv,
                     data/processed/soc2_regional.csv,
                     data/processed/soc2_auditoria.csv y
                     data/processed/soc2_sensibilidad.csv
Alimenta           : procesar_dimensiones.py, tablas, visualizadores y
                     figuras de la tesis
Fuente de datos    : base única SOC2 elaborada por el equipo de tesis

Uso:  python src/etl_soc2.py   (ejecutar desde la raíz del proyecto)

El archivo recibido se trata como fuente inmutable. Este ETL no confía en
sus columnas derivadas: reconstruye desde cargo, ingresos, clientes y
proporción vulnerable todas las magnitudes nacionales y regionales.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from config_siepac import (ANIOS_ANALISIS as ANIOS, DIR_PROCESSED,
                           DIR_RAW_EQUIPO, PAISES_SIEPAC as PAISES)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

RUTA_ENTRADA = (DIR_RAW_EQUIPO / "soc2_agregacion_regional" /
                "base_integrada.csv")

COLUMNAS_ENTRADA = [
    "pais", "anio", "clientes_residenciales", "cargo_anual_usd",
    "ingreso_prom_usd", "ingreso_vulnerable_usd",
    "proporcion_vulnerable", "fuente_hoja", "nota_metodologica",
    "observacion_clientes",
]


def _fallar(mensaje: str) -> None:
    sys.exit(f"VALIDACIÓN FALLIDA — SOC2: {mensaje}")


def _casi_iguales(a, b, tolerancia: float = 1e-9) -> bool:
    return bool(np.allclose(a, b, rtol=tolerancia, atol=tolerancia,
                            equal_nan=True))


def cargar_y_validar(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    """Lee la fuente, valida el contrato y recalcula las 30 observaciones."""
    if not ruta.exists():
        _fallar(f"no se encontró {ruta}")

    fuente = pd.read_csv(ruta)
    faltantes = [c for c in COLUMNAS_ENTRADA if c not in fuente.columns]
    if faltantes:
        _fallar(f"faltan columnas requeridas: {', '.join(faltantes)}")

    if len(fuente) != len(PAISES) * len(ANIOS):
        _fallar(f"se esperaban 30 filas país-año; hay {len(fuente)}")
    if fuente.duplicated(["pais", "anio"]).any():
        _fallar("hay claves país-año duplicadas")
    if set(fuente["pais"]) != set(PAISES):
        _fallar("la lista de países no coincide con el SIEPAC")
    if set(fuente["anio"]) != set(ANIOS):
        _fallar("la ventana temporal no coincide con 2020–2024")

    numericas = [
        "clientes_residenciales", "cargo_anual_usd", "ingreso_prom_usd",
        "ingreso_vulnerable_usd", "proporcion_vulnerable",
    ]
    if fuente[numericas].isna().any().any():
        _fallar("hay faltantes en clientes, cargo, ingresos o proporción")
    if not np.isfinite(fuente[numericas].to_numpy(dtype=float)).all():
        _fallar("hay valores no finitos en los insumos")
    if (fuente[numericas] <= 0).any().any():
        _fallar("clientes, cargos, ingresos y proporciones deben ser positivos")

    proporcion_esperada = fuente["pais"].map(
        lambda p: 0.296 if p == "Nicaragua" else 0.20)
    if not _casi_iguales(fuente["proporcion_vulnerable"],
                         proporcion_esperada):
        _fallar("la proporción vulnerable no respeta 20 % / Nicaragua 29.6 %")

    df = fuente[COLUMNAS_ENTRADA].copy()
    df["clientes_vulnerables_proxy"] = (
        df["clientes_residenciales"] * df["proporcion_vulnerable"])
    df["SOC2_PROM"] = (
        df["cargo_anual_usd"] / df["ingreso_prom_usd"] * 100)
    df["SOC2_VULNERABLE"] = (
        df["cargo_anual_usd"] / df["ingreso_vulnerable_usd"] * 100)
    df["gasto_prom_proxy_usd"] = (
        df["cargo_anual_usd"] * df["clientes_residenciales"])
    df["ingreso_prom_proxy_usd"] = (
        df["ingreso_prom_usd"] * df["clientes_residenciales"])
    df["gasto_vulnerable_proxy_usd"] = (
        df["cargo_anual_usd"] * df["clientes_vulnerables_proxy"])
    df["ingreso_vulnerable_proxy_usd"] = (
        df["ingreso_vulnerable_usd"] * df["clientes_vulnerables_proxy"])
    df["fuente_dato"] = "equipo_SOC2_base_unica"

    contrastes = {
        "soc2_prom_nacional": "SOC2_PROM",
        "soc2_vulnerable_nacional": "SOC2_VULNERABLE",
        "clientes_vulnerables_proxy": "clientes_vulnerables_proxy",
        "gasto_prom_proxy": "gasto_prom_proxy_usd",
        "ingreso_prom_proxy": "ingreso_prom_proxy_usd",
        "gasto_vulnerable_proxy": "gasto_vulnerable_proxy_usd",
        "ingreso_vulnerable_proxy": "ingreso_vulnerable_proxy_usd",
    }
    for original, calculada in contrastes.items():
        if original in fuente and not _casi_iguales(fuente[original],
                                                     df[calculada]):
            diferencia = (fuente[original] - df[calculada]).abs().max()
            _fallar(f"{original} no reconcilia; diferencia máxima {diferencia}")

    return df.sort_values(["pais", "anio"]).reset_index(drop=True)


def calcular_regional(df: pd.DataFrame) -> pd.DataFrame:
    """Razón de sumas del bloque, con componentes auditables por año."""
    g = df.groupby("anio", sort=True).agg(
        clientes_residenciales=("clientes_residenciales", "sum"),
        gasto_prom_proxy_usd=("gasto_prom_proxy_usd", "sum"),
        ingreso_prom_proxy_usd=("ingreso_prom_proxy_usd", "sum"),
        clientes_vulnerables_proxy=("clientes_vulnerables_proxy", "sum"),
        gasto_vulnerable_proxy_usd=("gasto_vulnerable_proxy_usd", "sum"),
        ingreso_vulnerable_proxy_usd=("ingreso_vulnerable_proxy_usd", "sum"),
    ).reindex(ANIOS)
    g["SOC2_PROM"] = (
        g["gasto_prom_proxy_usd"] / g["ingreso_prom_proxy_usd"] * 100)
    g["SOC2_VULNERABLE"] = (
        g["gasto_vulnerable_proxy_usd"] /
        g["ingreso_vulnerable_proxy_usd"] * 100)
    g["brecha_vulnerable_prom_pp"] = (
        g["SOC2_VULNERABLE"] - g["SOC2_PROM"])
    return g.reset_index()


def calcular_sensibilidad(df: pd.DataFrame,
                          regional: pd.DataFrame) -> pd.DataFrame:
    """Contrastes metodológicos usados para documentar robustez."""
    filas = []
    for anio in ANIOS:
        sub = df[df["anio"] == anio].copy()
        reg = regional[regional["anio"] == anio].iloc[0]
        prom_pond = np.average(sub["SOC2_PROM"],
                               weights=sub["clientes_residenciales"])
        vul_pond = np.average(sub["SOC2_VULNERABLE"],
                              weights=sub["clientes_residenciales"])

        p20 = sub["proporcion_vulnerable"].where(
            sub["pais"] != "Nicaragua", 0.20)
        clientes20 = sub["clientes_residenciales"] * p20
        vul20 = ((sub["cargo_anual_usd"] * clientes20).sum() /
                 (sub["ingreso_vulnerable_usd"] * clientes20).sum() * 100)

        sin_hn = sub[sub["pais"] != "Honduras"]
        vul_sin_hn = (
            sin_hn["gasto_vulnerable_proxy_usd"].sum() /
            sin_hn["ingreso_vulnerable_proxy_usd"].sum() * 100)
        filas.append({
            "anio": anio,
            "prom_ponderado_clientes": prom_pond,
            "prom_razon_sumas": reg["SOC2_PROM"],
            "vulnerable_ponderado_clientes": vul_pond,
            "vulnerable_razon_sumas": reg["SOC2_VULNERABLE"],
            "vulnerable_nicaragua_20": vul20,
            "vulnerable_sin_honduras": vul_sin_hn,
        })
    return pd.DataFrame(filas)


def construir_auditoria(df: pd.DataFrame,
                        regional: pd.DataFrame) -> pd.DataFrame:
    """Controles compactos para inspección humana y CI."""
    pesos = []
    for _, sub in df.groupby("anio"):
        componentes = [
            "clientes_residenciales", "gasto_prom_proxy_usd",
            "ingreso_prom_proxy_usd", "clientes_vulnerables_proxy",
            "gasto_vulnerable_proxy_usd", "ingreso_vulnerable_proxy_usd",
        ]
        for col in componentes:
            pesos.append(float((sub[col] / sub[col].sum()).max() * 100))
    controles = [
        ("observaciones_pais_anio", len(df), 30),
        ("duplicados_pais_anio", int(df.duplicated(["pais", "anio"]).sum()), 0),
        ("faltantes_criticos", int(df[["clientes_residenciales",
          "cargo_anual_usd", "ingreso_prom_usd", "ingreso_vulnerable_usd"]]
          .isna().sum().sum()), 0),
        ("maximo_peso_componente_pct", max(pesos), "< 50"),
        ("soc2_prom_2024", float(regional.iloc[-1]["SOC2_PROM"]),
         2.112803729840648),
        ("soc2_vulnerable_2024",
         float(regional.iloc[-1]["SOC2_VULNERABLE"]),
         12.949303219454952),
    ]
    return pd.DataFrame(controles, columns=["control", "resultado", "esperado"])


def main() -> None:
    log.info("Leyendo y validando %s", RUTA_ENTRADA)
    df = cargar_y_validar()
    regional = calcular_regional(df)
    sensibilidad = calcular_sensibilidad(df, regional)
    auditoria = construir_auditoria(df, regional)

    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    salidas = {
        "soc2_pais_anio.csv": df,
        "soc2_regional.csv": regional,
        "soc2_sensibilidad.csv": sensibilidad,
        "soc2_auditoria.csv": auditoria,
    }
    for nombre, tabla in salidas.items():
        ruta = DIR_PROCESSED / nombre
        tabla.to_csv(ruta, index=False, encoding="utf-8")
        log.info("Guardado: %s (%d filas)", ruta, len(tabla))
    log.info("SOC2 validado: 30 país-año y 5 agregados regionales.")


if __name__ == "__main__":
    main()
