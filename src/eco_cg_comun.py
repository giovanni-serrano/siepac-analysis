"""
eco_cg_comun.py — Serie complementaria de costos de generación
====================================================
Etapa del pipeline : validación y preparación de un insumo del equipo
Entradas           : data/raw_equipo/eco_cg_siepac.csv
Salidas            : — (funciones compartidas por tablas y figuras)
Alimenta           : generar_tablas_apa.py y generar_figuras_tesis.py
Fuente de datos    : archivo incorporado por el equipo de investigación

La serie ECO_CG no es un indicador IEDS adicional. Es un complemento de la
dimensión económica expresado en USD corrientes/MWh. Los instrumentos
nacionales pertenecen a distintos niveles metodológicos, por lo que no se
construye un costo agregado del SIEPAC. La mediana, la media simple y las
medidas de dispersión se usan únicamente para describir los seis proxies.

Uso:  importar desde los generadores que consumen la serie.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

from pathlib import Path

import pandas as pd

from config_siepac import ANIOS_ANALISIS, DIR_RAW_EQUIPO, PAISES_SIEPAC


CODIGO_ECO_CG = "ECO_CG"
ETIQUETA_ECO_CG = "ECO-CG"
COLUMNA_ECO_CG = "eco_cg_usd_mwh"
RUTA_ECO_CG = DIR_RAW_EQUIPO / "eco_cg_siepac.csv"

ORDEN_ECO_CG_DOCUMENTO = [
    "Guatemala", "Honduras", "El Salvador", "Nicaragua", "Costa Rica",
    "Panamá",
]

NIVEL_ECO_CG = {
    "Guatemala": 2,
    "Honduras": 3,
    "El Salvador": 4,
    "Nicaragua": 2,
    "Costa Rica": 3,
    "Panamá": 3,
}

BANDERAS_ECO_CG = {
    ("Honduras", 2020): "*",
    ("Costa Rica", 2024): "†",
    ("El Salvador", 2024): "‡",
}

FUENTES_ECO_CG = (
    "CNEE/AMM, CREE, SIGET/UT, CNDC/INE, DOCSE/ICE y ASEP"
)

NOTA_CALIDAD_ECO_CG = (
    "* Honduras 2020 incorpora reconstrucción retrospectiva del primer "
    "semestre. † Costa Rica 2024 es un proxy parcial de seis meses (junio "
    "y agosto–diciembre). ‡ El Salvador 2024 emplea desde el 15 de abril "
    "el PETT del bloque no protegido. Los niveles expresan proximidad "
    "metodológica al costo de generación y no equivalencia económica "
    "entre instrumentos."
)

FICHA_ECO_CG = dict(
    nombre="Costo de generación eléctrica",
    unidad="USD corrientes/MWh",
    formato=".2f",
    sufijo=" USD/MWh",
    delta="pct",
    dim="eco",
    formula=("Mejor proxy oficial nacional disponible de costo medio "
             "unitario de generación, operación o abastecimiento; la "
             "mediana describe el centro de los seis proxies sin formar "
             "un agregado regional"),
    descripcion=("Aproximación al costo medio unitario mediante el mejor "
                 "proxy oficial disponible para cada país y año; serie "
                 "económica complementaria al marco IEDS."),
    nota=("Serie económica complementaria; no constituye un noveno indicador "
          "IEDS. Los proxies nacionales no son conceptualmente homólogos: "
          "la mediana, la media y la dispersión son descriptivas y no "
          "constituyen un costo agregado del SIEPAC."),
)


def cargar_eco_cg(ruta: Path = RUTA_ECO_CG) -> pd.DataFrame:
    """Carga y valida la cobertura país-año completa de ECO_CG.

    Devuelve ``pais``, ``anio``, ``ECO_CG``, ``nivel`` y ``bandera``. Los
    dos últimos campos proceden de la trazabilidad metodológica documentada,
    no del CSV de valores. Una falla detiene el pipeline antes de que se
    publiquen tablas o figuras parciales.
    """
    if not ruta.exists():
        raise FileNotFoundError(
            f"VALIDACIÓN FALLIDA: no se encontró {ruta}. "
            "La serie complementaria ECO_CG es necesaria para generar sus "
            "tablas APA 7 y su figura del bloque.")

    datos = pd.read_csv(ruta)
    requeridas = {"pais", "anio", COLUMNA_ECO_CG}
    faltantes = requeridas - set(datos.columns)
    if faltantes:
        raise ValueError(
            "VALIDACIÓN FALLIDA en eco_cg_siepac.csv: faltan columnas "
            f"{sorted(faltantes)}.")

    datos = datos[["pais", "anio", COLUMNA_ECO_CG]].copy()
    datos["anio"] = pd.to_numeric(datos["anio"], errors="coerce")
    datos[COLUMNA_ECO_CG] = pd.to_numeric(
        datos[COLUMNA_ECO_CG], errors="coerce")

    errores = []
    if datos[["pais", "anio", COLUMNA_ECO_CG]].isna().any().any():
        errores.append("contiene valores nulos o no numéricos")
    if datos["anio"].notna().any() and not (
            datos.loc[datos["anio"].notna(), "anio"] % 1 == 0).all():
        errores.append("contiene años no enteros")

    if datos["anio"].notna().all():
        datos["anio"] = datos["anio"].astype(int)
        paises_extra = sorted(set(datos["pais"]) - set(PAISES_SIEPAC))
        anios_extra = sorted(set(datos["anio"]) - set(ANIOS_ANALISIS))
        if paises_extra:
            errores.append(f"países inesperados: {paises_extra}")
        if anios_extra:
            errores.append(f"años fuera de la ventana: {anios_extra}")

        duplicados = datos.duplicated(["pais", "anio"], keep=False)
        if duplicados.any():
            pares = datos.loc[duplicados, ["pais", "anio"]].values.tolist()
            errores.append(f"claves país-año duplicadas: {pares}")

        esperado = {(p, a) for p in PAISES_SIEPAC for a in ANIOS_ANALISIS}
        observado = set(map(tuple, datos[["pais", "anio"]].values.tolist()))
        ausentes = sorted(esperado - observado)
        if ausentes:
            errores.append(f"faltan combinaciones país-año: {ausentes}")

    if (datos[COLUMNA_ECO_CG].dropna() <= 0).any():
        errores.append("los costos deben ser mayores que cero")

    if errores:
        raise ValueError(
            "VALIDACIÓN FALLIDA en eco_cg_siepac.csv: " + "; ".join(errores))

    orden_pais = {pais: i for i, pais in enumerate(PAISES_SIEPAC)}
    datos["_orden_pais"] = datos["pais"].map(orden_pais)
    datos = datos.sort_values(["_orden_pais", "anio"]).drop(
        columns="_orden_pais")
    datos["nivel"] = datos["pais"].map(NIVEL_ECO_CG)
    datos["bandera"] = [
        BANDERAS_ECO_CG.get((pais, anio), "")
        for pais, anio in zip(datos["pais"], datos["anio"])
    ]
    return datos.rename(columns={COLUMNA_ECO_CG: CODIGO_ECO_CG}).reset_index(
        drop=True)


def serie_mediana_eco_cg(eco_cg: pd.DataFrame) -> list[float]:
    """Mediana descriptiva de los seis proxies, en orden cronológico.

    No se denomina agregado regional: cada país aporta un instrumento de
    distinto nivel metodológico y no existe un ponderador conceptualmente
    compatible entre los seis casos.
    """
    mediana = eco_cg.groupby("anio")[CODIGO_ECO_CG].median()
    return [float(mediana.loc[anio]) for anio in ANIOS_ANALISIS]
