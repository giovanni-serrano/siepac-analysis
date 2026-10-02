"""
procesar_dimensiones.py — Indicadores de las dimensiones ambiental y social
====================================================
Etapa del pipeline : indicadores
Entradas           : data/raw_equipo/ENVs.xlsx, data/raw_equipo/SOCs.xlsx,
                     data/processed/soc2_pais_anio.csv,
                     data/processed/soc2_regional.csv y
                     data/processed/poblacion_rural_urbana.csv
Salidas            : data/processed/indicadores_ENV_SIEPAC.xlsx y
                     data/processed/indicadores_SOC_SIEPAC.xlsx
Alimenta           : ENV1, ENV2, ENV3, ENV6, SOC1, SOC2, SOC3
Fuente de datos    : matrices ENVs.xlsx y SOCs.xlsx del estudio; Banco
                     Mundial WDI para población rural y urbana

Uso:  python src/procesar_dimensiones.py   (ejecutar desde la raíz)

Convierte las matrices de entrada en dos libros estandarizados con la misma
estructura del libro de la dimensión económica:
  - Hoja Metodologia (indicador, serie, unidad, fórmula, notas)
  - Una hoja por serie: fila 1 título, fila 2 fórmula, fila 3 encabezado
    (País + 2020..2024), filas 4-9 países, fila 10 Promedio regional
  - ENV6 conserva su formato especial de dos series por país

Reglas de transformación:
  - SOC1 viene con años descendentes y países en columnas -> se
    transpone; la columna TOTAL (suma entre países) se descarta.
  - SOC2 usa la base única en USD y calcula el agregado regional mediante
    razón de sumas de gasto e ingreso aproximados.
  - SOC3 combina electrificación y participación renovable. El agregado
    rural se pondera por población rural y el urbano por población urbana.
  - ENV1 intensidad: se lee el valor almacenado (o caché de fórmula).
    Si falta, se divide GEI en miles de t entre PIB en millones de USD.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
import sys
from pathlib import Path

import openpyxl
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from config_siepac import (PAISES_SIEPAC as PAISES, ANIOS_ANALISIS as ANIOS,
                            RAIZ_PROYECTO, DIR_PROCESSED)
from viz_comun import media_ponderada
from etl_comun import fallar_validacion, validar_panel

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

RUTA_ENV_RAW = RAIZ_PROYECTO / "data" / "raw_equipo" / "ENVs.xlsx"
RUTA_SOC_RAW = RAIZ_PROYECTO / "data" / "raw_equipo" / "SOCs.xlsx"
RUTA_POB_ZONA = DIR_PROCESSED / "poblacion_rural_urbana.csv"
RUTA_SOC2 = DIR_PROCESSED / "soc2_pais_anio.csv"
RUTA_SOC2_REGIONAL = DIR_PROCESSED / "soc2_regional.csv"
DIR_OUT = DIR_PROCESSED

# ------------------------------ estilos -----------------------------------
GRIS = "44546A"
F_TIT = Font(name="Arial", size=12, bold=True, color="1F3864")
F_SUB = Font(name="Arial", size=9, italic=True, color="595959")
F_HDR = Font(name="Arial", size=10, bold=True, color="FFFFFF")
F_TXT = Font(name="Arial", size=10)
F_NEG = Font(name="Arial", size=10, bold=True)
FILL_H = PatternFill("solid", start_color=GRIS)
FILL_P = PatternFill("solid", start_color="EDEDED")
BORDE = Border(*[Side(style="thin", color="BFBFBF")] * 4)


# ---------------------------------------------------------------------------
# LECTURA DIMENSION AMBIENTAL
# ---------------------------------------------------------------------------

def leer_env(ruta: Path) -> dict[str, pd.DataFrame]:
    """Devuelve {clave_serie: DataFrame pais x anio} + ENV6 especial."""
    wb = openpyxl.load_workbook(ruta, data_only=True)   # valores, no formulas
    # Revisar las claves originales antes de int(), pivot o diccionarios:
    # ninguna fila repetida puede sustituir a otra ni ocultar un hueco.
    try:
        for nombre in ("ENV1", "ENV2", "ENV3"):
            if nombre not in wb.sheetnames:
                fallar_validacion(f"ENV / {ruta.name}", f"hoja faltante: {nombre}")
            claves = pd.DataFrame(
                [(f[0], f[1]) for f in wb[nombre].iter_rows(min_row=2, values_only=True)],
                columns=["pais", "anio"])
            validar_panel(claves, f"{ruta.name} / {nombre}")
    except BaseException:
        wb.close()
        raise
    series = {}

    def tabla(hoja, col_valor, recalcular=None):
        ws = wb[hoja]
        filas = list(ws.iter_rows(min_row=2, values_only=True))
        reg = {}
        for f in filas:
            pais, anio = f[0], int(f[1])
            v = f[col_valor]
            if v is None and recalcular:
                v = recalcular(f)
            reg[(pais, anio)] = float(v)
        df = pd.DataFrame(
            [[reg[(p, a)] for a in ANIOS] for p in PAISES],
            index=PAISES, columns=ANIOS)
        return df

    # ENV1: col F (idx 5) per cápita; col G (idx 6) intensidad almacenada.
    series["ENV1_PC"] = tabla("ENV1", 5)
    # Miles de t -> kg y millones de USD -> USD aportan ambos 10⁶:
    # (f[2] × 10⁶) / (f[4] × 10⁶) = f[2] / f[4], en kg CO2eq/USD.
    series["ENV1_PIB"] = tabla("ENV1", 6,
        recalcular=lambda f: f[2] / f[4])
    # ENV2: 4 salidas (cols G..J -> idx 6..9)
    series["ENV2_SO2_PC"] = tabla("ENV2", 6)
    series["ENV2_PAR_PC"] = tabla("ENV2", 7)
    series["ENV2_SO2_PIB"] = tabla("ENV2", 8)
    series["ENV2_PAR_PIB"] = tabla("ENV2", 9)
    # ENV3: escala electrica g/kWh (ultima col, idx 10)
    series["ENV3"] = tabla("ENV3", 10)

    # ENV6: pares de filas (Inyeccion Biomasa / Saldo MER) por pais
    ws = wb["ENV6"]
    filas = list(ws.iter_rows(min_row=2, values_only=True))
    env6 = []
    pais_actual = None
    for f in filas:
        if f[0]:
            pais_actual = str(f[0]).strip()
        serie = str(f[1]).strip()
        env6.append([pais_actual, serie] + [float(v) for v in f[2:7]])
    series["ENV6"] = pd.DataFrame(
        env6, columns=["pais", "serie"] + ANIOS)

    # Datos base de la dimension: variables de entrada de ENV1/ENV2/ENV3.
    reg = {}
    for f in wb["ENV1"].iter_rows(min_row=2, values_only=True):
        reg[(f[0], int(f[1]))] = {
            "emisiones_gei_10e3t": float(f[2]),
            "poblacion_miles": float(f[3]),
            "pib_usd_const2015": float(f[4])}
    for f in wb["ENV2"].iter_rows(min_row=2, values_only=True):
        reg[(f[0], int(f[1]))].update({
            "so2_10e3t": float(f[2]), "particulas_10e3t": float(f[3])})
    for f in wb["ENV3"].iter_rows(min_row=2, values_only=True):
        reg[(f[0], int(f[1]))].update({
            "produccion_bruta_gwh": float(f[2]),
            "nox_10e3t": float(f[4]), "co_10e3t": float(f[5])})
    base = pd.DataFrame(
        [{"pais": p, "anio": a, **reg[(p, a)]}
         for p in PAISES for a in ANIOS])
    series["BASE"] = base
    wb.close()
    return series


# ---------------------------------------------------------------------------
# LECTURA DIMENSION SOCIAL
# ---------------------------------------------------------------------------

def leer_soc(ruta: Path) -> dict[str, pd.DataFrame]:
    wb = openpyxl.load_workbook(ruta, data_only=True)
    series = {}

    # --- SOC1: anios en filas (descendentes), paises en columnas C..H ---
    ws = wb["SOC 1"]
    orden_cols = ["Costa Rica", "El Salvador", "Guatemala",
                  "Honduras", "Nicaragua", "Panamá"]  # fila 2, cols C..H
    reg = {}
    for f in ws.iter_rows(min_row=3, max_row=7, values_only=True):
        anio = int(f[0])
        for j, pais in enumerate(orden_cols):
            reg[(pais, anio)] = float(f[2 + j])
    series["SOC1"] = pd.DataFrame(
        [[reg[(p, a)] for a in ANIOS] for p in PAISES],
        index=PAISES, columns=ANIOS)

    # --- SOC2: salida normalizada del ETL específico ------------------
    if not RUTA_SOC2.exists():
        sys.exit("VALIDACIÓN FALLIDA — falta soc2_pais_anio.csv; ejecutar "
                 "antes etl_soc2.py.")
    soc2 = pd.read_csv(RUTA_SOC2)
    esperadas = set(PAISES) | {""}
    if len(soc2) != 30 or soc2.duplicated(["pais", "anio"]).any():
        sys.exit("VALIDACIÓN FALLIDA — SOC2 procesado no contiene 30 "
                 "claves país-año únicas.")
    if set(soc2["pais"]) != esperadas - {""}:
        sys.exit("VALIDACIÓN FALLIDA — países inesperados en SOC2.")
    for clave in ("SOC2_PROM", "SOC2_VULNERABLE"):
        series[clave] = (soc2.pivot(index="pais", columns="anio",
                                    values=clave)
                         .reindex(index=PAISES, columns=ANIOS))

    # --- SOC3: tabla tidy oculta en columnas K..Y ---
    # Se filtra por contenido (col K = pais valido, col L = anio) porque
    # la hoja mezcla bloques auxiliares y el encabezado cambia de fila.
    ws = wb["SOC 3"]
    reg_r, reg_u = {}, {}
    n_filas = 0
    for f in ws.iter_rows(values_only=True):
        if f[10] in PAISES and f[11] is not None:
            try:
                anio = int(f[11])
            except (TypeError, ValueError):
                continue
            if anio not in ANIOS:
                continue
            pais = f[10]
            reg_r[(pais, anio)] = float(f[23])  # col X: acceso renov. rural
            reg_u[(pais, anio)] = float(f[24])  # col Y: acceso renov. urbano
            n_filas += 1
    assert n_filas == 30, f"SOC3: se esperaban 30 filas pais-anio, hay {n_filas}"

    # Datos base de la dimensión: tasas de electrificación y % renovable
    # (SOC1/SOC3), más los insumos unitarios en USD y ponderadores de SOC2.
    reg_b = {}
    for f in wb["SOC 3"].iter_rows(values_only=True):
        if f[10] in PAISES and f[11] is not None:
            try:
                anio = int(f[11])
            except (TypeError, ValueError):
                continue
            if anio not in ANIOS:
                continue
            reg_b[(f[10], anio)] = {
                "pct_renovable_generacion": float(f[20]),
                "tasa_electrificacion_rural": float(f[21]),
                "tasa_electrificacion_urbana": float(f[22])}
    for clave, reg in [("SOC3_RURAL", reg_r), ("SOC3_URB", reg_u)]:
        series[clave] = pd.DataFrame(
            [[reg[(p, a)] for a in ANIOS] for p in PAISES],
            index=PAISES, columns=ANIOS)

    series["BASE"] = pd.DataFrame(
        [{"pais": p, "anio": a,
          "pct_sin_electricidad": float(series["SOC1"].loc[p, a]),
          **reg_b[(p, a)]}
         for p in PAISES for a in ANIOS])
    columnas_soc2 = [
        "pais", "anio", "clientes_residenciales", "cargo_anual_usd",
        "ingreso_prom_usd", "ingreso_vulnerable_usd",
        "proporcion_vulnerable", "clientes_vulnerables_proxy",
        "gasto_prom_proxy_usd", "ingreso_prom_proxy_usd",
        "gasto_vulnerable_proxy_usd", "ingreso_vulnerable_proxy_usd",
        "fuente_dato",
    ]
    series["BASE_SOC2"] = soc2[columnas_soc2].copy()
    return series


# ---------------------------------------------------------------------------
# ESCRITURA EN FORMATO ESTANDAR (identico al libro ECO)
# ---------------------------------------------------------------------------

def hoja_serie(wb, nombre, df, titulo, formula, num_fmt, agregado=None):
    """Hoja estandar de una serie. `agregado` (lista por anio o None) es
    la razon de sumas Σnum/Σden — pondera cada pais por su denominador —
    calculada en main() con el denominador propio de cada serie."""
    ws = wb.create_sheet(nombre)
    ws["A1"] = titulo
    ws["A1"].font = F_TIT
    ws["A2"] = f"Fórmula: {formula}"
    ws["A2"].font = F_SUB
    ws.cell(row=3, column=1, value="País")
    for j, a in enumerate(ANIOS):
        ws.cell(row=3, column=2 + j, value=a)
    for c in range(1, 7):
        cel = ws.cell(row=3, column=c)
        cel.font, cel.fill, cel.border = F_HDR, FILL_H, BORDE
        cel.alignment = Alignment(horizontal="center")
    for i, pais in enumerate(PAISES):
        ws.cell(row=4 + i, column=1, value=pais).font = F_TXT
        ws.cell(row=4 + i, column=1).border = BORDE
        for j, a in enumerate(ANIOS):
            v = df.loc[pais, a]
            cel = ws.cell(row=4 + i, column=2 + j,
                          value=None if pd.isna(v) else float(v))
            cel.font, cel.border, cel.number_format = F_TXT, BORDE, num_fmt
    fila_p = 4 + len(PAISES)
    ws.cell(row=fila_p, column=1,
            value="Promedio de países (media simple)").font = F_NEG
    ws.cell(row=fila_p, column=1).fill = FILL_P
    ws.cell(row=fila_p, column=1).border = BORDE
    for j, a in enumerate(ANIOS):
        cel = ws.cell(row=fila_p, column=2 + j, value=float(df[a].mean()))
        cel.font, cel.fill, cel.border = F_NEG, FILL_P, BORDE
        cel.number_format = num_fmt
    if agregado is not None:
        fila_a = fila_p + 1
        ws.cell(row=fila_a, column=1,
                value="Agregado regional (razón de sumas)").font = F_NEG
        ws.cell(row=fila_a, column=1).fill = FILL_P
        ws.cell(row=fila_a, column=1).border = BORDE
        for j, v in enumerate(agregado):
            cel = ws.cell(row=fila_a, column=2 + j,
                          value=None if v is None else float(v))
            cel.font, cel.fill, cel.border = F_NEG, FILL_P, BORDE
            cel.number_format = num_fmt
    ws.column_dimensions["A"].width = 30
    for c in "BCDEF":
        ws.column_dimensions[c].width = 13
    ws.freeze_panes = "B4"


def hoja_env6(wb, df):
    ws = wb.create_sheet("ENV6")
    ws["A1"] = "ENV6 — Comparativo de inyección de Biomasa vs Saldo MER (GWh)"
    ws["A1"].font = F_TIT
    ws["A2"] = ("Indicador ilustrativo: contrasta la generación con biomasa "
                "de cada país con su saldo neto en el Mercado Eléctrico "
                "Regional. Saldo negativo = importador neto en el MER.")
    ws["A2"].font = F_SUB
    enc = ["País", "Serie"] + ANIOS
    for c, v in enumerate(enc, start=1):
        cel = ws.cell(row=3, column=c, value=v)
        cel.font, cel.fill, cel.border = F_HDR, FILL_H, BORDE
        cel.alignment = Alignment(horizontal="center")
    for i, fila in df.iterrows():
        for c, v in enumerate(fila, start=1):
            cel = ws.cell(row=4 + i, column=c, value=v)
            cel.font, cel.border = F_TXT, BORDE
            if c > 2:
                cel.number_format = "#,##0.0"
    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 20
    for c in "CDEFG":
        ws.column_dimensions[c].width = 12
    ws.freeze_panes = "C4"


def hoja_metodologia(wb, filas, titulo):
    ws = wb.create_sheet("Metodologia", 0)
    ws["A1"] = titulo
    ws["A1"].font = F_TIT
    enc = ["Hoja", "Indicador / Serie", "Unidad", "Fórmula", "Notas"]
    for c, v in enumerate(enc, start=1):
        cel = ws.cell(row=3, column=c, value=v)
        cel.font, cel.fill, cel.border = F_HDR, FILL_H, BORDE
    for r, fila in enumerate(filas, start=4):
        for c, v in enumerate(fila, start=1):
            cel = ws.cell(row=r, column=c, value=v)
            cel.font, cel.border = F_TXT, BORDE
            cel.alignment = Alignment(vertical="top", wrap_text=True)
    for letra, w in {"A": 14, "B": 38, "C": 18, "D": 44, "E": 46}.items():
        ws.column_dimensions[letra].width = w
    ws.freeze_panes = "A4"


# Peso del agregado regional (razon de sumas) por serie: el DENOMINADOR
# del indicador, tomado de la tabla BASE de la dimension. Con ese peso,
# la media ponderada de los valores nacionales equivale a Σnum/Σden del
# bloque. SOC1 pondera por poblacion total (poblacion_total.csv del ETL);
# SOC2 se agrega directamente desde sus magnitudes proxy en USD; no entra en
# este catálogo de ponderadores porque etl_soc2.py ya produce la razón de sumas.
PESOS_AGREGADO = {
    "ENV1_PC": "poblacion_miles",
    "ENV1_PIB": "pib_usd_const2015",
    "ENV2_SO2_PC": "poblacion_miles",
    "ENV2_PAR_PC": "poblacion_miles",
    "ENV2_SO2_PIB": "pib_usd_const2015",
    "ENV2_PAR_PIB": "pib_usd_const2015",
    "ENV3": "produccion_bruta_gwh",
}

PESOS_SOC3 = {
    "SOC3_RURAL": "poblacion_rural_hab",
    "SOC3_URB": "poblacion_urbana_hab",
}


def _valores_de(df: pd.DataFrame) -> dict:
    """DataFrame pais x anio -> {pais: [v_2020..v_2024]} con None en NaN."""
    return {p: [None if pd.isna(df.loc[p, a]) else float(df.loc[p, a])
                for a in ANIOS] for p in PAISES}


def _pesos_de(base: pd.DataFrame, col: str) -> dict:
    """Columna de la tabla BASE (tidy pais-anio) -> {pais: [w_2020..]}."""
    return {p: [float(base.loc[(base["pais"] == p) & (base["anio"] == a),
                               col].iloc[0]) for a in ANIOS]
            for p in PAISES}


# Catalogo: (clave, titulo, unidad, formula, formato excel, nota)
CAT_ENV = [
    ("ENV1_PC", "ENV1 — Emisiones GEI per cápita",
     "t CO2eq/habitante",
     "Emisiones GEI de centrales eléctricas (10³ t) ÷ Población", "0.0000",
     "Solo emisiones del sector de generación eléctrica."),
    ("ENV1_PIB", "ENV1 — Emisiones GEI por unidad de PIB",
     "kg CO2eq/USD const. 2015",
     "Emisiones GEI (kg) ÷ PIB real (USD constantes 2015)", "0.0000",
     "Valor recuperado de la fórmula original =(A×10⁶)/PIB."),
    ("ENV2_SO2_PC", "ENV2 — SO₂ per cápita", "kg/habitante",
     "Emisiones SO₂ de centrales eléctricas ÷ Población", "0.000", ""),
    ("ENV2_PAR_PC", "ENV2 — Partículas per cápita", "kg/habitante",
     "Emisiones de partículas ÷ Población", "0.0000", ""),
    ("ENV2_SO2_PIB", "ENV2 — SO₂ por unidad de PIB", "g/USD const. 2015",
     "Emisiones SO₂ (g) ÷ PIB real", "0.0000", ""),
    ("ENV2_PAR_PIB", "ENV2 — Partículas por unidad de PIB",
     "g/USD const. 2015", "Emisiones de partículas (g) ÷ PIB real",
     "0.00000", ""),
    ("ENV3", "ENV3 — Emisiones atmosféricas de los sistemas energéticos",
     "g/kWh", "(SO₂ + NOx + CO + PAR) ÷ Producción bruta", "0.000",
     "Escala eléctrica (g/kWh)."),
]
CAT_SOC = [
    ("SOC1", "SOC1 — Población sin acceso a electricidad", "%",
     "100 − Tasa de electrificación total", "0.00",
     "La columna TOTAL de la fuente (suma entre países) se descartó. "
     "La hoja cierra con dos resúmenes: Promedio de países (media "
     "simple) y Agregado regional (razón de sumas, ponderado por "
     "población: personas sin electricidad del bloque ÷ población "
     "del bloque)."),
    ("SOC2_PROM", "SOC2 — Ingreso destinado a electricidad (hogar promedio)",
     "%", "Cargo anual medio residencial ÷ ingreso anual de referencia "
     "del hogar × 100", "0.00",
     "El agregado regional es la razón entre el gasto residencial proxy y "
     "el ingreso PROM proxy, ambos expandidos por clientes residenciales."),
    ("SOC2_VULNERABLE", "SOC2 — Ingreso destinado a electricidad (estrato "
     "vulnerable)", "%",
     "Cargo anual medio residencial ÷ ingreso anual del estrato vulnerable "
     "× 100", "0.00",
     "El agregado regional usa clientes vulnerables proxy: 20 % en cinco "
     "países y 29.6 % en Nicaragua."),
    ("SOC3_RURAL", "SOC3 — Hogares rurales con acceso a energía renovable",
     "%", "Tasa de electrificación rural × % renovable de la generación",
     "0.00", "Combina la tasa de electrificación rural con la participación "
     "renovable nacional. El agregado pondera por población rural."),
    ("SOC3_URB", "SOC3 — Hogares urbanos con acceso a energía renovable",
     "%", "Tasa de electrificación urbana × % renovable de la generación",
     "0.00", "Combina la tasa de electrificación urbana con la participación "
     "renovable nacional. El agregado pondera por población urbana."),
]


def hoja_base(wb, base_df, titulo, nota):
    """Hoja Datos_Base: variables de entrada de la dimension, en tidy
    (una fila por pais-anio), mismo patron de estilo que el libro ECO."""
    ws = wb.create_sheet("Datos_Base")
    ws["A1"] = titulo
    ws["A1"].font = F_TIT
    ws["A2"] = nota
    ws["A2"].font = F_SUB
    for c, col in enumerate(base_df.columns, start=1):
        cel = ws.cell(row=3, column=c, value=col)
        cel.font, cel.fill, cel.border = F_HDR, FILL_H, BORDE
        cel.alignment = Alignment(horizontal="center")
    for r, fila in enumerate(base_df.itertuples(index=False), start=4):
        for c, v in enumerate(fila, start=1):
            cel = ws.cell(row=r, column=c, value=v)
            cel.font, cel.border = F_TXT, BORDE
            if c > 2:
                columna = str(base_df.columns[c - 1])
                cel.number_format = ("#,##0" if columna in {
                    "poblacion_rural_hab", "poblacion_urbana_hab",
                    "poblacion_total_hab"} else "#,##0.00")
            if c == 2:
                cel.number_format = "0"
    ws.column_dimensions["A"].width = 14
    for c in range(2, len(base_df.columns) + 1):
        letra = ws.cell(row=3, column=c).column_letter
        ws.column_dimensions[letra].width = 22
    ws.freeze_panes = "C4"


def main():
    log.info("Leyendo ENVs.xlsx y SOCs.xlsx ...")
    env = leer_env(RUTA_ENV_RAW)
    soc = leer_soc(RUTA_SOC_RAW)
    DIR_OUT.mkdir(parents=True, exist_ok=True)

    # Poblacion total (peso del agregado de SOC1), producida por el ETL.
    ruta_pob = DIR_PROCESSED / "poblacion_total.csv"
    pesos_pob = None
    if ruta_pob.exists():
        pob = pd.read_csv(ruta_pob)
        pesos_pob = _pesos_de(pob.rename(
            columns={"valor_habitantes": "poblacion"}), "poblacion")
    else:
        log.warning("Sin %s: SOC1 quedará sin fila de agregado regional.",
                    ruta_pob.name)

    if not RUTA_POB_ZONA.exists():
        sys.exit("VALIDACIÓN FALLIDA — falta poblacion_rural_urbana.csv; "
                 "ejecutar antes etl_poblacion_rural_urbana.py.")
    pob_zona = pd.read_csv(RUTA_POB_ZONA)
    pesos_soc3 = {
        clave: _pesos_de(pob_zona, columna)
        for clave, columna in PESOS_SOC3.items()
    }
    columnas_zona = ["pais", "anio", "poblacion_rural_hab",
                     "poblacion_urbana_hab", "poblacion_total_hab"]
    soc["BASE"] = soc["BASE"].merge(
        pob_zona[columnas_zona], on=["pais", "anio"], how="left",
        validate="one_to_one")
    if soc["BASE"][columnas_zona[2:]].isna().any().any():
        sys.exit("VALIDACIÓN FALLIDA — faltan ponderadores SOC3 tras "
                 "cruzar población rural/urbana.")
    soc["BASE"] = soc["BASE"].merge(
        soc["BASE_SOC2"], on=["pais", "anio"], how="left",
        validate="one_to_one")

    if not RUTA_SOC2_REGIONAL.exists():
        sys.exit("VALIDACIÓN FALLIDA — falta soc2_regional.csv; ejecutar "
                 "antes etl_soc2.py.")
    soc2_regional = pd.read_csv(RUTA_SOC2_REGIONAL).set_index("anio")
    agregados_soc2 = {
        clave: [float(soc2_regional.loc[a, clave]) for a in ANIOS]
        for clave in ("SOC2_PROM", "SOC2_VULNERABLE")
    }

    # ------- libro ambiental -------
    wb = Workbook(); wb.remove(wb.active)
    for clave, titulo, unidad, formula, fmt, nota in CAT_ENV:
        agregado = media_ponderada(_valores_de(env[clave]),
                                   _pesos_de(env["BASE"],
                                             PESOS_AGREGADO[clave]))
        hoja_serie(wb, clave, env[clave], f"{titulo} ({unidad})",
                   formula, fmt, agregado=agregado)
    hoja_env6(wb, env["ENV6"])
    hoja_base(wb, env["BASE"],
        "Datos base — dimensión ambiental (variables de entrada)",
        "Emisiones en 10³ t; población en miles; PIB en USD constantes "
        "2015; producción bruta en GWh. Fuente: matriz ENVs.xlsx.")
    hoja_metodologia(
        wb,
        [[c, t, u, f, n] for c, t, u, f, _, n in CAT_ENV] +
        [["ENV6", "ENV6 — Inyección de biomasa vs saldo MER", "GWh",
          "Series observadas (sin fórmula)",
          "Indicador ilustrativo; el saldo MER negativo indica importador "
          "neto en el mercado regional."]],
        "Indicadores de la dimensión ambiental — SIEPAC 2020–2024")
    ruta_env = DIR_OUT / "indicadores_ENV_SIEPAC.xlsx"
    wb.save(ruta_env)
    log.info("Guardado: %s", ruta_env)

    # ------- libro social -------
    wb = Workbook(); wb.remove(wb.active)
    for clave, titulo, unidad, formula, fmt, nota in CAT_SOC:
        if clave == "SOC1" and pesos_pob:
            agregado = media_ponderada(_valores_de(soc[clave]), pesos_pob)
        elif clave in pesos_soc3:
            agregado = media_ponderada(_valores_de(soc[clave]),
                                       pesos_soc3[clave])
        elif clave in agregados_soc2:
            agregado = agregados_soc2[clave]
        else:
            agregado = None
        hoja_serie(wb, clave, soc[clave], f"{titulo} ({unidad})",
                   formula, fmt, agregado=agregado)
    hoja_base(wb, soc["BASE"],
        "Datos base — dimensión social (variables de entrada)",
        "Tasas y participaciones en %; población rural, urbana y total "
        "en habitantes. SOC2 conserva cargo e ingresos anuales en USD, "
        "clientes residenciales y clientes vulnerables proxy. Fuentes: "
        "SOCs.xlsx, base única SOC2 del equipo y Banco Mundial WDI "
        "(SP.RUR.TOTL y SP.URB.TOTL).")
    hoja_metodologia(
        wb, [[c, t, u, f, n] for c, t, u, f, _, n in CAT_SOC],
        "Indicadores de la dimensión social — SIEPAC 2020–2024")
    ruta_soc = DIR_OUT / "indicadores_SOC_SIEPAC.xlsx"
    wb.save(ruta_soc)
    log.info("Guardado: %s", ruta_soc)


if __name__ == "__main__":
    main()
