"""
generar_tablas_apa.py — Tablas en formato APA 7.ª edición, listas para Word
====================================================
Etapa del pipeline : presentación de resultados (posterior a
                     generar_resumen_indicadores.py)
Entradas           : data/processed/indicadores_ECO_valores.csv y los libros
                     indicadores_ECO/ENV/SOC_SIEPAC.xlsx (hojas Datos_Base y
                     de indicadores), todo vía viz_comun
Salidas            : tablas-apa/tablas_apa_SIEPAC.docx (documento de Word con
                     todas las tablas), tablas_apa_SIEPAC.html (el mismo
                     documento en HTML), individuales/*.html (una tabla por
                     archivo) e indice_tablas.csv
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

Las tablas se arman en HTML y, si la máquina tiene Microsoft Word, el
script le pide al propio Word que convierta ese HTML en un .docx: el
resultado son tablas de Word nativas (bordes por celda, Times New Roman,
ancho ajustado al texto), listas para copiar al documento del monográfico
o para usarse tal cual como anexo. Sin Word, el HTML sirve igual copiando
y pegando desde el navegador.

Notas metodológicas:
  - Los valores NO se recalculan aquí: se leen de viz_comun, la misma
    fuente única que alimenta los visualizadores y el resumen en
    Markdown, de modo que las tablas del documento final no puedan
    divergir de las cifras del repositorio.
  - Cada tabla de indicador cierra con las dos filas de resumen del
    proyecto: promedio de países (media simple) y, cuando la serie tiene
    denominador disponible, agregado regional (razón de sumas).
  - Las tablas de datos base cierran con el total del bloque cuando la
    variable es una magnitud sumable (energía, población, PIB) y con el
    promedio de países cuando es una razón o un porcentaje, que no se
    puede sumar entre países.
  - Las referencias APA de las fuentes se declaran en FUENTES_APA y
    REFERENCIAS_APA (más abajo): es el único lugar del script que hay que
    tocar si cambia la forma de citar en el monográfico.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import argparse
import csv
import html
import logging
import math
import os
import re
import subprocess
import sys
import unicodedata
from collections import namedtuple
from datetime import date
from pathlib import Path

import pandas as pd

from config_siepac import RAIZ_PROYECTO
from viz_comun import (ANIOS, FICHAS, PAISES, RUTA_ENV, RUTA_EXCEL, RUTA_SOC,
                       agregados_eco, cargar_datos, leer_series_extra,
                       preparar_datos)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

DIR_SALIDA = RAIZ_PROYECTO / "tablas-apa"
DIR_INDIVIDUALES = DIR_SALIDA / "individuales"
RUTA_DOC = DIR_SALIDA / "tablas_apa_SIEPAC.html"
RUTA_DOCX = DIR_SALIDA / "tablas_apa_SIEPAC.docx"
RUTA_INDICE = DIR_SALIDA / "indice_tablas.csv"

NOMBRE_DIM = {"eco": "económica", "env": "ambiental", "soc": "social"}

# ---------------------------------------------------------------------------
# CITAS DE LAS FUENTES (formato APA 7.ª ed.)
# Claves cortas para la nota al pie de cada tabla; el texto completo de la
# referencia va en la sección final del documento. Ajustar aquí si el
# monográfico cita de otra forma.
# ---------------------------------------------------------------------------
FUENTES_APA = {
    "olade": "OLADE (2026)",
    "cepal": "CEPAL (2026)",
    "bm": "Banco Mundial (2026)",
    "ods": "CEPAL (2026) y UNIDO (2026)",
    "equipo": "el equipo de investigación",
}

REFERENCIAS_APA = [
    "Banco Mundial. (2026). <i>PIB (US$ a precios constantes de 2015)</i> "
    "[Conjunto de datos]. Indicadores del desarrollo mundial. "
    "https://datos.bancomundial.org/indicador/NY.GDP.MKTP.KD",
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
#   nota     : advertencia adicional para la nota al pie ("" si no hay)
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
    VarBase("vai_usd_const2015", "Valor agregado industrial",
            "millones de USD constantes de 2015", _MUSD, ",.0f", "pct",
            "suma", "ods",
            "Calculado en el ETL como participación del valor agregado "
            "industrial en el PIB multiplicada por el PIB real."),
    VarBase("vai_pct_pib",
            "Participación del valor agregado industrial en el PIB",
            "%", 1, ".2f", "pp", "media", "ods", ""),
    VarBase("tarifa_usd_mwh", "Precio medio de la electricidad regulada",
            "USD corrientes por MWh", 1, ".1f", "pct", "media", "cepal",
            "Los valores marcados con asterisco son imputaciones vía tasa "
            "de crecimiento anual compuesta (CAGR), no observaciones de la "
            "fuente."),
]

BASE_ENV = [
    VarBase("emisiones_gei_10e3t",
            "Emisiones de gases de efecto invernadero de las centrales "
            "eléctricas",
            "miles de toneladas de CO₂ equivalente", 1, ",.2f", "pct",
            "suma", "equipo", ""),
    VarBase("so2_10e3t",
            "Emisiones de dióxido de azufre de las centrales eléctricas",
            "miles de toneladas", 1, ",.3f", "pct", "suma", "equipo", ""),
    VarBase("nox_10e3t",
            "Emisiones de óxidos de nitrógeno de las centrales eléctricas",
            "miles de toneladas", 1, ",.4f", "pct", "suma", "equipo", ""),
    VarBase("co_10e3t",
            "Emisiones de monóxido de carbono de las centrales eléctricas",
            "miles de toneladas", 1, ",.3f", "pct", "suma", "equipo", ""),
    VarBase("particulas_10e3t",
            "Emisiones de material particulado de las centrales eléctricas",
            "miles de toneladas", 1, ",.4f", "pct", "suma", "equipo", ""),
    VarBase("pib_usd_const2015",
            "Producto interno bruto real empleado en la dimensión ambiental",
            "millones de USD constantes de 2015", 1, ",.1f", "pct", "suma",
            "equipo",
            "Serie del libro ambiental provisto por el equipo. Difiere "
            "entre −3.4 % y +7.8 % de la serie del Banco Mundial "
            "empleada en la dimensión económica; los indicadores ENV se "
            "calculan con esta serie y los ECO con aquella."),
]

BASE_SOC = [
    VarBase("pct_sin_electricidad", "Población sin acceso a electricidad",
            "%", 1, ".2f", "pp", "media", "equipo", ""),
    VarBase("tasa_electrificacion_rural", "Tasa de electrificación rural",
            "%", 1, ".2f", "pp", "media", "equipo", ""),
    VarBase("tasa_electrificacion_urbana", "Tasa de electrificación urbana",
            "%", 1, ".2f", "pp", "media", "equipo", ""),
    VarBase("pct_renovable_generacion",
            "Participación de las renovables en la generación eléctrica",
            "%", 1, ".2f", "pp", "media", "equipo",
            "Insumo del indicador SOC3; coincide con el indicador ECO13."),
]

# Variables de las hojas Datos_Base que no reciben tabla propia por ser
# idénticas (hasta el redondeo) a una ya presentada en la dimensión
# económica; se advierte en la introducción de cada sección.
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


def _slug(texto: str) -> str:
    """Nombre de archivo sin tildes ni signos, para los HTML sueltos."""
    plano = (unicodedata.normalize("NFKD", texto)
             .encode("ascii", "ignore").decode("ascii").lower())
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", plano)).strip("-")


# ---------------------------------------------------------------------------
# CONSTRUCCIÓN DE UNA TABLA APA
# ---------------------------------------------------------------------------

def _celda(contenido: str, estilo: str, etiqueta: str = "td") -> str:
    return f'<{etiqueta} style="{estilo}">{contenido}</{etiqueta}>'


def tabla_apa(numero: int, titulo: str, encabezados: list[str],
              filas: list[list[str]], resumen: list[list[str]],
              nota: str, cols_izq: int = 1) -> str:
    """Devuelve el bloque HTML de una tabla con formato APA 7.

    numero/titulo van encima (número en negrita, título en cursiva);
    la nota, debajo. `filas` son los países y `resumen` las filas de
    cierre (promedio, agregado o total), que se separan con una línea
    horizontal. `cols_izq` es cuántas columnas iniciales se alinean a la
    izquierda (1 = País; 2 = País y Serie, como en ENV6).
    """
    partes = [f'<div style="{S_BLOQUE}">',
              f'<p style="{S_NUMERO}">Tabla {numero}</p>',
              f'<p style="{S_TITULO}">{titulo}</p>',
              f'<table style="{S_TABLA}"><thead><tr>']
    for i, enc in enumerate(encabezados):
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
    partes.append(f'<p style="{S_NOTA}"><i>Nota.</i> {nota}</p>')
    partes.append("</div>")
    return "\n".join(partes)


# ---------------------------------------------------------------------------
# TABLAS DE DATOS BASE
# ---------------------------------------------------------------------------

def _leer_datos_base() -> dict[str, pd.DataFrame]:
    """Hojas Datos_Base de los tres libros. La económica trae el
    encabezado en la primera fila; las de ENV/SOC llevan dos líneas de
    presentación antes (mismo criterio que viz_comun.leer_series_extra)."""
    hojas = {"eco": pd.read_excel(RUTA_EXCEL, sheet_name="Datos_Base")}
    for dim, ruta in [("env", RUTA_ENV), ("soc", RUTA_SOC)]:
        if not ruta.exists():
            log.warning("No encontrado: %s - se omiten las tablas de datos "
                        "base de esa dimension.", ruta.name)
            continue
        hojas[dim] = pd.read_excel(ruta, sheet_name="Datos_Base", skiprows=2)
    return hojas


def _bloque_base(numero: int, var: VarBase, base: pd.DataFrame,
                 imputados: dict | None) -> tuple[str, str]:
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

    # Fila de cierre: total del bloque si la magnitud es sumable, media
    # simple si es una razón o un porcentaje (que no se pueden sumar).
    agregada = []
    for i in range(len(ANIOS)):
        vals = [series_pais[p][i] for p in PAISES if series_pais[p][i] is not None]
        if not vals:
            agregada.append(None)
        elif var.resumen == "suma":
            agregada.append(sum(vals))
        else:
            agregada.append(sum(vals) / len(vals))
    etiqueta = ("Total SIEPAC" if var.resumen == "suma"
                else "Promedio de países (media simple)")
    resumen = [[etiqueta] + [_fmt(v, var.formato) for v in agregada] +
               [_delta(agregada[0], agregada[-1], var.delta)]]

    titulo = f"{var.etiqueta} por país, {ANIOS[0]}–{ANIOS[-1]}"
    nota = (f"Valores en {var.unidad}. "
            f"Δ = variación {ANIOS[0]}–{ANIOS[-1]}"
            + (" en puntos porcentuales." if var.delta == "pp"
               else ", relativa.") + " ")
    nota += ("La última fila es la suma de los seis países."
             if var.resumen == "suma"
             else "La última fila es la media simple de los seis países.")
    if var.nota:
        nota += " " + var.nota
    fuente = FUENTES_APA[var.fuente]
    nota += (f" Elaboración propia con datos de {fuente}."
             if var.fuente != "equipo"
             else f" Serie recopilada por {fuente}.")

    encabezados = (["País"] + [str(a) for a in ANIOS] +
                   [f"Δ {ANIOS[0]}–{ANIOS[-1]}"])
    return tabla_apa(numero, titulo, encabezados, filas, resumen, nota), titulo


# ---------------------------------------------------------------------------
# TABLAS DE INDICADORES
# ---------------------------------------------------------------------------

def _armar_datos() -> tuple[dict, dict]:
    """Mismo empaquetado que generar_resumen_indicadores._armar_datos:
    {clave_serie: {paises, promedio, agregado}} + banderas de imputación
    de ECO14. Se reutiliza para que las tablas del documento final y las
    del resumen en Markdown no puedan divergir."""
    hojas = cargar_datos()
    df = preparar_datos(hojas)
    agregados = agregados_eco(hojas["datos_base"])
    datos = {}
    for codigo in [c for c, f in FICHAS.items() if f["dim"] == "eco"]:
        por_pais = {}
        for pais in PAISES:
            serie = (df[df["pais"] == pais].sort_values("anio")[codigo]
                     .round(6).tolist())
            por_pais[pais] = [None if _es_nulo(v) else v for v in serie]
        promedio = [None if math.isnan(v) else v
                    for v in df.groupby("anio")[codigo].mean().sort_index()
                    .round(6).tolist()]
        datos[codigo] = {"paises": por_pais, "promedio": promedio,
                         "agregado": agregados.get(codigo)}
    datos.update(leer_series_extra())
    imputados = {
        pais: df[df["pais"] == pais].sort_values("anio")["tarifa_imputada"]
              .tolist()
        for pais in PAISES
    }
    return datos, imputados


def _series_de(ficha: dict, codigo: str) -> list[dict]:
    """Sub-series de una ficha (las ECO tienen una sola salida)."""
    if not ficha.get("series"):
        return [dict(clave=codigo, etiqueta="", formato=ficha["formato"],
                     unidad=ficha["unidad"], formula=ficha["formula"])]
    return [dict(clave=s[0], etiqueta=s[1], formato=s[2], unidad=s[4],
                 formula=s[5]) for s in ficha["series"]]


def _fuente_indicador(codigo: str, dim: str) -> str:
    """Frase de atribución para la nota al pie del indicador."""
    if dim != "eco":
        return ("Elaboración propia a partir de las series recopiladas por "
                "el equipo de investigación.")
    claves = FUENTE_INDICADOR.get(codigo, "olade").split("+")
    citas = [FUENTES_APA[c] for c in claves]
    unidas = (citas[0] if len(citas) == 1
              else " y ".join([", ".join(citas[:-1]), citas[-1]]))
    return f"Elaboración propia con datos de {unidas}."


def _bloque_indicador(numero: int, codigo: str, ficha: dict, serie: dict,
                      bloque: dict, imputados: dict | None) -> tuple[str, str]:
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

    nota = (f"Valores en {serie['unidad']}. Fórmula: {serie['formula']}. "
            f"Δ = variación {ANIOS[0]}–{ANIOS[-1]}"
            + (" en puntos porcentuales. " if ficha["delta"] == "pp"
               else ", relativa. "))
    nota += ("El promedio de países es la media simple de los seis valores "
             "nacionales (peso 1/6 por país). ")
    if agr:
        nota += ("El agregado regional es la razón de sumas "
                 "(Σ numerador ÷ Σ denominador), equivalente "
                 "a ponderar cada país por su denominador; es el valor que "
                 "corresponde citar cuando el texto se refiere al bloque "
                 "como sistema. ")
    if ficha["nota"]:
        nota += ficha["nota"] + " "
    nota += _fuente_indicador(codigo, ficha["dim"])
    if imputados:
        nota += (" El asterisco marca valores imputados vía CAGR, no "
                 "observaciones directas de la fuente.")

    encabezados = (["País"] + [str(a) for a in ANIOS] +
                   [f"Δ {ANIOS[0]}–{ANIOS[-1]}"])
    return tabla_apa(numero, titulo, encabezados, filas, resumen,
                     nota), titulo


def _bloque_env6(numero: int, ficha: dict, datos: dict) -> tuple[str, str]:
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
            "Elaboración propia a partir de las series recopiladas por el "
            "equipo de investigación.")
    encabezados = ["País", "Serie"] + [str(a) for a in ANIOS]
    return tabla_apa(numero, titulo, encabezados, filas, [], nota,
                     cols_izq=2), titulo


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
estructura, los bordes y la cursiva. Si prefiere pegar una sola tabla,
cada una tiene además su propio archivo en la carpeta
<i>individuales/</i>. La numeración es correlativa dentro de este
documento; si en el monográfico las tablas aparecen intercaladas con
otras, renumérelas según su orden final de aparición.</p>
<p style="{s_p}">Cobertura: {paises}, ventana {a0}–{a1}.
«s.d.» indica que no hay dato para esa celda. Documento generado
automáticamente por <i>src/generar_tablas_apa.py</i> el {fecha}; los
valores provienen del mismo pipeline que alimenta los visualizadores y el
resumen metodológico del proyecto.</p>
"""


def _seccion(titulo: str, parrafos: list[str]) -> list[str]:
    bloque = [f'<h2 style="{S_H2}">{titulo}</h2>']
    bloque += [f'<p style="{S_P}">{p}</p>' for p in parrafos]
    return bloque


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
            marcas = imputados if var.columna == "tarifa_usd_mwh" else None
            cuerpo, titulo = _bloque_base(n, var, hojas[dim], marcas)
            tablas.append(dict(numero=n, seccion=f"Datos base ({nombre})",
                               codigo=var.columna, titulo=titulo,
                               html=cuerpo, dim=dim))
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
            cuerpo, titulo = _bloque_env6(n, ficha, datos)
            tablas.append(dict(numero=n,
                               seccion=f"Indicadores ({NOMBRE_DIM[ficha['dim']]})",
                               codigo="ENV6", titulo=titulo, html=cuerpo,
                               dim=ficha["dim"]))
            n += 1
            continue
        for serie in _series_de(ficha, codigo):
            if serie["clave"] not in datos:
                log.warning("Sin datos, se omite la tabla: %s",
                            serie["clave"])
                continue
            marcas = imputados if serie["clave"] == "ECO14" else None
            cuerpo, titulo = _bloque_indicador(
                n, codigo, ficha, serie, datos[serie["clave"]], marcas)
            tablas.append(dict(numero=n,
                               seccion=f"Indicadores ({NOMBRE_DIM[ficha['dim']]})",
                               codigo=serie["clave"], titulo=titulo,
                               html=cuerpo, dim=ficha["dim"]))
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
            f'<tr><td style="{S_TD_IZQ}white-space:nowrap;">Tabla '
            f'{t["numero"]}</td><td style="{S_TD_IZQ}">{t["titulo"]}</td></tr>')
    return [f'<h2 style="{S_H2}">Índice de tablas</h2>',
            f'<table style="{S_TABLA}"><tbody>'] + filas + ["</tbody></table>"]


def _referencias_html() -> list[str]:
    """Sección final con las referencias APA de las fuentes de datos."""
    sangria = ("margin:0 0 8pt 0;padding-left:36pt;text-indent:-36pt;"
               f"font-family:{S_SERIF};font-size:11pt;")
    bloque = [f'<h2 style="{S_H2}">Referencias de las fuentes de datos</h2>',
              f'<p style="{S_P}">Referencias en formato APA 7 de los '
              'conjuntos de datos citados en las notas de las tablas. Las '
              'series de las dimensiones ambiental y social fueron '
              'recopiladas por el equipo de investigación a partir de los '
              'informes del Ente Operador Regional y de los inventarios '
              'nacionales; verifique la referencia exacta con el equipo '
              'antes de incluirla en el monográfico.</p>']
    bloque += [f'<p style="{sangria}">{r}</p>' for r in REFERENCIAS_APA]
    return bloque


# ---------------------------------------------------------------------------
# CONVERSIÓN A .docx
# Word abre el HTML de forma nativa y lo convierte en tablas de Word
# reales (bordes por celda, Times New Roman, ancho ajustado al texto).
# Se automatiza con el propio Word por COM a través de PowerShell, para
# no añadir dependencias de Python al pipeline. Si el equipo no tiene
# Word (u otro sistema operativo), el paso se omite con aviso: el HTML
# sigue siendo utilizable copiando y pegando.
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
    """Convierte el documento HTML a .docx con Microsoft Word. Devuelve
    True si lo logró; nunca lanza excepción (es un paso opcional que no
    debe tumbar el pipeline)."""
    if sys.platform != "win32":
        log.info("Conversion a .docx omitida: requiere Microsoft Word en "
                 "Windows. El HTML se puede copiar y pegar igual.")
        return False
    entorno = {**os.environ,
               "APA_HTML": str(ruta_html.resolve()),
               "APA_DOCX": str(ruta_docx.resolve())}
    try:
        proceso = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             PS_A_DOCX],
            capture_output=True, text=True, timeout=300, env=entorno)
    except (OSError, subprocess.TimeoutExpired) as error:
        log.warning("No se pudo convertir a .docx (%s). Queda el HTML.",
                    error)
        return False
    if proceso.returncode != 0 or not ruta_docx.exists():
        log.warning("No se pudo convertir a .docx; probablemente Word no "
                    "este instalado. Queda el HTML, que Word abre igual "
                    "con Archivo > Abrir.")
        log.debug("PowerShell: %s", proceso.stderr.strip()[:500])
        return False
    tablas = proceso.stdout.strip().splitlines()
    log.info("Exportado: %s (%s tablas de Word, %.0f KB)", ruta_docx,
             tablas[-1] if tablas else "?", ruta_docx.stat().st_size / 1024)
    return True


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

    cuerpo = [f'<h1 style="{S_H1}">Tablas de la fase cuantitativa</h1>',
              f'<p style="{S_TITULO}">Evaluación del suministro de energía '
              'eléctrica en el SIEPAC: perspectivas económicas, sociales y '
              f'ambientales, {ANIOS[0]}–{ANIOS[-1]}</p>',
              INTRO.format(s_p=S_P, n=len(tablas), paises=", ".join(PAISES),
                           a0=ANIOS[0], a1=ANIOS[-1],
                           fecha=date.today().isoformat())]
    cuerpo += _indice_html(tablas)

    secciones = {
        "base": _seccion(
            "Tablas de datos base",
            ["Variables de entrada del cálculo, tal como quedan en las hojas "
             "<i>Datos_Base</i> de los libros del pipeline. Las magnitudes "
             "energéticas se presentan en GWh (1 GWh = 10⁶ kWh) y las "
             "monetarias en millones de USD constantes de 2015, para que las "
             "cifras sean legibles en una tabla impresa; los libros conservan "
             "las unidades originales (kWh y USD).",
             "Las hojas ambiental y social repiten población y producción "
             "bruta con los mismos valores de la dimensión económica, por lo "
             "que no se duplican aquí; el PIB del libro ambiental sí difiere "
             "y se presenta aparte."]),
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
             "Las series sin denominador disponible en el repositorio "
             "(ECO14, SOC2 y SOC3) presentan únicamente el promedio de "
             "países, y así lo advierte su nota."]),
    }
    orden_secciones = ([("base", base), ("indicadores", indicadores)]
                       if args.orden == "base"
                       else [("indicadores", indicadores), ("base", base)])
    for clave, grupo in orden_secciones:
        cuerpo += secciones[clave]
        cuerpo += [t["html"] for t in grupo]
    cuerpo += _referencias_html()

    DIR_SALIDA.mkdir(exist_ok=True)
    DIR_INDIVIDUALES.mkdir(exist_ok=True)

    RUTA_DOC.write_text(
        PLANTILLA.format(titulo="Tablas APA - Fase cuantitativa SIEPAC",
                         cuerpo="\n".join(cuerpo)),
        encoding="utf-8")
    log.info("Exportado: %s (%d tablas, %.0f KB)", RUTA_DOC, len(tablas),
             RUTA_DOC.stat().st_size / 1024)

    # Se limpian las tablas sueltas de corridas anteriores: al cambiar
    # --orden cambia el numero de cada tabla y quedarian archivos viejos
    # con numeracion contradictoria mezclados con los nuevos.
    for viejo in DIR_INDIVIDUALES.glob("Tabla_*.html"):
        viejo.unlink()

    for t in tablas:
        nombre = f"Tabla_{t['numero']:02d}_{_slug(t['codigo'])}.html"
        (DIR_INDIVIDUALES / nombre).write_text(
            PLANTILLA.format(titulo=html.escape(f"Tabla {t['numero']}"),
                             cuerpo=t["html"]),
            encoding="utf-8")
        t["archivo"] = f"individuales/{nombre}"
    log.info("Exportadas %d tablas sueltas en: %s", len(tablas),
             DIR_INDIVIDUALES)

    with open(RUTA_INDICE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["numero", "seccion", "dimension", "codigo", "titulo",
                    "archivo"])
        for t in tablas:
            w.writerow([t["numero"], t["seccion"], t["dim"], t["codigo"],
                        t["titulo"], t["archivo"]])
    log.info("Exportado: %s", RUTA_INDICE)

    if not args.sin_docx:
        _exportar_docx(RUTA_DOC, RUTA_DOCX)


if __name__ == "__main__":
    main()
