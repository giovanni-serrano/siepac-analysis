"""
figuras_comun.py — Estética común de las figuras regionales de tesis
====================================================
Etapa del pipeline : visualización (módulo compartido)
Entradas           : series país-año y medida principal ya calculada
Salidas            : objetos Plotly listos para exportar
Alimenta           : generar_figuras_tesis.py
Fuente de datos    : salidas normalizadas del pipeline

La banda mínimo–máximo describe la heterogeneidad de los seis países; la
línea discontinua representa la media simple y la continua, la medida que
corresponde al bloque (razón de sumas o mediana, según el indicador).

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

from collections.abc import Sequence

import pandas as pd
import plotly.graph_objects as go

from config_siepac import ANIOS_ANALISIS as ANIOS

AZUL = "#1F4E79"
NARANJA = "#FF7F0E"
GRIS_LINEA = "#8A8A8A"
GRIS_GRILLA = "#EBEBEB"
TINTA = "#1A1A1A"
BANDA = "rgba(138,138,138,0.18)"
BANDA_PROXY = "rgba(31,119,180,0.14)"
FUENTE = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
ANCHO, ALTO, ESCALA = 1000, 620, 3


def crear_figura_bloque(
        codigo: str,
        nombre: str,
        unidad: str,
        sufijo: str,
        valores_pais: pd.DataFrame,
        principal: Sequence[float],
        etiqueta_principal: str,
        promedio: Sequence[float] | None = None,
        color_principal: str = AZUL,
        color_banda: str = BANDA,
        subtitulo: str | None = None,
        permite_negativos: bool = False,
        franja_imputada: bool = False,
        etiqueta_promedio: str = "Promedio de países (media simple)",
        etiqueta_banda: str = "Banda mín–máx de los seis países",
        ) -> go.Figure:
    """Construye la figura canónica del bloque SIEPAC."""
    piv = valores_pais.reindex(index=ANIOS)
    prom = list(promedio) if promedio is not None else piv.mean(axis=1)

    fig = go.Figure()
    fig.add_scatter(x=ANIOS, y=piv.max(axis=1), mode="lines",
                    line=dict(width=0), showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=ANIOS, y=piv.min(axis=1), mode="lines",
                    line=dict(width=0), fill="tonexty",
                    fillcolor=color_banda, name=etiqueta_banda)
    fig.add_scatter(x=ANIOS, y=prom, mode="lines+markers",
                    name=etiqueta_promedio,
                    line=dict(color=GRIS_LINEA, width=2, dash="dash"),
                    marker=dict(size=7, color=GRIS_LINEA))
    fig.add_scatter(x=ANIOS, y=list(principal), mode="lines+markers",
                    name=etiqueta_principal,
                    line=dict(color=color_principal, width=3.4),
                    marker=dict(size=9, color=color_principal))

    if franja_imputada:
        fig.add_vrect(x0=2022.5, x1=ANIOS[-1] + 0.15,
                      fillcolor="rgba(0,0,0,0.05)", line_width=0)
        fig.add_annotation(x=2023.5, y=1.02, yref="paper",
                           text="imputado (CAGR)", showarrow=False,
                           font=dict(size=12, color="#5B5B5B"))

    rango_y = (dict(zerolinecolor=GRIS_LINEA, zerolinewidth=1.4)
               if permite_negativos else dict(rangemode="tozero"))
    subtitulo = subtitulo or (
        f"{unidad} · bloque SIEPAC con banda mín–máx entre países")
    fig.update_layout(
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family=FUENTE, size=15, color=TINTA),
        title=dict(
            text=f"<b>{codigo} — {nombre}</b><br>"
                 f"<sup style='color:#5B5B5B'>{subtitulo}</sup>",
            x=0.02, xanchor="left", font=dict(size=21)),
        legend=dict(orientation="h", y=-0.14, x=0.5, xanchor="center"),
        margin=dict(l=70, r=110, t=86, b=76),
        xaxis=dict(tickvals=ANIOS, gridcolor="#F5F5F5", automargin=True),
        yaxis=dict(gridcolor=GRIS_GRILLA, ticksuffix=sufijo,
                   automargin=True, **rango_y),
    )
    return fig
