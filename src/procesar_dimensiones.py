"""
procesar_dimensiones.py — Indicadores de las dimensiones ambiental y social
====================================================
Etapa del pipeline : indicadores
Entradas           : data/raw_equipo/ENVs.xlsx, data/raw_equipo/SOCs.xlsx,
                     data/processed/soc2_pais_anio.csv,
                     data/processed/soc2_regional.csv y
                     data/processed/poblacion_rural_urbana.csv
Salidas            : data/processed/indicadores_ENV_SIEPAC.xlsx y
                     data/processed/indicadores_SOC_SIEPAC.xlsx y
                     resultados_ENV/SOC.json para los demás productos
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
from metadatos_indicadores import (PESOS_AGREGADO, PESOS_SOC3,
                                  TEXTOS_EXCEL_DIMENSIONES)
from datos_dimensiones import leer_env, leer_soc as _leer_soc, preparar_dimensiones
from resultados_indicadores import guardar_dimension

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


def leer_soc(ruta: Path):
    """Conserva la entrada histórica y la ruta SOC2 configurable por el llamador."""
    return _leer_soc(ruta, RUTA_SOC2)


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


# Catalogo: (clave, titulo, unidad, formula, formato excel, nota)
CAT_ENV = [
    (c, t["titulo"], t["unidad"], t["formula"], fmt, t["nota"])
    for c, fmt in [('ENV1_PC', '0.0000'), ('ENV1_PIB', '0.0000'), ('ENV2_SO2_PC', '0.000'), ('ENV2_PAR_PC', '0.0000'), ('ENV2_SO2_PIB', '0.0000'), ('ENV2_PAR_PIB', '0.00000'), ('ENV3', '0.000')]
    for t in [TEXTOS_EXCEL_DIMENSIONES[c]]
]
CAT_SOC = [
    (c, t["titulo"], t["unidad"], t["formula"], fmt, t["nota"])
    for c, fmt in [('SOC1', '0.00'), ('SOC2_PROM', '0.00'), ('SOC2_VULNERABLE', '0.00'), ('SOC3_RURAL', '0.00'), ('SOC3_URB', '0.00')]
    for t in [TEXTOS_EXCEL_DIMENSIONES[c]]
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

    agregados_env, agregados_soc = preparar_dimensiones(
        env, soc, DIR_PROCESSED, RUTA_POB_ZONA, RUTA_SOC2_REGIONAL)

    guardar_dimension(DIR_OUT / "resultados_ENV.json", env, agregados_env)
    guardar_dimension(DIR_OUT / "resultados_SOC.json", soc, agregados_soc)

    # ------- libro ambiental -------
    wb = Workbook(); wb.remove(wb.active)
    for clave, titulo, unidad, formula, fmt, nota in CAT_ENV:
        agregado = agregados_env[clave]
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
        agregado = agregados_soc[clave]
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
