"""
viz_comun.py — Paleta y compatibilidad de imports históricos
====================================================
Etapa del pipeline : presentación (módulo importable)
Entradas           : resultados y fichas comunes, mediante reexportaciones
Salidas            : paleta y símbolos históricos
Alimenta           : visualizador y consumidores anteriores
Fuente de datos    : resultados_indicadores; metadatos_indicadores
Uso                : importar la paleta; los nuevos consumidores de datos usan
                     directamente resultados_indicadores
Notas metodológicas: no calcula indicadores ni mantiene definiciones científicas.
Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""
from config_siepac import (PAISES_SIEPAC as PAISES, ANIOS_ANALISIS as ANIOS,
                           DIR_PROCESSED)
from calculos_indicadores import media_ponderada, agregados_eco
from metadatos_indicadores import SERIES_ENV, SERIES_SOC
from presentacion_indicadores import FICHAS
from resultados_indicadores import (cargar_datos, preparar_datos,
                                    leer_series_extra, construir_datos_json)

# Nombres históricos conservados para quien localiza los libros publicados.
RUTA_EXCEL = DIR_PROCESSED / "indicadores_ECO_SIEPAC.xlsx"
RUTA_VALORES = DIR_PROCESSED / "indicadores_ECO_valores.csv"
RUTA_ENV = DIR_PROCESSED / "indicadores_ENV_SIEPAC.xlsx"
RUTA_SOC = DIR_PROCESSED / "indicadores_SOC_SIEPAC.xlsx"

COLOR_FONDO = "#FAF9F5"        # crema cálido
COLOR_TEXTO = "#1F1E1D"        # casi negro cálido
COLOR_TEXTO_SUAVE = "#6E6A63"  # gris topo para subtítulos
COLOR_GRILLA = "#E8E4DB"       # líneas de grilla muy suaves
FUENTE_TITULO = "Georgia, 'Times New Roman', serif"
FUENTE_CUERPO = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

# Un color por país; Nicaragua lleva el terracota de acento del proyecto.
COLORES_PAIS = {
    "Costa Rica":  "#3E8A7B",   # verde bosque
    "El Salvador": "#5B84A8",   # azul pizarra
    "Guatemala":   "#C2963F",   # ocre
    "Honduras":    "#8B7BA8",   # lila grisaceo
    "Nicaragua":   "#D97757",   # terracota
    "Panamá":      "#6B705C",   # verde oliva
}
