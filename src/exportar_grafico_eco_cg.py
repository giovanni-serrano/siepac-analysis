"""
exportar_grafico_eco_cg.py — Figura del costo de generación del bloque
====================================================
Etapa del pipeline : exportación de resultados económicos a PNG
Entradas           : data/processed/eco_cg_siepac.csv
Salidas            : analisis-eco/salidas/figuras/ECO_CG_bloque.png y
                     analisis-eco/salidas/figuras_alt/ECO_CG_bloque.png
Alimenta           : capítulo cuantitativo de la dimensión económica
Fuente de datos    : CNEE/AMM, CREE, SIGET/UT, CNDC/INE, DOCSE/ICE y ASEP

La línea principal es la mediana descriptiva de los seis proxies nacionales.
También se muestran la media simple y la banda mínimo–máximo. Ninguna de
estas medidas se interpreta como costo agregado regional, porque los
instrumentos nacionales no son conceptualmente homólogos.

Uso:  python src/exportar_grafico_eco_cg.py   (desde la raíz del proyecto)

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from config_siepac import ANIOS_ANALISIS, RAIZ_PROYECTO
from eco_cg_comun import (CODIGO_ECO_CG, ETIQUETA_ECO_CG, FICHA_ECO_CG,
                          cargar_eco_cg, serie_mediana_eco_cg)


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

ANIOS = list(ANIOS_ANALISIS)
DIRECTORIOS_SALIDA = [
    RAIZ_PROYECTO / "analisis-eco" / "salidas" / "figuras",
    RAIZ_PROYECTO / "analisis-eco" / "salidas" / "figuras_alt",
]

AZUL = "#1F77B4"
NARANJA = "#FF7F0E"
GRIS_GRILLA = "#EBEBEB"
TINTA = "#1A1A1A"
BANDA = "rgba(31,119,180,0.14)"
FUENTE = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
ANCHO, ALTO, ESCALA = 1000, 620, 3


def construir_figura(eco_cg: pd.DataFrame) -> go.Figure:
    """Construye la figura con la estética del análisis económico."""
    pivote = (eco_cg.pivot(index="anio", columns="pais",
                           values=CODIGO_ECO_CG).reindex(ANIOS))
    promedio = pivote.mean(axis=1)
    mediana = serie_mediana_eco_cg(eco_cg)
    ficha = FICHA_ECO_CG

    fig = go.Figure()
    fig.add_scatter(
        x=ANIOS, y=pivote.max(axis=1), mode="lines",
        line=dict(width=0), showlegend=False, hoverinfo="skip")
    fig.add_scatter(
        x=ANIOS, y=pivote.min(axis=1), mode="lines",
        line=dict(width=0), fill="tonexty", fillcolor=BANDA,
        name="Mínimo–máximo entre países")
    fig.add_scatter(
        x=ANIOS, y=promedio, mode="lines+markers",
        name="Promedio simple de países",
        line=dict(color=AZUL, width=2.4, dash="dash"),
        marker=dict(size=7, color=AZUL))
    fig.add_scatter(
        x=ANIOS, y=mediana, mode="lines+markers",
        name="Mediana de proxies nacionales",
        line=dict(color=NARANJA, width=3.4),
        marker=dict(size=9, color=NARANJA))

    fig.update_layout(
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family=FUENTE, size=15, color=TINTA),
        title=dict(
            text=(f"<b>{ETIQUETA_ECO_CG} — {ficha['nombre']}</b><br>"
                  f"<sup style='color:#5B5B5B'>{ficha['unidad']} · "
                  "comparación descriptiva de proxies nacionales</sup>"),
            x=0.02, xanchor="left", font=dict(size=21)),
        legend=dict(orientation="h", y=-0.14, x=0.5, xanchor="center"),
        margin=dict(l=70, r=110, t=86, b=76),
        xaxis=dict(tickvals=ANIOS, gridcolor="#F5F5F5", automargin=True),
        yaxis=dict(gridcolor=GRIS_GRILLA, ticksuffix=ficha["sufijo"],
                   rangemode="tozero", automargin=True),
    )
    return fig


def main() -> None:
    eco_cg = cargar_eco_cg()
    figura = construir_figura(eco_cg)

    for directorio in DIRECTORIOS_SALIDA:
        directorio.mkdir(parents=True, exist_ok=True)
        ruta = directorio / f"{CODIGO_ECO_CG}_bloque.png"
        pio.write_image(
            figura, ruta, width=ANCHO, height=ALTO, scale=ESCALA)
        log.info("OK  %s", ruta.relative_to(RAIZ_PROYECTO))


if __name__ == "__main__":
    main()
