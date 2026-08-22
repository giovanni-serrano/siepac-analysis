"""
generar_capturas_readme.py — Capturas reproducibles del visualizador regional
====================================================
Etapa del pipeline : documentación pública
Entradas           : graficos/visualizador_siepac.html
Salidas            : docs/Visualizador_Regional.png y
                     docs/Visualizador_Indicador.png
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

RUTA_ENTRADA = DIR_GRAFICOS / "visualizador_siepac.html"
CAPTURA_INICIO = RAIZ_PROYECTO / "docs" / "Visualizador_Regional.png"
CAPTURA_DETALLE = RAIZ_PROYECTO / "docs" / "Visualizador_Indicador.png"


def main() -> None:
    if not RUTA_ENTRADA.exists():
        raise FileNotFoundError(
            f"VALIDACIÓN FALLIDA: primero genere {RUTA_ENTRADA}")

    with sync_playwright() as playwright:
        navegador = playwright.chromium.launch(headless=True)
        pagina = navegador.new_page(
            viewport={"width": 1880, "height": 930},
            device_scale_factor=1,
        )
        pagina.goto(RUTA_ENTRADA.resolve().as_uri(), wait_until="load")
        pagina.wait_for_selector(".hero-stats", state="visible")
        pagina.screenshot(path=str(CAPTURA_INICIO), full_page=False)
        log.info("OK  %s", CAPTURA_INICIO.relative_to(RAIZ_PROYECTO))

        pagina.locator(".card").first.click()
        pagina.wait_for_selector("#chart .plot-container", state="visible")
        pagina.wait_for_selector(".finding", state="visible")
        pagina.wait_for_timeout(500)
        pagina.set_viewport_size({"width": 1880, "height": 1200})
        pagina.screenshot(path=str(CAPTURA_DETALLE), full_page=False)
        log.info("OK  %s", CAPTURA_DETALLE.relative_to(RAIZ_PROYECTO))
        navegador.close()


if __name__ == "__main__":
    main()
