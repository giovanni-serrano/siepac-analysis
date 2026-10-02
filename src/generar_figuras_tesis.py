"""
generar_figuras_tesis.py — Figuras oficiales de la fase cuantitativa
====================================================
Etapa del pipeline : presentación de resultados
Entradas           : resultados estructurados y CSV normalizados en data/processed/ y
                     data/raw_equipo/eco_cg_siepac.csv
Salidas            : salidas/tesis/figuras/*.png
Alimenta           : documento final de la monografía
Fuente de datos    : salidas del pipeline; fichas en metadatos_indicadores.FICHAS

Genera las 22 figuras oficiales: 9 económicas, 5 sociales y 8 ambientales.
Todas usan el mismo lenguaje visual; ENV6 conserva un
tratamiento especial porque contrasta dos magnitudes observadas en GWh.

Uso:  python src/generar_figuras_tesis.py   (desde la raíz)

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from config_siepac import (ANIOS_ANALISIS as ANIOS, DIR_SALIDAS_TESIS,
                           PAISES_SIEPAC as PAISES)
from eco_cg_comun import (CODIGO_ECO_CG, ETIQUETA_ECO_CG, FICHA_ECO_CG,
                          cargar_eco_cg, serie_mediana_eco_cg)
from figuras_comun import (ALTO, ANCHO, AZUL, BANDA, BANDA_PROXY, ESCALA,
                           FUENTE, GRIS_GRILLA, GRIS_LINEA, NARANJA, TINTA,
                           crear_figura_bloque)
from presentacion_indicadores import (FICHAS)
from calculos_indicadores import (agregados_eco)
from resultados_indicadores import (cargar_datos, leer_series_extra, preparar_datos)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

DIR_FIGURAS = DIR_SALIDAS_TESIS / "figuras"

from metadatos_indicadores import CODIGOS_ECO as ECO, SERIES_SOC as SOC, SERIES_ENV as ENV


def _catalogo_series() -> dict[str, dict]:
    catalogo = {}
    for codigo, ficha in FICHAS.items():
        for serie in ficha.get("series", []):
            catalogo[serie[0]] = {
                "codigo": serie[0],
                "nombre": ficha["nombre"] +
                          (f" — {serie[1]}" if serie[1] else ""),
                "unidad": serie[4], "sufijo": serie[3],
                "dimension": ficha["dim"],
            }
    return catalogo


def _exportar(fig: go.Figure, nombre: str) -> Path:
    ruta = DIR_FIGURAS / nombre
    pio.write_image(fig, ruta, width=ANCHO, height=ALTO, scale=ESCALA)
    log.info("OK  %s", ruta.relative_to(DIR_SALIDAS_TESIS.parent.parent))
    return ruta


def _figura_env6(extra: dict) -> go.Figure:
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("Inyección de biomasa",
                                        "Saldo neto en el MER"))
    colores = {"biomasa": AZUL, "saldo": "#4A4A4A"}
    etiquetas = {"biomasa": "Total del bloque",
                 "saldo": "Saldo agregado del bloque"}
    for col, clave in enumerate(("biomasa", "saldo"), start=1):
        piv = pd.DataFrame(
            {pais: extra["ENV6"][pais][clave] for pais in PAISES},
            index=ANIOS)
        fig.add_scatter(x=ANIOS, y=piv.max(axis=1), mode="lines",
                        line=dict(width=0), showlegend=False,
                        hoverinfo="skip", row=1, col=col)
        fig.add_scatter(x=ANIOS, y=piv.min(axis=1), mode="lines",
                        line=dict(width=0), fill="tonexty",
                        fillcolor=BANDA,
                        name="Banda mín–máx entre países",
                        showlegend=col == 1, row=1, col=col)
        fig.add_scatter(x=ANIOS, y=piv.sum(axis=1), mode="lines+markers",
                        name=etiquetas[clave], showlegend=True,
                        line=dict(color=colores[clave], width=3.4),
                        marker=dict(size=9, color=colores[clave]),
                        row=1, col=col)
    fig.update_layout(
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family=FUENTE, size=15, color=TINTA),
        title=dict(
            text="<b>ENV6 — Biomasa y balance del mercado regional</b><br>"
                 "<sup style='color:#5B5B5B'>GWh · comparación de dos "
                 "magnitudes observadas; no constituye un cociente</sup>",
            x=0.02, xanchor="left", font=dict(size=21)),
        legend=dict(orientation="h", y=-0.16, x=0.5, xanchor="center"),
        margin=dict(l=70, r=70, t=100, b=82),
    )
    fig.update_xaxes(tickvals=ANIOS, gridcolor="#F5F5F5")
    fig.update_yaxes(gridcolor=GRIS_GRILLA, ticksuffix=" GWh",
                     zerolinecolor=GRIS_LINEA, automargin=True)
    return fig


def main() -> None:
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    generadas = []

    hojas = cargar_datos()
    eco_df = preparar_datos(hojas)
    agregados = agregados_eco(hojas["datos_base"])
    for codigo in ECO:
        ficha = FICHAS[codigo]
        piv = (eco_df.pivot(index="anio", columns="pais", values=codigo)
               .reindex(index=ANIOS, columns=PAISES))
        if codigo == "ECO14":
            principal = piv.median(axis=1)
            etiqueta = "Mediana de países (sin ponderador)"
        else:
            principal = agregados[codigo]
            etiqueta = "Agregado regional (razón de sumas)"
        fig = crear_figura_bloque(
            codigo, ficha["nombre"], ficha["unidad"], ficha["sufijo"],
            piv, principal, etiqueta, permite_negativos=codigo == "ECO15",
            franja_imputada=codigo == "ECO14")
        nombre = f"{codigo}_bloque.png"
        _exportar(fig, nombre)
        generadas.append(nombre)

    eco_cg = cargar_eco_cg()
    piv_cg = (eco_cg.pivot(index="anio", columns="pais",
                           values=CODIGO_ECO_CG)
              .reindex(index=ANIOS, columns=PAISES))
    fig = crear_figura_bloque(
        ETIQUETA_ECO_CG, FICHA_ECO_CG["nombre"], FICHA_ECO_CG["unidad"],
        FICHA_ECO_CG["sufijo"], piv_cg, serie_mediana_eco_cg(eco_cg),
        "Mediana de proxies nacionales", color_principal=NARANJA,
        color_banda=BANDA_PROXY,
        subtitulo=(f"{FICHA_ECO_CG['unidad']} · comparación descriptiva "
                    "de proxies nacionales"),
        etiqueta_promedio="Promedio simple de países",
        etiqueta_banda="Mínimo–máximo entre países")
    nombre = f"{CODIGO_ECO_CG}_bloque.png"
    _exportar(fig, nombre)
    generadas.append(nombre)

    extra = leer_series_extra()
    catalogo = _catalogo_series()
    for codigo in SOC + ENV:
        info = catalogo[codigo]
        bloque = extra[codigo]
        if not bloque.get("agregado"):
            raise ValueError(f"VALIDACIÓN FALLIDA: {codigo} sin agregado")
        piv = pd.DataFrame(bloque["paises"], index=ANIOS)
        fig = crear_figura_bloque(
            codigo, info["nombre"], info["unidad"], info["sufijo"], piv,
            bloque["agregado"], "Agregado regional (razón de sumas)",
            promedio=bloque["promedio"])
        nombre = f"{codigo}_bloque.png"
        _exportar(fig, nombre)
        generadas.append(nombre)

    nombre = "ENV6_bloque.png"
    _exportar(_figura_env6(extra), nombre)
    generadas.append(nombre)

    if len(generadas) != 22:
        raise ValueError(f"VALIDACIÓN FALLIDA: se esperaban 22 figuras; "
                         f"se generaron {len(generadas)}")
    log.info("Listo: 22 figuras oficiales en %s", DIR_FIGURAS)


if __name__ == "__main__":
    main()
