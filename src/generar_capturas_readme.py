"""
generar_capturas_readme.py — Capturas reproducibles de las apps HTML
====================================================
Etapa del pipeline : documentación pública
Entradas           : graficos/panel_siepac.html y
                     graficos/0_explorador_indicadores.html
Salidas            : docs/Panel.png y docs/Explorador_Indicadores.png
Alimenta           : README.md
Fuente de datos    : visualizadores HTML generados por el pipeline

Uso:  python src/generar_capturas_readme.py   (desde la raíz)
      Requiere: python -m playwright install chromium

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from config_siepac import DIR_GRAFICOS, RAIZ_PROYECTO

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

CAPTURAS = [
    (DIR_GRAFICOS / "panel_siepac.html", RAIZ_PROYECTO / "docs" / "Panel.png",
     ".hero-stats"),
    (DIR_GRAFICOS / "0_explorador_indicadores.html",
     RAIZ_PROYECTO / "docs" / "Explorador_Indicadores.png", "#grafico"),
]


def main() -> None:
    faltantes = [entrada for entrada, _, _ in CAPTURAS
                 if not entrada.exists()]
    if faltantes:
        raise FileNotFoundError(
            "VALIDACIÓN FALLIDA: primero genere los visualizadores: " +
            ", ".join(str(ruta) for ruta in faltantes))

    with sync_playwright() as playwright:
        navegador = playwright.chromium.launch(headless=True)
        pagina = navegador.new_page(
            viewport={"width": 1880, "height": 930},
            device_scale_factor=1,
        )
        for entrada, salida, selector in CAPTURAS:
            pagina.goto(entrada.resolve().as_uri(), wait_until="load")
            pagina.wait_for_selector(selector, state="visible")
            pagina.wait_for_timeout(1200)
            pagina.screenshot(path=str(salida), full_page=False)
            log.info("OK  %s", salida.relative_to(RAIZ_PROYECTO))
        navegador.close()


if __name__ == "__main__":
    main()
