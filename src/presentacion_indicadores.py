"""
presentacion_indicadores.py — Formato de fichas para productos
====================================================
Etapa del pipeline : metadatos compartidos (módulo importable)
Entradas           : definiciones metodológicas documentadas del proyecto
Salidas            : FICHAS con el contrato histórico de presentación
Alimenta           : libros, resumen, tablas, figuras y visualizador
Fuente de datos    : fichas IEDS y decisiones de la tesis
Uso                : importar los catálogos
Notas metodológicas: conserva literalmente los textos publicados; las variantes
                     editoriales de Excel no redefinen las fórmulas científicas.
Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

from copy import deepcopy
from metadatos_indicadores import FICHAS as FICHAS_CIENTIFICAS

PRESENTACION = {'ECO1': {'formato': ',.0f', 'sufijo': ' kWh/hab', 'modos': ['serie', 'barras'], 'nota_figura': ''},
 'ECO2': {'formato': '.4f', 'sufijo': '', 'modos': ['serie', 'barras'], 'nota_figura': ''},
 'ECO3': {'formato': '.1f',
          'sufijo': '%',
          'modos': ['serie', 'barras', 'heatmap'],
          'nota_figura': ''},
 'ECO6': {'formato': '.4f', 'sufijo': '', 'modos': ['serie', 'barras'], 'nota_figura': ''},
 'ECO11': {'formato': '.1f',
           'sufijo': '%',
           'modos': ['serie', 'barras', 'heatmap'],
           'nota_figura': ''},
 'ECO13': {'formato': '.1f',
           'sufijo': '%',
           'modos': ['serie', 'barras', 'heatmap'],
           'nota_figura': ''},
 'ECO14': {'formato': '.1f',
           'sufijo': ' USD/MWh',
           'nota_figura': 'Los puntos huecos identifican valores calculados vía CAGR (2023–2024 en '
                          'cinco países; 2022–2024 en El Salvador).',
           'modos': ['serie', 'barras']},
 'ECO15': {'formato': '.1f',
           'sufijo': '%',
           'nota_figura': 'La línea punteada en 0 separa importadores (arriba) de exportadores '
                          'netos (abajo).',
           'modos': ['serie', 'heatmap', 'barras']},
 'ENV1': {'formato': '.4f',
          'sufijo': '',
          'modos': ['serie', 'barras'],
          'nota_figura': '',
          'series': {'ENV1_PC': {'formato': '.4f', 'sufijo': ' t/hab'},
                     'ENV1_PIB': {'formato': '.4f', 'sufijo': ' kg/USD'}}},
 'ENV2': {'formato': '.4f',
          'sufijo': '',
          'modos': ['serie', 'barras'],
          'nota_figura': '',
          'series': {'ENV2_SO2_PC': {'formato': '.3f', 'sufijo': ' kg/hab'},
                     'ENV2_PAR_PC': {'formato': '.4f', 'sufijo': ' kg/hab'},
                     'ENV2_SO2_PIB': {'formato': '.4f', 'sufijo': ' g/USD'},
                     'ENV2_PAR_PIB': {'formato': '.5f', 'sufijo': ' g/USD'}}},
 'ENV3': {'formato': '.3f',
          'sufijo': '',
          'modos': ['serie', 'barras', 'heatmap'],
          'nota_figura': '',
          'series': {'ENV3': {'formato': '.3f', 'sufijo': ' g/kWh'}}},
 'ENV6': {'formato': ',.0f', 'sufijo': ' GWh', 'modos': [], 'nota_figura': ''},
 'SOC1': {'formato': '.2f',
          'sufijo': '%',
          'modos': ['serie', 'barras', 'heatmap'],
          'nota_figura': '',
          'series': {'SOC1': {'formato': '.2f', 'sufijo': '%'}}},
 'SOC2': {'formato': '.2f',
          'sufijo': '%',
          'modos': ['serie', 'barras', 'heatmap'],
          'nota_figura': '',
          'series': {'SOC2_PROM': {'formato': '.2f', 'sufijo': '%'},
                     'SOC2_VULNERABLE': {'formato': '.2f', 'sufijo': '%'}}},
 'SOC3': {'formato': '.1f',
          'sufijo': '%',
          'modos': ['serie', 'barras', 'heatmap'],
          'nota_figura': '',
          'series': {'SOC3_RURAL': {'formato': '.1f', 'sufijo': '%'},
                     'SOC3_URB': {'formato': '.1f', 'sufijo': '%'}}}}

def construir_fichas():
    """Compone el contrato histórico sin mutar las definiciones científicas."""
    fichas = deepcopy(FICHAS_CIENTIFICAS)
    for codigo, ficha in fichas.items():
        estilo = PRESENTACION[codigo]
        if "series" in ficha:
            ficha["series"] = [
                [s["clave"], s["etiqueta"], estilo["series"][s["clave"]]["formato"],
                 estilo["series"][s["clave"]]["sufijo"], s["unidad"], s["formula"]]
                for s in ficha["series"]]
        ficha.update({k: deepcopy(v) for k, v in estilo.items() if k != "series"})
    return fichas

FICHAS = construir_fichas()


def series_de(ficha: dict, codigo: str) -> list[dict]:
    """Lista de sub-series de una ficha con el mismo esquema que usan
    los visualizadores: clave de datos, etiqueta, formato, unidad y
    fórmula. Las fichas ECO no tienen 'series' (una sola salida)."""
    if not ficha.get("series"):
        return [dict(clave=codigo, etiqueta="", formato=ficha["formato"],
                     unidad=ficha["unidad"], formula=ficha["formula"])]
    return [dict(clave=s[0], etiqueta=s[1], formato=s[2], unidad=s[4],
                 formula=s[5]) for s in ficha["series"]]
