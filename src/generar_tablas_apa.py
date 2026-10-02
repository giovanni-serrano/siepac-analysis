"""
generar_tablas_apa.py — Tablas en formato APA 7.ª edición, listas para Word
====================================================
Etapa del pipeline : presentación de resultados (posterior a
                     generar_resumen_indicadores.py)
Entradas           : data/processed/indicadores_ECO_valores.csv,
                     data/raw_equipo/eco_cg_siepac.csv y
                     resultados_ECO/ENV/SOC.json, vía resultados_indicadores
Salidas            : salidas/tesis/tablas/tablas_apa_SIEPAC.docx (todas las
                     tablas con su nota metodológica),
                     tablas_apa_SIEPAC_sin_notas.docx
                     (las mismas tablas sin nota, para el cuerpo del texto),
                     los dos en .html, indice_tablas.csv y la Tabla 7
                     regional de SOC2
Alimenta           : — (producto final para la redacción del monográfico)
Fuente de datos    : salidas del pipeline

Uso:  python src/generar_tablas_apa.py                 (ejecutar desde la raíz)
      python src/generar_tablas_apa.py --orden indicadores
      python src/generar_tablas_apa.py --sin-docx

Convierte la fase cuantitativa completa —las variables base de las tres
dimensiones y los indicadores calculados a partir de ellas— en tablas con
el formato de la 7.ª edición del Manual APA: número en negrita sobre el
título en cursiva, encabezados centrados, SIN líneas verticales, líneas
horizontales solo arriba y abajo de los encabezados y al cierre de la
tabla, y una nota al pie que declara unidad, fórmula y fuente.

Se producen dos versiones del mismo conjunto de tablas, con numeración y
cifras idénticas: una con la nota metodológica al pie (para el anexo y
para auditar fórmulas y fuentes) y otra sin ella (para intercalar en el
cuerpo del monográfico). En la versión sin notas la unidad de medida se
traslada al título, entre paréntesis, porque de otro modo desaparecería
del documento.

Las tablas se generan en HTML. Cuando Microsoft Word está disponible, la
conversión automatizada produce archivos .docx con tablas nativas. El HTML
permanece como formato de intercambio en las demás plataformas.

Notas metodológicas:
  - Los valores se leen de resultados_indicadores, la misma fuente que alimenta los
    visualizadores y el resumen en Markdown.
  - Cada tabla de indicador cierra con las dos filas de resumen del
    proyecto: promedio de países (media simple) y, cuando la serie tiene
    denominador disponible, agregado regional (razón de sumas).
  - Las tablas de datos base cierran con el total del bloque cuando la
    variable es una magnitud sumable (energía, población, PIB) y con el
    promedio de países cuando es una razón o un porcentaje, que no se
    puede sumar entre países.
  - FUENTES_APA y REFERENCIAS_APA centralizan las citas del documento.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

from calculos_indicadores import (_mediana, _de_poblacional, _cv_pct,
                                  _estadisticos_paises)

from resultados_indicadores import leer_bases, cargar_paquete

import argparse
import csv
import html
import logging
import math
import os
import subprocess
import sys
from collections import namedtuple
from datetime import date
from pathlib import Path

import pandas as pd

from config_siepac import DIR_SALIDAS_TESIS, RAIZ_PROYECTO
from eco_cg_comun import (BANDERAS_ECO_CG, CODIGO_ECO_CG,
                          COLUMNA_ECO_CG, ETIQUETA_ECO_CG, FICHA_ECO_CG,
                          FUENTES_ECO_CG, NIVEL_ECO_CG,
                          NOTA_CALIDAD_ECO_CG, ORDEN_ECO_CG_DOCUMENTO,
                          cargar_eco_cg, serie_mediana_eco_cg)
from presentacion_indicadores import FICHAS, series_de as _series_de
from config_siepac import ANIOS_ANALISIS as ANIOS, PAISES_SIEPAC as PAISES

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

DIR_SALIDA = DIR_SALIDAS_TESIS / "tablas"
RUTA_DOC = DIR_SALIDA / "tablas_apa_SIEPAC.html"
RUTA_DOCX = DIR_SALIDA / "tablas_apa_SIEPAC.docx"
# Segunda version: las mismas tablas sin la nota al pie, para intercalar
# en el cuerpo del monografico. La unidad viaja en el titulo.
RUTA_DOC_SIN_NOTAS = DIR_SALIDA / "tablas_apa_SIEPAC_sin_notas.html"
RUTA_DOCX_SIN_NOTAS = DIR_SALIDA / "tablas_apa_SIEPAC_sin_notas.docx"
RUTA_INDICE = DIR_SALIDA / "indice_tablas.csv"
RUTA_SOC2_TESIS = DIR_SALIDA / "tabla_07_soc2_regional_tesis.html"
RUTA_SOC2_TESIS_CSV = DIR_SALIDA / "tabla_07_soc2_regional_tesis.csv"

NOMBRE_DIM = {"eco": "económica", "env": "ambiental", "soc": "social"}

# ---------------------------------------------------------------------------
# CITAS DE LAS FUENTES (formato APA 7.ª ed.)
# Claves cortas para la nota al pie de cada tabla; el texto completo de la
# referencia se incluye en la sección final del documento.
# ---------------------------------------------------------------------------
FUENTES_APA = {
    "olade": "OLADE (2026)",
    "cepal": "CEPAL (2026)",
    "bm": "Banco Mundial (2026a)",
    "bm_pob": "Banco Mundial (2026b)",
    "ods": "CEPAL (2026) y UNIDO (2026)",
    "env": "la matriz ENVs.xlsx",
    "soc": "SOCs.xlsx y la base única SOC2 elaborada por el equipo",
    "eco_cg": FUENTES_ECO_CG,
}

REFERENCIAS_APA = [
    "Banco Mundial. (2026a). <i>PIB (US$ a precios constantes de 2015)</i> "
    "[Conjunto de datos]. Indicadores del desarrollo mundial. "
    "https://datos.bancomundial.org/indicador/NY.GDP.MKTP.KD",
    "Banco Mundial. (2026b). <i>Población rural y población urbana</i> "
    "[Conjuntos de datos]. Indicadores del desarrollo mundial. "
    "https://datos.bancomundial.org/indicador/SP.RUR.TOTL; "
    "https://datos.bancomundial.org/indicador/SP.URB.TOTL",
    "Comisión Económica para América Latina y el Caribe. (2026). "
    "<i>CEPALSTAT: bases de datos y publicaciones estadísticas</i> "
    "[Conjunto de datos]. https://statistics.cepal.org/portal/cepalstat/",
    "Comisión Económica para América Latina y el Caribe. (2026). "
    "<i>Banco de datos regional de seguimiento de los ODS: valor agregado "
    "de la industria manufacturera (indicador 9.2.1)</i> [Conjunto de "
    "datos]. https://agenda2030lac.org/estadisticas/",
    "Organización Latinoamericana de Energía. (2026). <i>Sistema de "
    "Información Energética de Latinoamérica y el Caribe (SIELAC)</i> "
    "[Conjunto de datos]. https://sielac.olade.org/",
    "Organización Internacional de Energía Atómica, Naciones Unidas, "
    "Agencia Internacional de Energía, Eurostat y Agencia Europea de "
    "Medio Ambiente. (2005). <i>Indicadores energéticos del desarrollo "
    "sostenible: directrices y metodologías</i>. OIEA.",
    "Organización de las Naciones Unidas para el Desarrollo Industrial. "
    "(2026). <i>National accounts database</i> [Conjunto de datos]. "
    "https://stat.unido.org",
]

# Fuente que respalda cada indicador, por dimensión o por código.
FUENTE_INDICADOR = {
    "ECO1": "olade+cepal", "ECO2": "olade+bm", "ECO3": "olade",
    "ECO6": "olade+ods", "ECO11": "olade", "ECO13": "olade",
    "ECO14": "cepal", "ECO15": "olade",
}

# ---------------------------------------------------------------------------
# VARIABLES BASE: cómo se presenta cada columna de las hojas Datos_Base.
#   columna  : nombre de la columna en la hoja Datos_Base
#   etiqueta : título de la tabla (sin el "por país, 2020-2024" final)
#   unidad   : unidad que declara la nota al pie
#   escala   : factor por el que se multiplica el valor crudo
#   formato  : formato de impresión (sintaxis format() de Python)
#   delta    : 'pct' variación relativa | 'pp' puntos porcentuales
#   resumen  : 'suma' fila "Total SIEPAC" | 'media' fila "Promedio de países"
#   fuente   : clave de FUENTES_APA
#   nota     : precisión metodológica para la nota al pie ("" si no hay)
# ---------------------------------------------------------------------------
VarBase = namedtuple("VarBase", "columna etiqueta unidad escala formato "
                                "delta resumen fuente nota")

_GWH = 1 / 1_000_000        # kWh -> GWh
_MUSD = 1 / 1_000_000       # USD -> millones de USD

BASE_ECO = [
    VarBase("consumo_final_total_kwh", "Consumo final total de electricidad",
            "GWh", _GWH, ",.1f", "pct", "suma", "olade", ""),
    VarBase("consumo_industrial_kwh",
            "Consumo final de electricidad de la industria",
            "GWh", _GWH, ",.1f", "pct", "suma", "olade", ""),
    VarBase("produccion_bruta_kwh", "Producción bruta de electricidad",
            "GWh", _GWH, ",.1f", "pct", "suma", "olade", ""),
    VarBase("gen_total_kwh", "Generación eléctrica total",
            "GWh", _GWH, ",.1f", "pct", "suma", "olade", ""),
    VarBase("gen_hidro_kwh", "Generación hidroeléctrica",
            "GWh", _GWH, ",.1f", "pct", "suma", "olade", ""),
    VarBase("gen_geotermia_kwh", "Generación geotérmica",
            "GWh", _GWH, ",.1f", "pct", "suma", "olade", ""),
    VarBase("gen_eolica_kwh", "Generación eólica",
            "GWh", _GWH, ",.1f", "pct", "suma", "olade", ""),
    VarBase("gen_solar_kwh", "Generación solar",
            "GWh", _GWH, ",.1f", "pct", "suma", "olade", ""),
    VarBase("gen_biomasa_kwh", "Generación con biomasa",
            "GWh", _GWH, ",.1f", "pct", "suma", "olade", ""),
    VarBase("gen_renovable_kwh", "Generación renovable total",
            "GWh", _GWH, ",.1f", "pct", "suma", "olade",
            "Suma de las generaciones hidroeléctrica, geotérmica, eólica, "
            "solar y con biomasa."),
    VarBase("gen_fosil_kwh", "Generación térmica fósil",
            "GWh", _GWH, ",.1f", "pct", "suma", "olade", ""),
    VarBase("importaciones_kwh", "Importaciones de electricidad",
            "GWh", _GWH, ",.1f", "pct", "suma", "olade", ""),
    VarBase("exportaciones_kwh", "Exportaciones de electricidad",
            "GWh", _GWH, ",.1f", "pct", "suma", "olade", ""),
    VarBase("poblacion_habitantes", "Población total",
            "habitantes", 1, ",.0f", "pct", "suma", "cepal", ""),
    VarBase("pib_usd_const2015", "Producto interno bruto real",
            "millones de USD constantes de 2015", _MUSD, ",.0f", "pct",
            "suma", "bm", ""),
    VarBase("vai_usd_const2015", "Valor agregado manufacturero",
            "millones de USD constantes de 2015", _MUSD, ",.0f", "pct",
            "suma", "ods",
            "Calculado en el ETL como participación del valor agregado "
            "manufacturero en el PIB (indicador ODS 9.2.1) multiplicada "
            "por el PIB real."),
    VarBase("vai_pct_pib",
            "Participación del valor agregado manufacturero en el PIB",
            "%", 1, ".2f", "pp", "media", "ods", ""),
    VarBase("tarifa_usd_mwh", "Precio medio de la electricidad regulada",
            "USD corrientes por MWh", 1, ".1f", "pct", "media", "cepal",
            "Los valores marcados con asterisco se calculan mediante tasa "
            "de crecimiento anual compuesta (CAGR)."),
    VarBase(COLUMNA_ECO_CG, "Costo de generación eléctrica",
            "USD corrientes/MWh", 1, ".2f", "pct", "sin_resumen", "eco_cg",
            "Serie económica complementaria; no constituye un noveno "
            "indicador IEDS. Los proxies nacionales no son "
            "conceptualmente homólogos y no forman un costo agregado del "
            "SIEPAC."),
]

BASE_ENV = [
    VarBase("emisiones_gei_10e3t",
            "Emisiones de gases de efecto invernadero de las centrales "
            "eléctricas",
            "miles de toneladas de CO₂ equivalente", 1, ",.2f", "pct",
            "suma", "env", ""),
    VarBase("so2_10e3t",
            "Emisiones de dióxido de azufre de las centrales eléctricas",
            "miles de toneladas", 1, ",.3f", "pct", "suma", "env", ""),
    VarBase("nox_10e3t",
            "Emisiones de óxidos de nitrógeno de las centrales eléctricas",
            "miles de toneladas", 1, ",.4f", "pct", "suma", "env", ""),
    VarBase("co_10e3t",
            "Emisiones de monóxido de carbono de las centrales eléctricas",
            "miles de toneladas", 1, ",.3f", "pct", "suma", "env", ""),
    VarBase("particulas_10e3t",
            "Emisiones de material particulado de las centrales eléctricas",
            "miles de toneladas", 1, ",.4f", "pct", "suma", "env", ""),
    VarBase("pib_usd_const2015",
            "Producto interno bruto real empleado en la dimensión ambiental",
            "millones de USD constantes de 2015", 1, ",.1f", "pct", "suma",
            "env", "Serie de PIB correspondiente a la matriz ENVs.xlsx."),
]

BASE_SOC = [
    VarBase("pct_sin_electricidad", "Población sin acceso a electricidad",
            "%", 1, ".2f", "pp", "media", "soc", ""),
    VarBase("tasa_electrificacion_rural", "Tasa de electrificación rural",
            "%", 1, ".2f", "pp", "media", "soc", ""),
    VarBase("tasa_electrificacion_urbana", "Tasa de electrificación urbana",
            "%", 1, ".2f", "pp", "media", "soc", ""),
    VarBase("pct_renovable_generacion",
            "Participación de las renovables en la generación eléctrica",
            "%", 1, ".2f", "pp", "media", "soc",
            "Insumo del indicador SOC3; coincide con el indicador ECO13."),
]

# Variables comunes que se presentan una sola vez en las tablas de datos base.
OMITIDAS = {
    "env": ["poblacion_miles", "produccion_bruta_gwh"],
    "soc": [],
}

# ---------------------------------------------------------------------------
# ESTILOS EN LÍNEA
# Word descarta con frecuencia las hojas de estilo al pegar, pero respeta
# los atributos style de cada elemento: por eso van repetidos en línea.
# ---------------------------------------------------------------------------
S_SERIF = "'Times New Roman', Times, serif"
S_NUMERO = (f"font-family:{S_SERIF};font-size:12pt;font-weight:bold;"
            "margin:0;padding:0;")
S_TITULO = (f"font-family:{S_SERIF};font-size:12pt;font-style:italic;"
            "margin:0 0 6pt 0;padding:0;")
S_TABLA = ("border-collapse:collapse;width:100%;margin:0 0 6pt 0;"
           f"font-family:{S_SERIF};font-size:10.5pt;")
S_TH = ("border-top:1pt solid #000000;border-bottom:1pt solid #000000;"
        "padding:4pt 5pt;text-align:center;font-weight:normal;"
        "vertical-align:bottom;")
S_TH_IZQ = S_TH.replace("text-align:center", "text-align:left")
S_TD = "padding:3pt 5pt;text-align:right;vertical-align:top;"
S_TD_IZQ = "padding:3pt 5pt;text-align:left;vertical-align:top;"
S_BORDE_SUP = "border-top:1pt solid #000000;"
S_BORDE_INF = "border-bottom:1pt solid #000000;"
S_NOTA = (f"font-family:{S_SERIF};font-size:10.5pt;margin:0 0 24pt 0;"
          "padding:0;text-align:justify;")
S_BLOQUE = "margin:0 0 24pt 0;page-break-inside:avoid;"


# ---------------------------------------------------------------------------
# FORMATO DE VALORES
# ---------------------------------------------------------------------------

def _es_nulo(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def _fmt(v, formato: str) -> str:
    """Formatea un valor con el formato de la ficha. Sin dato -> 's.d.'."""
    if _es_nulo(v):
        return "s.d."
    return format(v, formato)


def _delta(v0, v4, tipo: str) -> str:
    """Variación 2020-2024: relativa (%) para magnitudes, en puntos
    porcentuales (pp) para las series que ya son porcentajes. Misma
    convención que docs/resumen_indicadores_SIEPAC.md."""
    if _es_nulo(v0) or _es_nulo(v4) or not v0:
        return "s.d."
    if tipo == "pp":
        return f"{v4 - v0:+.1f} pp"
    return f"{(v4 / v0 - 1) * 100:+.1f} %"


# ---------------------------------------------------------------------------
# CONSTRUCCIÓN DE UNA TABLA APA
# ---------------------------------------------------------------------------

def _celda(contenido: str, estilo: str, etiqueta: str = "td") -> str:
    return f'<{etiqueta} style="{estilo}">{contenido}</{etiqueta}>'


def tabla_apa(tabla: dict, con_nota: bool = True) -> str:
    """Devuelve el bloque HTML de una tabla con formato APA 7 a partir
    del diccionario que arman las funciones _bloque_*.

    El número y el título van encima (número en negrita, título en
    cursiva) y la nota, debajo. `filas` son los países y `resumen` las
    filas de cierre (promedio, agregado o total), que se separan con una
    línea horizontal. `cols_izq` es cuántas columnas iniciales se
    alinean a la izquierda (1 = País; 2 = País y Serie, como en ENV6).

    Con con_nota=False se omite la nota al pie y se usa el título que
    lleva la unidad entre paréntesis, para que la tabla siga siendo
    interpretable por sí sola: sin la nota, la unidad no aparecería en
    ninguna parte.
    """
    filas, resumen = tabla["filas"], tabla["resumen"]
    cols_izq = tabla["cols_izq"]
    titulo = tabla["titulo"] if con_nota else tabla["titulo_con_unidad"]

    # La tabla de convergencia económica creció con ECO-CG. Cerramos la tabla
    # anterior con un salto para que su rótulo no quede aislado en el corte.
    estilo_bloque = S_BLOQUE + (
        "page-break-after:always;" if tabla["numero"] == 60 else ""
    )
    partes = [f'<div id="tabla-{tabla["numero"]:02d}" '
              f'style="{estilo_bloque}">',
              f'<p style="{S_NUMERO}">Tabla {tabla["numero"]}</p>',
              f'<p style="{S_TITULO}">{titulo}</p>',
              f'<table style="{S_TABLA}"><thead><tr>']
    for i, enc in enumerate(tabla["encabezados"]):
        partes.append(_celda(enc, S_TH_IZQ if i < cols_izq else S_TH, "th"))
    partes.append("</tr></thead><tbody>")

    todas = [(f, False) for f in filas] + [(f, True) for f in resumen]
    for j, (fila, es_resumen) in enumerate(todas):
        primera_resumen = es_resumen and j == len(filas)
        ultima = j == len(todas) - 1
        partes.append("<tr>")
        for i, valor in enumerate(fila):
            estilo = S_TD_IZQ if i < cols_izq else S_TD
            if primera_resumen:
                estilo += S_BORDE_SUP
            if ultima:
                estilo += S_BORDE_INF
            partes.append(_celda(valor, estilo))
        partes.append("</tr>")
    partes.append("</tbody></table>")
    if con_nota:
        partes.append(f'<p style="{S_NOTA}"><i>Nota.</i> {tabla["nota"]}</p>')
    partes.append("</div>")
    return "\n".join(partes)


def _exportar_tabla_soc2_tesis(datos: dict) -> None:
    """Regenera la Tabla 7 del cuerpo de la tesis desde el agregado SOC2."""
    prom = datos["SOC2_PROM"].get("agregado")
    vulnerable = datos["SOC2_VULNERABLE"].get("agregado")
    if not prom or not vulnerable:
        raise ValueError("VALIDACIÓN FALLIDA: SOC2 no tiene agregado regional")

    filas = [[str(anio), f"{p:.3f}", f"{v:.3f}", f"{v - p:.3f}"]
             for anio, p, v in zip(ANIOS, prom, vulnerable)]
    tabla = dict(
        numero=7,
        titulo=f"SOC2 regional agregado del SIEPAC, {ANIOS[0]}–{ANIOS[-1]}",
        titulo_con_unidad=(f"SOC2 regional agregado del SIEPAC, "
                           f"{ANIOS[0]}–{ANIOS[-1]} (en %)"),
        encabezados=["Año", "SOC2_PROM (%)", "SOC2_VULNERABLE (%)",
                     "Brecha VUL–PROM (pp)"],
        filas=filas,
        resumen=[],
        nota=("Valores en porcentaje, calculados mediante razón de sumas; "
              "pp = puntos porcentuales."),
        cols_izq=1,
    )
    RUTA_SOC2_TESIS.write_text(
        PLANTILLA.format(
            titulo="Tabla 7 — SOC2 regional agregado",
            cuerpo=tabla_apa(tabla)),
        encoding="utf-8",
    )
    with open(RUTA_SOC2_TESIS_CSV, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f)
        escritor.writerow(["anio", "SOC2_PROM", "SOC2_VULNERABLE",
                           "brecha_vulnerable_prom_pp"])
        escritor.writerows([[anio, p, v, v - p]
                            for anio, p, v in zip(ANIOS, prom, vulnerable)])
    log.info("Exportada Tabla 7 de la tesis: %s", RUTA_SOC2_TESIS)


# ---------------------------------------------------------------------------
# TABLAS DE DATOS BASE
# ---------------------------------------------------------------------------

def _leer_datos_base() -> dict[str, pd.DataFrame]:
    """Bases comunes a libros y tablas, sin releer productos Excel."""
    hojas = leer_bases()
    eco_cg = cargar_eco_cg().rename(columns={CODIGO_ECO_CG: COLUMNA_ECO_CG})
    hojas["eco"] = hojas["eco"].merge(
        eco_cg, on=["pais", "anio"], how="left", validate="one_to_one")
    return hojas


def _bloque_base(numero: int, var: VarBase, base: pd.DataFrame,
                 imputados: dict | None) -> dict:
    """Tabla de una variable base: países en filas, años en columnas."""
    pivote = base.pivot(index="pais", columns="anio", values=var.columna)
    filas, series_pais = [], {}
    for pais in PAISES:
        vals = [None if pd.isna(pivote.loc[pais, a]) else
                float(pivote.loc[pais, a]) * var.escala for a in ANIOS]
        series_pais[pais] = vals
        celdas = []
        for i, v in enumerate(vals):
            marca = "*" if imputados and imputados[pais][i] else ""
            celdas.append(_fmt(v, var.formato) + marca)
        filas.append([pais] + celdas +
                     [_delta(vals[0], vals[-1], var.delta)])

    # Fila de cierre: total del bloque si la magnitud es sumable y media
    # simple si es una razón o un porcentaje que no se puede sumar.
    agregada = []
    for i in range(len(ANIOS)):
        vals = [series_pais[p][i] for p in PAISES if series_pais[p][i] is not None]
        if not vals:
            agregada.append(None)
        elif var.resumen == "suma":
            agregada.append(sum(vals))
        else:
            agregada.append(sum(vals) / len(vals))
    if var.resumen == "suma":
        etiqueta = "Total SIEPAC"
    else:
        etiqueta = "Promedio de países (media simple)"
    resumen = [[etiqueta] + [_fmt(v, var.formato) for v in agregada] +
               [_delta(agregada[0], agregada[-1], var.delta)]]

    titulo = f"{var.etiqueta} por país, {ANIOS[0]}–{ANIOS[-1]}"
    nota = (f"Valores en {var.unidad}. "
            f"Δ = variación {ANIOS[0]}–{ANIOS[-1]}"
            + (" en puntos porcentuales." if var.delta == "pp"
               else ", relativa.") + " ")
    if var.resumen == "suma":
        nota += "La última fila es la suma de los seis países."
    else:
        nota += "La última fila es la media simple de los seis países."
    if var.nota:
        nota += " " + var.nota
    if var.fuente == "eco_cg":
        nota += (" Elaboración propia a partir del archivo procesado "
                 "eco_cg_siepac.csv incorporado por el equipo de "
                 "investigación.")
    else:
        fuente = FUENTES_APA[var.fuente]
        nota += f" Elaboración propia con datos de {fuente}."

    encabezados = (["País"] + [str(a) for a in ANIOS] +
                   [f"Δ {ANIOS[0]}–{ANIOS[-1]}"])
    return dict(numero=numero, titulo=titulo,
                titulo_con_unidad=f"{titulo} (en {var.unidad})",
                encabezados=encabezados, filas=filas, resumen=resumen,
                nota=nota, cols_izq=1)


def _bloque_base_eco_cg(numero: int, base: pd.DataFrame) -> dict:
    """Matriz de proxies ECO-CG con nivel y banderas metodológicas.

    A diferencia de las demás variables base, esta tabla no cierra con una
    fila regional: los instrumentos nacionales no son conceptualmente
    homólogos. La estructura replica la Tabla 4 de la sección metodológica.
    """
    pivote = base.pivot(index="pais", columns="anio",
                        values=COLUMNA_ECO_CG)
    filas = []
    for pais in ORDEN_ECO_CG_DOCUMENTO:
        valores = []
        for anio in ANIOS:
            valor = float(pivote.loc[pais, anio])
            valores.append(_fmt(valor, ".2f")
                           + BANDERAS_ECO_CG.get((pais, anio), ""))
        filas.append([pais, str(NIVEL_ECO_CG[pais])] + valores)

    titulo = (f"Matriz {ETIQUETA_ECO_CG} de los países del SIEPAC, "
              f"{ANIOS[0]}–{ANIOS[-1]}")
    nota = (f"Valores en {FICHA_ECO_CG['unidad']}. {NOTA_CALIDAD_ECO_CG} "
            f"Elaboración propia a partir de {FUENTES_ECO_CG}.")
    return dict(
        numero=numero, titulo=titulo,
        titulo_con_unidad=f"{titulo} (en {FICHA_ECO_CG['unidad']})",
        encabezados=["País", "Nivel"] + [str(a) for a in ANIOS],
        filas=filas, resumen=[], nota=nota, cols_izq=1)


# ---------------------------------------------------------------------------
# TABLAS DE INDICADORES
# ---------------------------------------------------------------------------

def _armar_datos() -> tuple[dict, dict]:
    """Mismo empaquetado que generar_resumen_indicadores._armar_datos:
    {clave_serie: {paises, promedio, agregado}} + banderas de imputación
    de ECO14. El esquema compartido mantiene consistencia entre las tablas
    del documento y el resumen en Markdown."""
    datos = cargar_paquete()
    imputados = datos.pop("imputados")

    # ECO_CG es una serie económica complementaria y por eso no se añade a
    # FICHAS (el catálogo reservado a los IEDS). Sí se empaqueta aquí para
    # que participe en las tablas descriptivas del bloque.
    eco_cg = cargar_eco_cg()
    por_pais_cg = {
        pais: (eco_cg[eco_cg["pais"] == pais]
               .sort_values("anio")[CODIGO_ECO_CG].round(6).tolist())
        for pais in PAISES
    }
    promedio_cg = (eco_cg.groupby("anio")[CODIGO_ECO_CG]
                   .mean().reindex(ANIOS).round(6).tolist())
    datos[CODIGO_ECO_CG] = {
        "paises": por_pais_cg,
        "promedio": promedio_cg,
        "mediana": serie_mediana_eco_cg(eco_cg),
        "agregado": None,
    }
    return datos, imputados




def _fuente_indicador(codigo: str, dim: str) -> str:
    """Frase de atribución para la nota al pie del indicador."""
    if codigo == CODIGO_ECO_CG:
        return f"Elaboración propia a partir de {FUENTES_ECO_CG}."
    if dim == "env":
        return "Elaboración propia a partir de ENVs.xlsx."
    if dim == "soc":
        fuente = "SOCs.xlsx"
        if codigo == "SOC3":
            fuente += f" y {FUENTES_APA['bm_pob']}"
        return f"Elaboración propia a partir de {fuente}."
    claves = FUENTE_INDICADOR.get(codigo, "olade").split("+")
    citas = [FUENTES_APA[c] for c in claves]
    unidas = (citas[0] if len(citas) == 1
              else " y ".join([", ".join(citas[:-1]), citas[-1]]))
    return f"Elaboración propia con datos de {unidas}."


def _bloque_indicador(numero: int, codigo: str, ficha: dict, serie: dict,
                      bloque: dict, imputados: dict | None) -> dict:
    """Tabla de una serie de indicador: países en filas, años en columnas,
    y las filas de resumen del proyecto al cierre."""
    formato = serie["formato"]
    filas = []
    for pais in PAISES:
        vals = bloque["paises"][pais]
        celdas = []
        for i, v in enumerate(vals):
            marca = "*" if imputados and imputados[pais][i] else ""
            celdas.append(_fmt(v, formato) + marca)
        filas.append([pais] + celdas +
                     [_delta(vals[0], vals[-1], ficha["delta"])])

    prom = bloque["promedio"]
    resumen = [["Promedio de países (media simple)"] +
               [_fmt(v, formato) for v in prom] +
               [_delta(prom[0], prom[-1], ficha["delta"])]]
    agr = bloque.get("agregado")
    if agr:
        resumen.append(["Agregado regional (razón de sumas)"] +
                       [_fmt(v, formato) for v in agr] +
                       [_delta(agr[0], agr[-1], ficha["delta"])])

    # La etiqueta conserva su grafía original: los títulos APA van en
    # estilo titular y bajarla a minúsculas rompería SO₂, PIB, MER...
    sub = f", {serie['etiqueta']}" if serie["etiqueta"] else ""
    titulo = (f"{ficha['nombre']} ({serie['clave']}){sub}, por país, "
              f"{ANIOS[0]}–{ANIOS[-1]}")

    # Las filas de resumen se identifican por su etiqueta y su cálculo
    # está en las Convenciones de cálculo (Ec. 1 y 2): la nota solo
    # remite, no reexplica el método en cada una de las 21 tablas.
    nota = (f"Valores en {serie['unidad']}. Fórmula: {serie['formula']}. "
            f"Δ = variación {ANIOS[0]}–{ANIOS[-1]}"
            + (" en puntos porcentuales. " if ficha["delta"] == "pp"
               else ", relativa. "))
    nota += ("Filas de resumen: promedio de países (Ec. 2) y agregado "
             "regional (Ec. 1). " if agr
             else "Fila de resumen: promedio de países (Ec. 2). ")
    if ficha["nota"]:
        nota += ficha["nota"] + " "
    if imputados:
        nota += "El asterisco marca valores imputados vía CAGR. "
    nota += _fuente_indicador(codigo, ficha["dim"])

    encabezados = (["País"] + [str(a) for a in ANIOS] +
                   [f"Δ {ANIOS[0]}–{ANIOS[-1]}"])
    return dict(numero=numero, titulo=titulo,
                titulo_con_unidad=f"{titulo} (en {serie['unidad']})",
                encabezados=encabezados, filas=filas, resumen=resumen,
                nota=nota, cols_izq=1)


def _bloque_env6(numero: int, ficha: dict, datos: dict) -> dict:
    """ENV6 es un comparativo de dos series observadas, no un cociente:
    lleva una columna extra de serie y no admite filas de resumen."""
    filas = []
    for pais in PAISES:
        for nombre_s, clave in [("Inyección de biomasa", "biomasa"),
                                ("Saldo en el MER", "saldo")]:
            vals = datos["ENV6"][pais][clave]
            filas.append([pais, nombre_s] + [_fmt(v, ",.1f") for v in vals])

    titulo = (f"Inyección de biomasa y saldo neto en el Mercado Eléctrico "
              f"Regional (ENV6), por país, {ANIOS[0]}–{ANIOS[-1]}")
    nota = (f"Valores en {ficha['unidad']}. {ficha['descripcion']} "
            f"{ficha['nota']} No se reportan filas de resumen: la tabla "
            "contrasta dos series observadas y no calcula un cociente. "
            "Elaboración propia a partir de ENVs.xlsx.")
    encabezados = ["País", "Serie"] + [str(a) for a in ANIOS]
    return dict(numero=numero, titulo=titulo,
                titulo_con_unidad=f"{titulo} (en {ficha['unidad']})",
                encabezados=encabezados, filas=filas, resumen=[],
                nota=nota, cols_izq=2)


# ---------------------------------------------------------------------------
# DOCUMENTO
# ---------------------------------------------------------------------------

S_H1 = (f"font-family:{S_SERIF};font-size:16pt;margin:0 0 6pt 0;")
S_H2 = (f"font-family:{S_SERIF};font-size:13pt;margin:28pt 0 10pt 0;")
S_P = (f"font-family:{S_SERIF};font-size:11pt;margin:0 0 10pt 0;"
       "text-align:justify;")

PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{titulo}</title>
<style>
  body {{ background:#ffffff; color:#000000; margin:0; padding:32px;
         max-width:1000px; }}
  @media print {{ body {{ padding:0; }} }}
</style>
</head>
<body>
{cuerpo}
</body>
</html>
"""

INTRO = """<p style="{s_p}">Este archivo reúne las <b>{n} tablas</b> de la
fase cuantitativa del estudio con el formato de la 7.<sup>a</sup> edición
del Manual de Publicaciones de la APA: número de tabla en negrita, título
en cursiva, encabezados centrados, sin líneas verticales, con líneas
horizontales únicamente arriba y abajo de los encabezados y al cierre de
la tabla, y una nota al pie que declara unidad, fórmula, criterio de
agregación y fuente.</p>
<p style="{s_p}"><b>Cómo llevarlas a Word:</b> seleccione la tabla completa
en esta página —desde la línea «Tabla&nbsp;<i>n</i>» hasta el final de la
nota—, cópiela con Ctrl+C y péguela en Word con Ctrl+V. Word conserva la
estructura, los bordes y la cursiva. El índice enlaza directamente a cada
tabla dentro de este mismo archivo. La numeración es correlativa dentro de
este documento; si en el monográfico las tablas aparecen intercaladas con
otras, renumérelas según su orden final de aparición.</p>
<p style="{s_p}">Cobertura: {paises}, ventana {a0}–{a1}.
«s.d.» indica que no hay dato para esa celda. Documento generado
automáticamente por <i>src/generar_tablas_apa.py</i> el {fecha}; los
valores provienen del mismo pipeline que alimenta los visualizadores y el
resumen metodológico del proyecto.</p>
"""

INTRO_SIN_NOTAS = """<p style="{s_p}">Esta es la <b>versión sin notas</b>
de las {n} tablas de la fase cuantitativa: cada tabla lleva únicamente su
número, su título y los datos, para intercalarlas en el cuerpo del
monográfico sin arrastrar el aparato metodológico. La unidad de medida se
trasladó al título, entre paréntesis, para que ninguna tabla quede sin
declarar en qué se expresan sus cifras.</p>
<p style="{s_p}">Las notas completas —fórmula, criterio de agregación y
fuente de cada serie— están en <i>tablas_apa_SIEPAC.docx</i>, con la misma
numeración.</p>
<p style="{s_p}">Cobertura: {paises}, ventana {a0}–{a1}.
«s.d.» indica que no hay dato para esa celda. El asterisco identifica valores
calculados mediante CAGR. Documento generado automáticamente por
<i>src/generar_tablas_apa.py</i> el {fecha}.</p>
"""


def _seccion(titulo: str, parrafos: list[str]) -> list[str]:
    bloque = [f'<h2 style="{S_H2}">{titulo}</h2>']
    bloque += [f'<p style="{S_P}">{p}</p>' for p in parrafos]
    return bloque


# ---------------------------------------------------------------------------
# CONVENCIONES DE CÁLCULO (leyenda del archivo)
# Las notas al pie remiten a estas ecuaciones en lugar de reexplicar el
# método en cada tabla. La numeración Ec. 1–5 es la misma del capítulo
# cuantitativo (analisis-eco/generar_documento_eco.py), de modo que quien
# lea la tabla dentro de la tesis encuentre la referencia ya definida.
# Va marcado como bloque propio para poder omitirlo al insertar las
# tablas en el monográfico, donde las ecuaciones ya están numeradas.
# ---------------------------------------------------------------------------

_ECUACIONES_LEYENDA = [
    ("1", "Agregado regional (razón de sumas)",
     "I<sup>RS</sup><sub>t</sub> = Σ<sub>i</sub> N<sub>i,t</sub> ÷ "
     "Σ<sub>i</sub> D<sub>i,t</sub>"),
    ("2", "Promedio de países (media simple)",
     "x̄<sub>t</sub> = (1/6) Σ<sub>i</sub> I<sub>i,t</sub>"),
    ("3", "Desviación estándar poblacional (DE)",
     "σ<sub>t</sub> = √[(1/6) Σ<sub>i</sub> (I<sub>i,t</sub> − "
     "x̄<sub>t</sub>)²]"),
    ("4", "Coeficiente de variación (CV)",
     "CV<sub>t</sub> = σ<sub>t</sub> ÷ |x̄<sub>t</sub>| × 100"),
    ("5", "Tasa de crecimiento anual compuesta (CAGR)",
     f"CAGR = (V<sub>{ANIOS[-1]}</sub> ÷ V<sub>{ANIOS[0]}</sub>)"
     f"<sup>1/{len(ANIOS) - 1}</sup> − 1"),
]


def _leyenda_convenciones() -> list[str]:
    """Bloque «Convenciones de cálculo»: la leyenda a la que remiten las
    notas. Se emite como sección separada para poder omitirla al pegar
    las tablas dentro del capítulo."""
    celda = ("border:0;padding:3pt 10pt 3pt 0;vertical-align:top;"
             f"font-family:{S_SERIF};font-size:10.5pt;")
    filas = "".join(
        f'<tr><td style="{celda}white-space:nowrap;">({n})</td>'
        f'<td style="{celda}">{nombre}</td>'
        f'<td style="{celda}">{formula}</td></tr>'
        for n, nombre, formula in _ECUACIONES_LEYENDA)
    return [
        f'<h2 style="{S_H2}">Convenciones de cálculo</h2>',
        f'<p style="{S_P}">Las notas al pie de las tablas remiten a las '
        'ecuaciones siguientes, con la misma numeración que el capítulo '
        'cuantitativo. Sea <i>I</i><sub>i,t</sub> el valor del indicador '
        f'en el país i (i = 1, …, {len(PAISES)}) y el año t '
        f'(t = {ANIOS[0]}, …, {ANIOS[-1]}), construido como el cociente '
        'entre un numerador <i>N</i><sub>i,t</sub> y un denominador '
        '<i>D</i><sub>i,t</sub> propios de cada indicador.</p>',
        ('<table style="border-collapse:collapse;margin:0 0 12pt 0;">'
         f'{filas}</table>'),
        f'<p style="{S_P}">Los {len(PAISES)} países interconectados '
        'forman el universo completo del bloque, de modo que el '
        'tratamiento es descriptivo, la desviación estándar se calcula '
        f'con denominador N = {len(PAISES)} (Ec. 3) y no procede la '
        'inferencia estadística. La Ec. 1 se aplica a los indicadores '
        'con numerador y denominador agregables. ECO14 y ECO-CG se '
        'resumen con la mediana de países; ninguna de las dos medidas se '
        'denomina agregado regional por falta de un ponderador compatible. '
        'En ECO-CG, además, los proxies nacionales pertenecen a distintos '
        'niveles metodológicos. '
        'El promedio de países (Ec. 2) '
        'y el agregado regional (Ec. 1) responden preguntas distintas y '
        'pueden divergir incluso en el signo de la tendencia, por lo que '
        'ambos se reportan siempre etiquetados.</p>',
    ]


# ---------------------------------------------------------------------------
# TABLAS DE ESTADÍSTICA DESCRIPTIVA DEL BLOQUE (dimensión económica)
# Los seis países son el universo del SIEPAC, no una muestra: el marco es
# descriptivo (niveles, dispersión, convergencia, composición) y no
# procede inferencia. Misma numeración corrida que el resto del documento.
# ---------------------------------------------------------------------------

ECO_BLOQUE = ["ECO1", "ECO2", "ECO3", "ECO6", "ECO11", "ECO13",
              "ECO14", CODIGO_ECO_CG, "ECO15"]
FICHAS_BLOQUE_ECO = {**FICHAS, CODIGO_ECO_CG: FICHA_ECO_CG}

# El carácter censal del bloque y la definición de σ, CV y las ecuaciones
# se declaran una sola vez en las Convenciones de cálculo del encabezado
# del archivo; las notas de tabla remiten a ellas en lugar de repetirlas.


def _valores_anio(datos: dict, codigo: str, i: int) -> list[float]:
    """Los seis valores nacionales del año i-ésimo de la ventana."""
    return [datos[codigo]["paises"][p][i] for p in PAISES
            if not _es_nulo(datos[codigo]["paises"][p][i])]








def _serie_bloque(datos: dict, codigo: str) -> list[float]:
    """Serie de nivel: agregado, salvo ECO14 y ECO-CG (mediana)."""
    if codigo == CODIGO_ECO_CG:
        return datos[codigo]["mediana"]
    agr = datos[codigo].get("agregado")
    if agr:
        return agr
    return [_mediana(_valores_anio(datos, codigo, i))
            for i in range(len(ANIOS))]


def _cagr_txt(v0: float, v4: float) -> str:
    """CAGR de la ventana; «s.d.» si un extremo no es positivo (el
    exponente fraccionario no está definido con cambio de signo)."""
    if _es_nulo(v0) or _es_nulo(v4) or v0 <= 0 or v4 <= 0:
        return "s.d."
    return f"{((v4 / v0) ** (1 / (len(ANIOS) - 1)) - 1) * 100:+.2f}"


def _bloque_tendencia(numero: int, datos: dict) -> dict:
    """Tabla única: nivel y tendencia del bloque por indicador ECO."""
    filas = []
    # Las participaciones se expresan como cambio en puntos porcentuales.
    # ECO15 puede cambiar de signo, por lo que la CAGR no está definida.
    sin_cagr = ("ECO11", "ECO13", "ECO15")
    for cod in ECO_BLOQUE:
        f = FICHAS_BLOQUE_ECO[cod]
        s = _serie_bloque(datos, cod)
        if cod == "ECO14":
            marca = "†"
        elif cod == CODIGO_ECO_CG:
            marca = "‡"
        else:
            marca = ""
        etiqueta = ETIQUETA_ECO_CG if cod == CODIGO_ECO_CG else cod
        filas.append(
            [f"{etiqueta}. {f['nombre']} ({f['unidad']}){marca}"]
            + [_fmt(v, f["formato"]) for v in s]
            + [_delta(s[0], s[-1], f["delta"]),
               "n.a." if cod in sin_cagr else _cagr_txt(s[0], s[-1])])
    titulo = (f"Nivel y tendencia de las series económicas del SIEPAC, "
              f"{ANIOS[0]}–{ANIOS[-1]}")
    nota = ("Las series con numerador y denominador compatibles se resumen "
            "mediante el agregado regional (Ec. 1). La daga (†) marca "
            "ECO14, resumido con la mediana de países por falta de "
            "ponderador. La doble daga (‡) marca ECO-CG, resumido con la "
            "mediana descriptiva de los proxies nacionales; no constituye "
            "un costo agregado del SIEPAC. "
            f"Δ = variación {ANIOS[0]}–{ANIOS[-1]}, "
            "relativa o en puntos porcentuales según la serie; CAGR "
            "(Ec. 5) en % por año, «n.a.» donde no procede calcularla "
            "sobre una participación. En ECO14, 2023–2024 (y 2022 en El "
            "Salvador) se calculan mediante CAGR. Elaboración propia a "
            "partir de las tablas de valores económicos de este archivo.")
    return dict(
        numero=numero, titulo=titulo,
        titulo_con_unidad=f"{titulo} (unidad indicada en cada fila)",
        encabezados=["Indicador"] + [str(a) for a in ANIOS]
                    + [f"Δ {ANIOS[0]}–{ANIOS[-1]}", "CAGR (%/año)"],
        filas=filas, resumen=[], nota=nota, cols_izq=1)


def _bloque_heterogeneidad(numero: int, codigo: str, datos: dict) -> dict:
    """Una tabla por indicador: dispersión entre países, año a año.

    Los valores mínimo y máximo se presentan sin identificar el país:
    la sección describe la amplitud del bloque como sistema, y quien
    necesite la cifra de un país concreto la tiene en las tablas de
    indicadores por país de este mismo documento.
    """
    f = FICHAS_BLOQUE_ECO[codigo]
    fmt = f["formato"]
    filas = []
    for i, anio in enumerate(ANIOS):
        v = _valores_anio(datos, codigo, i)
        formato_cv = ".2f" if codigo == CODIGO_ECO_CG else ".1f"
        filas.append([str(anio), _fmt(sum(v) / len(v), fmt),
                      _fmt(_mediana(v), fmt), _fmt(_de_poblacional(v), fmt),
                      format(_cv_pct(v), formato_cv),
                      _fmt(min(v), fmt), _fmt(max(v), fmt),
                      _fmt(max(v) - min(v), fmt)])
    etiqueta = ETIQUETA_ECO_CG if codigo == CODIGO_ECO_CG else codigo
    titulo = (f"Estadística descriptiva de {f['nombre']} ({etiqueta}) entre "
              f"los países del SIEPAC, por año, {ANIOS[0]}–{ANIOS[-1]}")
    nota = (f"Estadísticos de los seis valores nacionales de cada año, "
            f"en {f['unidad']}; DE (Ec. 3) y CV (Ec. 4). Esos valores "
            "están en la tabla del indicador por país. ")
    if codigo == "ECO15":
        nota += ("El CV se calcula sobre una media cercana a cero "
                 "con signos mixtos, de modo que no es interpretable "
                 "como dispersión relativa y la lectura corresponde a la "
                 "DE absoluta y al rango, en puntos porcentuales. ")
    if codigo == "ECO14":
        nota += ("Los estadísticos de 2023–2024 (y 2022 en El Salvador) "
                 "incorporan valores imputados vía CAGR. ")
    if codigo == CODIGO_ECO_CG:
        nota += ("Serie económica complementaria; no constituye un noveno "
                 "indicador IEDS. Son estadísticos no ponderados y no "
                 "constituyen un costo "
                 "regional ni corrigen la diferencia entre niveles "
                 "metodológicos. Los resultados de 2024 incluyen las "
                 "banderas de calidad de la matriz ECO-CG. ")
    if f["nota"] and codigo != CODIGO_ECO_CG:
        nota += f["nota"] + " "
    nota += _fuente_indicador(codigo, f["dim"])
    return dict(
        numero=numero, titulo=titulo,
        titulo_con_unidad=f"{titulo} (en {f['unidad']}; CV en %)",
        encabezados=["Año", "Media", "Mediana", "DE", "CV (%)",
                     "Mínimo", "Máximo", "Rango"],
        filas=filas, resumen=[], nota=nota, cols_izq=1)


def _bloque_convergencia(numero: int, datos: dict) -> dict:
    """Tabla única: convergencia sigma (trayectoria del CV) por indicador."""
    filas = []
    for cod in ECO_BLOQUE:
        f = FICHAS_BLOQUE_ECO[cod]
        if cod == "ECO15":
            # CV sobre media cercana a cero con signos mixtos: no es
            # interpretable; no se publican sus CV ni se emite veredicto.
            filas.append([f"{cod}. {f['nombre']}"]
                         + ["—"] * len(ANIOS) + ["—", "No aplicable"])
            continue
        cvs = [_cv_pct(_valores_anio(datos, cod, i))
               for i in range(len(ANIOS))]
        delta = cvs[-1] - cvs[0]
        etiqueta = ETIQUETA_ECO_CG if cod == CODIGO_ECO_CG else cod
        if cod == CODIGO_ECO_CG:
            lectura = "No aplicable"
        else:
            lectura = "Convergen" if delta < 0 else "Divergen"
        filas.append([f"{etiqueta}. {f['nombre']}"]
                     + [f"{cv:.1f}" for cv in cvs]
                     + [f"{delta:+.1f}", lectura])
    titulo = ("Convergencia sigma entre los países del SIEPAC por serie "
              f"económica, {ANIOS[0]}–{ANIOS[-1]}")
    nota = ("CV de los seis valores nacionales de cada año (Ec. 4). Una "
            "caída en la ventana (Δ negativo) indica convergencia sigma "
            "—los países se asemejan— y un aumento, divergencia. En "
            "ECO15 el CV no es interpretable, porque la media es "
            "cercana a cero con signos mixtos, y su dispersión se lee "
            "en la tabla del indicador. Para ECO14, el contraste de "
            "convergencia utiliza 2020–2022. Los CV de ECO-CG se muestran "
            "solo como estadísticos descriptivos; no se emite un dictamen "
            "de convergencia porque los proxies no son conceptualmente "
            "homólogos. "
            "Elaboración propia a partir de las tablas de valores económicos "
            "de este archivo.")
    return dict(
        numero=numero, titulo=titulo,
        titulo_con_unidad=f"{titulo} (CV en %)",
        encabezados=["Indicador"] + [f"CV {a}" for a in ANIOS]
                    + ["Δ (pp)", "Lectura"],
        filas=filas, resumen=[], nota=nota, cols_izq=1)


def _tablas_bloque(inicio: int, datos: dict) -> list[dict]:
    """Lista de tablas de estadística descriptiva del bloque, numeradas
    desde `inicio`: tendencia, heterogeneidad (una por indicador) y
    convergencia sigma. Todas describen al bloque como sistema, sin
    identificar países."""
    tablas = [(_bloque_tendencia(inicio, datos), "BLOQUE_TENDENCIA")]
    n = inicio + 1
    for cod in ECO_BLOQUE:
        tablas.append((_bloque_heterogeneidad(n, cod, datos),
                       f"BLOQUE_HET_{cod}"))
        n += 1
    tablas.append((_bloque_convergencia(n, datos), "BLOQUE_CONVERGENCIA"))
    for t, codigo in tablas:
        t.update(seccion="Estadística descriptiva del bloque (económica)",
                 codigo=codigo, dim="eco")
    return [t for t, _ in tablas]


# ---------------------------------------------------------------------------
# ESTADÍSTICA DESCRIPTIVA SOCIAL (compacta, posterior a ECO)
# Se mantiene separada para conservar la numeración 50-59 de las tablas
# económicas ya utilizadas en el análisis de la monografía.
# ---------------------------------------------------------------------------

SOC_REGION = [("SOC1", "SOC1"),
              ("SOC2", "SOC2_PROM"),
              ("SOC2", "SOC2_VULNERABLE"),
              ("SOC3", "SOC3_RURAL"),
              ("SOC3", "SOC3_URB")]
SOC_PAISES = [("SOC1", "SOC1"),
              ("SOC2", "SOC2_PROM"),
              ("SOC2", "SOC2_VULNERABLE"),
              ("SOC3", "SOC3_RURAL"),
              ("SOC3", "SOC3_URB")]
SOC2_SERIES = [("SOC2", "SOC2_PROM"),
               ("SOC2", "SOC2_VULNERABLE")]


def _info_subserie(codigo: str, clave: str) -> tuple[dict, dict]:
    ficha = FICHAS[codigo]
    serie = next(s for s in _series_de(ficha, codigo)
                 if s["clave"] == clave)
    return ficha, serie


def _nombre_subserie(codigo: str, clave: str) -> str:
    ficha, serie = _info_subserie(codigo, clave)
    sufijo = f" — {serie['etiqueta']}" if serie["etiqueta"] else ""
    return f"{clave}. {ficha['nombre']}{sufijo}"


def _bloque_tendencia_social(numero: int, datos: dict) -> dict:
    """Nivel y variación de las series SOC con agregado regional."""
    filas = []
    for codigo, clave in SOC_REGION:
        ficha, serie = _info_subserie(codigo, clave)
        agregado = datos[clave].get("agregado")
        if not agregado:
            raise ValueError(f"{clave} no tiene agregado regional.")
        filas.append(
            [f"{_nombre_subserie(codigo, clave)} ({serie['unidad']})"]
            + [_fmt(v, serie["formato"]) for v in agregado]
            + [_delta(agregado[0], agregado[-1], ficha["delta"])])

    titulo = ("Nivel y tendencia regional de los indicadores sociales "
              f"agregables del SIEPAC, {ANIOS[0]}–{ANIOS[-1]}")
    nota = ("SOC1 pondera por población total; SOC2 reconstruye gasto e "
            "ingreso agregados aproximados en USD; SOC3_RURAL pondera por "
            "población rural y SOC3_URB, por población urbana. Cada fila "
            "es una razón de sumas (Ec. 1). Δ se expresa en puntos "
            "porcentuales. "
            "SOC3 combina la tasa de electrificación de cada zona con la "
            "participación renovable nacional. Elaboración propia a partir de las tablas "
            "de indicadores de este archivo.")
    return dict(
        numero=numero, titulo=titulo,
        titulo_con_unidad=f"{titulo} (en %)",
        encabezados=["Indicador"] + [str(a) for a in ANIOS]
                    + [f"Δ {ANIOS[0]}–{ANIOS[-1]}"],
        filas=filas, resumen=[], nota=nota, cols_izq=1)


def _bloque_heterogeneidad_social(numero: int, datos: dict) -> dict:
    """Dispersión nacional de SOC en los extremos de la ventana."""
    filas = []
    for codigo, clave in SOC_PAISES:
        _, serie = _info_subserie(codigo, clave)
        for i in (0, len(ANIOS) - 1):
            valores = _valores_anio(datos, clave, i)
            formato = serie["formato"]
            filas.append([
                _nombre_subserie(codigo, clave), str(ANIOS[i]),
                str(len(valores)), _fmt(sum(valores) / len(valores), formato),
                _fmt(_mediana(valores), formato),
                _fmt(_de_poblacional(valores), formato),
                _fmt(min(valores), formato), _fmt(max(valores), formato),
                _fmt(max(valores) - min(valores), formato),
            ])

    titulo = ("Heterogeneidad de los indicadores sociales entre los países "
              f"del SIEPAC, {ANIOS[0]} y {ANIOS[-1]}")
    nota = ("Estadísticos descriptivos de los valores nacionales, en %; "
            "DE poblacional (Ec. 3). n indica los países con dato. En SOC2, "
            "la mediana y el rango complementan la media. Esta tabla "
            "describe diferencias entre países y no sustituye el agregado "
            "regional. Elaboración propia a partir de las tablas de "
            "indicadores de este archivo.")
    return dict(
        numero=numero, titulo=titulo,
        titulo_con_unidad=f"{titulo} (en %)",
        encabezados=["Serie", "Año", "n", "Media", "Mediana", "DE",
                     "Mínimo", "Máximo", "Rango"],
        filas=filas, resumen=[], nota=nota, cols_izq=2)




def _bloque_soc2_anual(numero: int, datos: dict) -> dict:
    """Descripción anual completa de las dos series SOC2."""
    filas = []
    for codigo, clave in SOC2_SERIES:
        _, serie = _info_subserie(codigo, clave)
        for i, anio in enumerate(ANIOS):
            e = _estadisticos_paises(_valores_anio(datos, clave, i))
            filas.append([
                serie["etiqueta"], str(anio), str(e["n"]),
                _fmt(e["media"], ".2f"), _fmt(e["mediana"], ".2f"),
                _fmt(e["de"], ".2f"), _fmt(e["minimo"], ".2f"),
                _fmt(e["maximo"], ".2f"), _fmt(e["rango"], ".2f"),
            ])
    titulo = ("Estadística descriptiva anual del ingreso destinado a "
              f"electricidad en los países del SIEPAC, {ANIOS[0]}–"
              f"{ANIOS[-1]}")
    nota = ("Estadísticos de los seis valores nacionales de cada año, en "
            "porcentaje. La DE es poblacional porque se incluyen todos "
            "los países del SIEPAC. La media resume el nivel conjunto; "
            "la mediana identifica el centro de la distribución y el "
            "rango muestra su amplitud. Elaboración propia a partir de "
            "las tablas SOC2 de este archivo.")
    return dict(
        numero=numero, titulo=titulo,
        titulo_con_unidad=f"{titulo} (en %)",
        encabezados=["Serie", "Año", "n", "Media", "Mediana", "DE",
                     "Mínimo", "Máximo", "Rango"],
        filas=filas, resumen=[], nota=nota, cols_izq=2)


def _bloque_soc2_cambio(numero: int, datos: dict) -> dict:
    """Contrasta centro y dispersión de SOC2 entre 2020 y 2024."""
    filas = []
    for codigo, clave in SOC2_SERIES:
        _, serie = _info_subserie(codigo, clave)
        e0 = _estadisticos_paises(_valores_anio(datos, clave, 0))
        e4 = _estadisticos_paises(_valores_anio(datos, clave, -1))
        filas.append([
            serie["etiqueta"], _fmt(e0["media"], ".2f"),
            _fmt(e4["media"], ".2f"),
            f"{e4['media'] - e0['media']:+.2f}",
            _fmt(e0["mediana"], ".2f"),
            _fmt(e4["mediana"], ".2f"),
            f"{e4['mediana'] - e0['mediana']:+.2f}",
            _fmt(e0["de"], ".2f"), _fmt(e4["de"], ".2f"),
        ])
    titulo = ("Cambio en el nivel y la dispersión de SOC2 entre "
              f"{ANIOS[0]} y {ANIOS[-1]}")
    nota = ("Valores y cambios en puntos porcentuales. Una reducción de "
            "la DE indica mayor cercanía entre los resultados nacionales; "
            "un aumento indica mayor heterogeneidad. La media y la "
            "mediana se presentan juntas para distinguir el comportamiento "
            "general de la influencia de valores extremos. Elaboración "
            "propia a partir de las tablas SOC2 de este archivo.")
    return dict(
        numero=numero, titulo=titulo,
        titulo_con_unidad=f"{titulo} (en puntos porcentuales)",
        encabezados=["Serie", "Media 2020", "Media 2024", "Δ media",
                     "Mediana 2020", "Mediana 2024", "Δ mediana",
                     "DE 2020", "DE 2024"],
        filas=filas, resumen=[], nota=nota, cols_izq=1)


def _tablas_sociales(inicio: int, datos: dict) -> list[dict]:
    tablas = [
        (_bloque_tendencia_social(inicio, datos), "BLOQUE_SOC_TENDENCIA"),
        (_bloque_heterogeneidad_social(inicio + 1, datos),
         "BLOQUE_SOC_HETEROGENEIDAD"),
        (_bloque_soc2_anual(inicio + 2, datos),
         "BLOQUE_SOC2_DESCRIPTIVOS"),
        (_bloque_soc2_cambio(inicio + 3, datos),
         "BLOQUE_SOC2_CAMBIO"),
    ]
    for tabla, codigo in tablas:
        tabla.update(
            seccion="Estadística descriptiva del bloque (social)",
            codigo=codigo, dim="soc")
    return [tabla for tabla, _ in tablas]


# ---------------------------------------------------------------------------
# ESTADÍSTICA DESCRIPTIVA AMBIENTAL
# Se agrega después del bloque social para conservar intacta la numeración
# 50-63 ya utilizada en el análisis de las dimensiones ECO y SOC.
# ---------------------------------------------------------------------------

ENV_SERIES = [
    ("ENV1", "ENV1_PC"),
    ("ENV1", "ENV1_PIB"),
    ("ENV2", "ENV2_SO2_PC"),
    ("ENV2", "ENV2_PAR_PC"),
    ("ENV2", "ENV2_SO2_PIB"),
    ("ENV2", "ENV2_PAR_PIB"),
    ("ENV3", "ENV3"),
]


def _bloque_tendencia_ambiental(numero: int, datos: dict) -> dict:
    """Nivel y variación de los agregados regionales ENV1-ENV3."""
    filas = []
    for codigo, clave in ENV_SERIES:
        ficha, serie = _info_subserie(codigo, clave)
        agregado = datos[clave].get("agregado")
        if not agregado:
            raise ValueError(f"{clave} no tiene agregado regional.")
        filas.append(
            [f"{_nombre_subserie(codigo, clave)} ({serie['unidad']})"]
            + [_fmt(v, serie["formato"]) for v in agregado]
            + [_delta(agregado[0], agregado[-1], ficha["delta"])])

    titulo = ("Nivel y tendencia regional de los indicadores ambientales "
              f"del SIEPAC, {ANIOS[0]}–{ANIOS[-1]}")
    nota = ("Cada fila corresponde al agregado regional calculado como "
            "razón de sumas (Ec. 1), con el denominador indicado en la "
            "unidad: población, PIB real o producción eléctrica bruta. "
            f"Δ = variación relativa {ANIOS[0]}–{ANIOS[-1]}. En estos "
            "indicadores de intensidad, una cifra menor representa menos "
            "emisiones por unidad del denominador, aunque no necesariamente "
            "una reducción de las emisiones totales. Elaboración propia a "
            "partir de las tablas ENV1–ENV3 de este archivo.")
    return dict(
        numero=numero, titulo=titulo,
        titulo_con_unidad=f"{titulo} (unidad indicada en cada fila)",
        encabezados=["Indicador"] + [str(a) for a in ANIOS]
                    + [f"Δ {ANIOS[0]}–{ANIOS[-1]}"],
        filas=filas, resumen=[], nota=nota, cols_izq=1)


def _bloque_heterogeneidad_ambiental(numero: int, codigo: str,
                                     clave: str, datos: dict) -> dict:
    """Dispersión anual de una subserie ambiental entre los seis países."""
    ficha, serie = _info_subserie(codigo, clave)
    filas = []
    for i, anio in enumerate(ANIOS):
        valores = _valores_anio(datos, clave, i)
        e = _estadisticos_paises(valores)
        filas.append([
            str(anio), str(e["n"]),
            _fmt(e["media"], serie["formato"]),
            _fmt(e["mediana"], serie["formato"]),
            _fmt(e["de"], serie["formato"]), f"{_cv_pct(valores):.1f}",
            _fmt(e["minimo"], serie["formato"]),
            _fmt(e["maximo"], serie["formato"]),
            _fmt(e["rango"], serie["formato"]),
        ])

    titulo = (f"Estadística descriptiva de {ficha['nombre']} ({clave}), "
              f"{serie['etiqueta']}, entre los países del SIEPAC, "
              f"{ANIOS[0]}–{ANIOS[-1]}")
    nota = (f"Estadísticos de los valores nacionales, en {serie['unidad']}; "
            "DE poblacional (Ec. 3) y CV (Ec. 4). n indica los países con "
            "dato. La media y la mediana describen al conjunto de países; "
            "no sustituyen el agregado regional de la tabla de tendencia. "
            f"{_fuente_indicador(codigo, ficha['dim'])}")
    return dict(
        numero=numero, titulo=titulo,
        titulo_con_unidad=f"{titulo} (en {serie['unidad']}; CV en %)",
        encabezados=["Año", "n", "Media", "Mediana", "DE", "CV (%)",
                     "Mínimo", "Máximo", "Rango"],
        filas=filas, resumen=[], nota=nota, cols_izq=1)


def _bloque_convergencia_ambiental(numero: int, datos: dict) -> dict:
    """Trayectoria del CV de las intensidades ambientales nacionales."""
    filas = []
    for codigo, clave in ENV_SERIES:
        cvs = [_cv_pct(_valores_anio(datos, clave, i))
               for i in range(len(ANIOS))]
        delta = cvs[-1] - cvs[0]
        lectura = ("Convergen" if delta < 0 else
                   "Divergen" if delta > 0 else "Sin cambio")
        filas.append([_nombre_subserie(codigo, clave)]
                     + [f"{cv:.1f}" for cv in cvs]
                     + [f"{delta:+.1f}", lectura])

    titulo = ("Convergencia sigma entre los países del SIEPAC por "
              f"indicador ambiental, {ANIOS[0]}–{ANIOS[-1]}")
    nota = ("CV de los seis valores nacionales de cada año (Ec. 4). Una "
            "reducción del CV indica convergencia sigma y un aumento, "
            "divergencia. Esta lectura describe si las intensidades "
            "nacionales se acercan entre sí; no determina por sí sola una "
            "mejora ambiental, que debe evaluarse junto con el nivel del "
            "indicador. Elaboración propia a partir de las tablas ENV1–ENV3 "
            "de este archivo.")
    return dict(
        numero=numero, titulo=titulo,
        titulo_con_unidad=f"{titulo} (CV en %)",
        encabezados=["Indicador"] + [f"CV {a}" for a in ANIOS]
                    + ["Δ (pp)", "Lectura"],
        filas=filas, resumen=[], nota=nota, cols_izq=1)


def _bloque_env6_descriptivo(numero: int, datos: dict) -> dict:
    """Descriptivos anuales de biomasa y saldo MER, sin emplear CV."""
    filas = []
    for etiqueta, clave in [("Inyección de biomasa", "biomasa"),
                            ("Saldo neto en el MER", "saldo")]:
        for i, anio in enumerate(ANIOS):
            valores = [datos["ENV6"][pais][clave][i] for pais in PAISES]
            e = _estadisticos_paises(valores)
            filas.append([
                etiqueta, str(anio), str(e["n"]),
                _fmt(e["media"], ",.1f"), _fmt(e["mediana"], ",.1f"),
                _fmt(e["de"], ",.1f"), _fmt(e["minimo"], ",.1f"),
                _fmt(e["maximo"], ",.1f"), _fmt(e["rango"], ",.1f"),
            ])

    titulo = ("Estadística descriptiva anual de la inyección de biomasa y "
              "el saldo neto en el MER (ENV6) entre los países del SIEPAC, "
              f"{ANIOS[0]}–{ANIOS[-1]}")
    nota = ("Estadísticos de los seis valores nacionales de cada año, en "
            "GWh; DE poblacional (Ec. 3). El saldo conserva su signo: los "
            "valores negativos identifican importadores netos según la "
            "convención del indicador. No se calcula CV para el saldo "
            "porque combina signos y su media puede aproximarse a cero. "
            "ENV6 es un comparativo descriptivo de dos series observadas, "
            "no un cociente. Elaboración propia a partir de la tabla ENV6 "
            "de este archivo.")
    return dict(
        numero=numero, titulo=titulo,
        titulo_con_unidad=f"{titulo} (en GWh)",
        encabezados=["Serie", "Año", "n", "Media", "Mediana", "DE",
                     "Mínimo", "Máximo", "Rango"],
        filas=filas, resumen=[], nota=nota, cols_izq=2)


def _tablas_ambientales(inicio: int, datos: dict) -> list[dict]:
    """Tablas ambientales agregadas sin renumerar los bloques previos."""
    tablas = [(_bloque_tendencia_ambiental(inicio, datos),
               "BLOQUE_ENV_TENDENCIA")]
    n = inicio + 1
    for codigo, clave in ENV_SERIES:
        tablas.append((
            _bloque_heterogeneidad_ambiental(n, codigo, clave, datos),
            f"BLOQUE_HET_{clave}"))
        n += 1
    tablas.append((_bloque_convergencia_ambiental(n, datos),
                   "BLOQUE_ENV_CONVERGENCIA"))
    n += 1
    tablas.append((_bloque_env6_descriptivo(n, datos),
                   "BLOQUE_ENV6_DESCRIPTIVOS"))
    for tabla, codigo in tablas:
        tabla.update(
            seccion="Estadística descriptiva del bloque (ambiental)",
            codigo=codigo, dim="env")
    return [tabla for tabla, _ in tablas]


def _tablas_base(inicio: int, hojas: dict, imputados: dict) -> list[dict]:
    """Lista de tablas de datos base, numeradas desde `inicio`."""
    tablas, n = [], inicio
    catalogo = [("eco", "económica", BASE_ECO), ("env", "ambiental", BASE_ENV),
                ("soc", "social", BASE_SOC)]
    for dim, nombre, variables in catalogo:
        if dim not in hojas:
            continue
        for var in variables:
            if var.columna not in hojas[dim].columns:
                log.warning("Columna ausente en Datos_Base %s: %s (se omite)",
                            dim.upper(), var.columna)
                continue
            if var.columna == COLUMNA_ECO_CG:
                tabla = _bloque_base_eco_cg(n, hojas[dim])
            else:
                marcas = (imputados
                           if var.columna == "tarifa_usd_mwh" else None)
                tabla = _bloque_base(n, var, hojas[dim], marcas)
            tabla.update(seccion=f"Datos base ({nombre})",
                         codigo=var.columna, dim=dim)
            tablas.append(tabla)
            n += 1
    return tablas


def _tablas_indicadores(inicio: int, datos: dict,
                        imputados: dict) -> list[dict]:
    """Lista de tablas de indicadores, numeradas desde `inicio`."""
    tablas, n = [], inicio
    for codigo, ficha in FICHAS.items():
        if ficha.get("tipo") == "env6":
            if "ENV6" not in datos:
                continue
            tabla = _bloque_env6(n, ficha, datos)
            tabla.update(seccion=f"Indicadores ({NOMBRE_DIM[ficha['dim']]})",
                         codigo="ENV6", dim=ficha["dim"])
            tablas.append(tabla)
            n += 1
            continue
        for serie in _series_de(ficha, codigo):
            if serie["clave"] not in datos:
                log.warning("Sin datos, se omite la tabla: %s",
                            serie["clave"])
                continue
            marcas = imputados if serie["clave"] == "ECO14" else None
            tabla = _bloque_indicador(
                n, codigo, ficha, serie, datos[serie["clave"]], marcas)
            tabla.update(seccion=f"Indicadores ({NOMBRE_DIM[ficha['dim']]})",
                         codigo=serie["clave"], dim=ficha["dim"])
            tablas.append(tabla)
            n += 1
    return tablas


def _indice_html(tablas: list[dict]) -> list[str]:
    """Lista de tablas, útil para el índice de tablas del monográfico."""
    filas = []
    seccion_previa = None
    for t in tablas:
        if t["seccion"] != seccion_previa:
            filas.append(f'<tr><td colspan="2" style="{S_TD_IZQ}'
                         f'padding-top:10pt;"><b>{t["seccion"]}</b></td></tr>')
            seccion_previa = t["seccion"]
        filas.append(
            f'<tr><td style="{S_TD_IZQ}white-space:nowrap;">'
            f'<a href="#tabla-{t["numero"]:02d}" '
            f'style="color:inherit;">Tabla {t["numero"]}</a></td>'
            f'<td style="{S_TD_IZQ}">{t["titulo"]}</td></tr>')
    return [f'<h2 style="{S_H2}">Índice de tablas</h2>',
            f'<table style="{S_TABLA}"><tbody>'] + filas + ["</tbody></table>"]


def _referencias_html() -> list[str]:
    """Sección final con las referencias APA de las fuentes de datos."""
    sangria = ("margin:0 0 8pt 0;padding-left:36pt;text-indent:-36pt;"
               f"font-family:{S_SERIF};font-size:11pt;")
    bloque = [f'<h2 style="{S_H2}">Referencias de las fuentes de datos</h2>',
              f'<p style="{S_P}">Referencias en formato APA 7 de los '
              'conjuntos citados en las notas. Las matrices ENVs.xlsx y '
              'SOCs.xlsx se identifican como insumos del estudio.</p>']
    bloque += [f'<p style="{sangria}">{r}</p>' for r in REFERENCIAS_APA]
    return bloque


# ---------------------------------------------------------------------------
# CONVERSIÓN A .docx
# Word abre el HTML de forma nativa y lo convierte en tablas de Word
# reales (bordes por celda, Times New Roman, ancho ajustado al texto).
# Se automatiza con el propio Word por COM a través de PowerShell, para
# evitar dependencias adicionales de Python. En plataformas sin Word, el
# paso se omite y el HTML permanece disponible como formato de intercambio.
# ---------------------------------------------------------------------------
PS_A_DOCX = r"""
$ErrorActionPreference = 'Stop'
$app = New-Object -ComObject Word.Application
$app.Visible = $false
$app.DisplayAlerts = 0
try {
    $doc = $app.Documents.Open($env:APA_HTML, [ref]$false, [ref]$true)
    # 16 = wdFormatDocumentDefault (.docx)
    $doc.SaveAs([ref]$env:APA_DOCX, [ref]16)
    $tablas = $doc.Tables.Count
    $doc.Close()
    Write-Output $tablas
} finally {
    $app.Quit()
}
"""


def _exportar_docx(ruta_html: Path, ruta_docx: Path) -> bool:
    """Convierte el HTML a DOCX y devuelve el estado del paso opcional."""
    if sys.platform != "win32":
        log.info("Conversion a .docx omitida: requiere Microsoft Word en "
                 "Windows. El HTML se puede copiar y pegar igual.")
        return False
    # Word no sustituye de forma fiable un DOCX existente mediante SaveAs.
    # La conversión se hace a un temporal y solo se reemplaza la salida
    # anterior cuando Word terminó correctamente.
    ruta_temporal = ruta_docx.with_name(f"{ruta_docx.stem}_nuevo.docx")
    ruta_temporal.unlink(missing_ok=True)
    entorno = {**os.environ,
               "APA_HTML": str(ruta_html.resolve()),
               "APA_DOCX": str(ruta_temporal.resolve())}
    try:
        proceso = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             PS_A_DOCX],
            capture_output=True, text=True, timeout=300, env=entorno)
    except (OSError, subprocess.TimeoutExpired) as error:
        log.warning("No se pudo convertir a .docx (%s). Queda el HTML.",
                    error)
        return False
    if proceso.returncode != 0 or not ruta_temporal.exists():
        log.warning("No se pudo automatizar Word para convertir a .docx "
                    "en esta sesión. Queda el HTML, que Word abre con "
                    "Archivo > Abrir; el detalle está en el log DEBUG.")
        log.debug("PowerShell: %s", proceso.stderr.strip()[:500])
        return False
    try:
        ruta_temporal.replace(ruta_docx)
    except OSError as error:
        ruta_temporal.unlink(missing_ok=True)
        log.warning("Word generó el .docx, pero no se pudo reemplazar %s "
                    "(%s).", ruta_docx.name, error)
        return False
    tablas = proceso.stdout.strip().splitlines()
    log.info("Exportado: %s (%s tablas de Word, %.0f KB)", ruta_docx,
             tablas[-1] if tablas else "?", ruta_docx.stat().st_size / 1024)
    return True


def _armar_documento(tablas: list[dict], base: list[dict],
                     indicadores: list[dict], bloque: list[dict],
                     orden: str, con_notas: bool) -> list[str]:
    """Cuerpo HTML completo de una de las dos versiones del documento.

    Ambas comparten portada, índice y tablas; la versión sin notas omite
    la nota al pie de cada tabla y la sección de referencias, que solo
    tiene sentido acompañando a las notas que citan las fuentes.
    """
    plantilla_intro = INTRO if con_notas else INTRO_SIN_NOTAS
    encabezado = ("Tablas de la fase cuantitativa" if con_notas
                  else "Tablas de la fase cuantitativa (sin notas)")
    cuerpo = [f'<h1 style="{S_H1}">{encabezado}</h1>',
              f'<p style="{S_TITULO}">Evaluación del suministro de energía '
              'eléctrica en el SIEPAC: perspectivas económicas, sociales y '
              f'ambientales, {ANIOS[0]}–{ANIOS[-1]}</p>',
              plantilla_intro.format(
                  s_p=S_P, n=len(tablas), paises=", ".join(PAISES),
                  a0=ANIOS[0], a1=ANIOS[-1],
                  fecha=date.today().isoformat())]
    # La leyenda solo acompaña a la versión con notas: es a ella a la que
    # esas notas remiten. En la versión sin notas no tendría referente.
    if con_notas:
        cuerpo += _leyenda_convenciones()
    cuerpo += _indice_html(tablas)

    cierre_indicadores = (
        "ECO14 se resume mediante la mediana de países por falta de "
        "ponderador. SOC2 sí presenta agregado regional por razón de sumas "
        "a partir de gasto e ingreso aproximados." if con_notas
        else "ECO14 usa la mediana de países; SOC2 presenta agregado "
        "regional por razón de sumas.")
    secciones = {
        "base": _seccion(
            "Tablas de datos base",
            ["Variables de entrada del cálculo, tal como quedan en las hojas "
             "<i>Datos_Base</i> de los libros del pipeline. Las magnitudes "
             "energéticas se presentan en GWh (1 GWh = 10⁶ kWh) y las "
             "monetarias en millones de USD constantes de 2015, para que las "
             "cifras sean legibles en una tabla impresa; los libros conservan "
             "las unidades originales (kWh y USD). El costo de generación "
             "complementario se conserva en USD/MWh.",
             "Las variables comunes a varias dimensiones se presentan una "
             "sola vez. El PIB específico de la matriz ambiental conserva su "
             "serie de origen y se presenta por separado."]),
        "indicadores": _seccion(
            "Tablas de indicadores",
            ["Indicadores energéticos del desarrollo sostenible (IEDS, "
             "OIEA/NU, 2005) calculados sobre las variables base anteriores. "
             "Cada tabla cierra con dos resúmenes que responden preguntas "
             "distintas: el promedio de países describe al país típico del "
             "bloque y el agregado regional describe al SIEPAC como sistema. "
             "Al citar una cifra regional debe indicarse cuál de los dos se "
             "utiliza, porque pueden divergir incluso en el signo de la "
             "tendencia.",
             cierre_indicadores]),
        "bloque": _seccion(
            "Tablas de estadística descriptiva del bloque",
            ["Estadística descriptiva del SIEPAC como sistema, calculada "
             "sobre las tablas de indicadores anteriores. La dimensión "
             "económica conserva sus tres cortes de nivel y tendencia, "
             "heterogeneidad y convergencia sigma. La dimensión social "
             "añade un resumen compacto de tendencia regional para SOC1 y "
             "SOC3, heterogeneidad nacional para las cinco series SOC y "
             "una descripción anual completa de nivel, centro, dispersión "
             "y cambio para SOC2. SOC2 conserva la comparación nacional y "
             "añade la razón de sumas regional como medida del bloque. La "
             "dimensión ambiental incorpora nivel regional, dispersión y "
             "convergencia para ENV1–ENV3, además de una descripción de "
             "las dos series observadas de ENV6. ECO-CG se incorpora como "
             "serie económica complementaria y no como un noveno IEDS; "
             "sus medidas centrales son descriptivas y no forman un costo "
             "agregado del SIEPAC."]),
    }
    orden_secciones = ([("base", base), ("indicadores", indicadores)]
                       if orden == "base"
                       else [("indicadores", indicadores), ("base", base)])
    orden_secciones.append(("bloque", bloque))
    for clave, grupo in orden_secciones:
        cuerpo += secciones[clave]
        cuerpo += [tabla_apa(t, con_nota=con_notas) for t in grupo]
    if con_notas:
        cuerpo += _referencias_html()
    return cuerpo


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera las tablas de la fase cuantitativa en formato "
                    "APA 7, listas para pegar en Word.")
    parser.add_argument(
        "--orden", choices=["base", "indicadores"], default="base",
        help="Qué sección se numera primero (por defecto: base).")
    parser.add_argument(
        "--sin-docx", action="store_true",
        help="No generar el .docx (se genera si hay Word instalado).")
    args = parser.parse_args()

    log.info("Cargando indicadores y datos base del pipeline...")
    datos, imputados = _armar_datos()
    hojas = _leer_datos_base()

    # Se numeran primero las tablas de la seccion elegida para que la
    # numeracion del documento sea correlativa en el orden de lectura.
    if args.orden == "base":
        base = _tablas_base(1, hojas, imputados)
        indicadores = _tablas_indicadores(len(base) + 1, datos, imputados)
        tablas = base + indicadores
    else:
        indicadores = _tablas_indicadores(1, datos, imputados)
        base = _tablas_base(len(indicadores) + 1, hojas, imputados)
        tablas = indicadores + base

    # La estadística descriptiva del bloque cierra el documento en ambos
    # órdenes: se apoya en las tablas de indicadores, así que debe leerse
    # después de ellas.
    bloque_eco = _tablas_bloque(len(tablas) + 1, datos)
    bloque_soc = _tablas_sociales(len(tablas) + len(bloque_eco) + 1, datos)
    bloque_env = _tablas_ambientales(
        len(tablas) + len(bloque_eco) + len(bloque_soc) + 1, datos)
    bloque = bloque_eco + bloque_soc + bloque_env
    tablas += bloque

    for ruta, con_notas in [(RUTA_DOC, True), (RUTA_DOC_SIN_NOTAS, False)]:
        cuerpo = _armar_documento(tablas, base, indicadores, bloque,
                                  args.orden, con_notas)
        DIR_SALIDA.mkdir(parents=True, exist_ok=True)
        ruta.write_text(
            PLANTILLA.format(
                titulo=("Tablas APA - Fase cuantitativa SIEPAC" if con_notas
                        else "Tablas APA sin notas - Fase cuantitativa "
                             "SIEPAC"),
                cuerpo="\n".join(cuerpo)),
            encoding="utf-8")
        log.info("Exportado: %s (%d tablas%s, %.0f KB)", ruta, len(tablas),
                 "" if con_notas else ", sin notas",
                 ruta.stat().st_size / 1024)

    for t in tablas:
        t["archivo"] = ("tablas_apa_SIEPAC.html#tabla-"
                        f"{t['numero']:02d}")

    with open(RUTA_INDICE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["numero", "seccion", "dimension", "codigo", "titulo",
                    "archivo"])
        for t in tablas:
            w.writerow([t["numero"], t["seccion"], t["dim"], t["codigo"],
                        t["titulo"], t["archivo"]])
    log.info("Exportado: %s", RUTA_INDICE)
    _exportar_tabla_soc2_tesis(datos)
    if not args.sin_docx:
        _exportar_docx(RUTA_DOC, RUTA_DOCX)
        _exportar_docx(RUTA_DOC_SIN_NOTAS, RUTA_DOCX_SIN_NOTAS)


if __name__ == "__main__":
    main()
