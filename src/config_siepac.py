"""
config_siepac.py — Constantes compartidas del proyecto (fuente única de verdad)
====================================================
Etapa del pipeline : configuración (módulo común, no se ejecuta directo)
Entradas           : —
Salidas            : — (lo importan todos los scripts de src/)

Define las rutas del proyecto, la lista canónica de países del SIEPAC
(grafía con tildes), los códigos ISO3, la ventana de análisis y las
constantes de conversión de unidades.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""
from pathlib import Path

# Raíz del proyecto: este archivo vive en src/, así que subimos un nivel.
RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
DIR_RAW = RAIZ_PROYECTO / "data" / "raw"
DIR_PROCESSED = RAIZ_PROYECTO / "data" / "processed"
DIR_GRAFICOS = RAIZ_PROYECTO / "graficos"

# Los 6 países del SIEPAC, grafía canónica del proyecto (con tildes).
PAISES_SIEPAC = ["Costa Rica", "El Salvador", "Guatemala",
                 "Honduras", "Nicaragua", "Panamá"]

CODIGOS_ISO3 = {"GTM": "Guatemala", "SLV": "El Salvador", "HND": "Honduras",
                "NIC": "Nicaragua", "CRI": "Costa Rica", "PAN": "Panamá"}

ANIOS_ANALISIS = [2020, 2021, 2022, 2023, 2024]

GWH_A_KWH = 1_000_000  # 1 GWh = 1,000,000 kWh
