"""
exportar_graficos.py — Exporta a PNG los gráficos del explorador
====================================================
Etapa del pipeline : visualización (posterior a generar_explorador.py)
Entradas           : graficos/0_explorador_indicadores.html
Salidas            : graficos/eco/*.png, graficos/env/*.png, graficos/soc/*.png
Alimenta           : — (imágenes estáticas para el documento de tesis)
Fuente de datos    : el propio explorador HTML (Plotly.js)

Toma el explorador ya generado y, con un navegador Chromium sin ventana
(headless), fotografía cada gráfico TAL CUAL se ve en el visor usando
Plotly.toImage. No redibuja nada en Python: maneja las mismas funciones
JavaScript del explorador (render, setModo, setSerie, setPaisEnv6), así la
imagen nunca discrepa del gráfico interactivo (una sola fuente de verdad).

Exporta las vistas de SERIE TEMPORAL y de BARRAS (2020 vs 2024) de cada
indicador y sub-serie; los mapas de calor se omiten a propósito. Cada
imagen se guarda en la carpeta de su dimensión (eco/env/soc), tomada del
campo "dim" de la ficha del indicador en viz_comun.py.

Requisito (una sola vez):
    pip install playwright
    python -m playwright install chromium

Uso:  python src/exportar_graficos.py   (ejecutar desde la raíz, después
      de generar_explorador.py)

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import base64
import logging
import sys
import unicodedata
from pathlib import Path

from config_siepac import DIR_GRAFICOS, PAISES_SIEPAC as PAISES
from viz_comun import FICHAS

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

RUTA_HTML = DIR_GRAFICOS / "0_explorador_indicadores.html"

# Vistas a exportar. El explorador ofrece además "heatmap", que se omite
# a propósito (decisión del proyecto: solo serie temporal y barras).
MODOS_EXPORTAR = ["serie", "barras"]

# Tamaño lógico del lienzo y factor de escala. La imagen final mide
# ANCHO*ESCALA x ALTO*ESCALA píxeles (por defecto 3000x1860), nítida para
# insertar en el documento.
ANCHO, ALTO, ESCALA = 1000, 620, 3

PREFIJO_PNG = "data:image/png;base64,"


def _slug(texto: str) -> str:
    """Convierte 'Per cápita' -> 'per-capita' (sin tildes, minúsculas,
    espacios como guiones) para nombres de archivo limpios."""
    sin_tildes = (unicodedata.normalize("NFKD", texto)
                  .encode("ascii", "ignore").decode("ascii"))
    limpio = "".join(c if c.isalnum() else "-" for c in sin_tildes.lower())
    return "-".join(p for p in limpio.split("-") if p)


def _combinaciones() -> list[dict]:
    """Genera la lista de imágenes a exportar leyendo FICHAS (mismo catálogo
    que usa el explorador). Cada entrada trae qué renderizar, en qué carpeta
    guardarla y con qué nombre de archivo."""
    tareas = []
    for codigo, ficha in FICHAS.items():
        dim = ficha["dim"]

        # ENV6: gráfico de barras especial con un país por imagen.
        if ficha.get("tipo") == "env6":
            for pais in PAISES:
                tareas.append(dict(
                    codigo=codigo, dim=dim, clave="ENV6", pais=pais,
                    nombre=f"{codigo}_{_slug(pais)}"))
            continue

        # Indicadores normales: una o varias sub-series, cada una en las
        # vistas de serie y barras que ofrezca la ficha.
        series = ficha.get("series")
        indices = range(len(series)) if series else [0]
        for i in indices:
            clave = series[i][0] if series else codigo
            etiqueta = series[i][1] if series else ""
            for modo in ficha["modos"]:
                if modo not in MODOS_EXPORTAR:
                    continue
                partes = [codigo]
                if etiqueta:
                    partes.append(_slug(etiqueta))
                partes.append(modo)
                tareas.append(dict(
                    codigo=codigo, dim=dim, clave=clave, serie=i, modo=modo,
                    pais=None, nombre="_".join(partes)))
    return tareas


# JavaScript que se ejecuta dentro de la página: posiciona el explorador en
# la vista pedida (reutilizando sus propias funciones) y devuelve el PNG
# como data URL en base64.
_JS_CAPTURA = """
async ({codigo, serie, modo, pais, ancho, alto, escala}) => {
  render(codigo);                         // fija el indicador activo
  if (pais !== null) setPaisEnv6(pais);   // ENV6: elige el país
  else { setSerie(serie); setModo(modo); }
  const gd = document.getElementById('grafico');
  return await Plotly.toImage(
      gd, {format: 'png', width: ancho, height: alto, scale: escala});
}
"""


def main() -> None:
    if not RUTA_HTML.exists():
        sys.exit(f"No se encontró {RUTA_HTML}.\n"
                 "Ejecuta antes: python src/generar_explorador.py")

    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        sys.exit("Falta Playwright. Instálalo una sola vez con:\n"
                 "  pip install playwright\n"
                 "  python -m playwright install chromium")

    for dim in ("eco", "env", "soc"):
        (DIR_GRAFICOS / dim).mkdir(parents=True, exist_ok=True)

    tareas = _combinaciones()
    log.info("Explorador: %s", RUTA_HTML.name)
    log.info("A exportar: %d imagenes (vistas: %s) a %dx%d px",
             len(tareas), " + ".join(MODOS_EXPORTAR),
             ANCHO * ESCALA, ALTO * ESCALA)

    exportadas = omitidas = 0
    with sync_playwright() as pw:
        try:
            navegador = pw.chromium.launch()
        except Exception as exc:
            sys.exit(f"No se pudo abrir Chromium ({exc}).\n"
                     "Instálalo una sola vez con:\n"
                     "  python -m playwright install chromium")
        pagina = navegador.new_page(
            viewport={"width": ANCHO + 400, "height": ALTO + 200})
        pagina.goto(RUTA_HTML.as_uri())
        # Esperar a que el explorador y Plotly estén listos.
        pagina.wait_for_function(
            "() => typeof render === 'function' "
            "&& typeof Plotly !== 'undefined'")

        for t in tareas:
            # Omitir indicadores cuya dimensión no llegó (archivo faltante):
            # se comprueba igual que el menú del explorador.
            if not pagina.evaluate("(clave) => clave in DATOS", t["clave"]):
                log.warning("Sin datos, se omite: %s", t["nombre"])
                omitidas += 1
                continue

            url = pagina.evaluate(_JS_CAPTURA, {
                "codigo": t["codigo"], "serie": t.get("serie", 0),
                "modo": t.get("modo", "serie"), "pais": t["pais"],
                "ancho": ANCHO, "alto": ALTO, "escala": ESCALA})

            destino = DIR_GRAFICOS / t["dim"] / f"{t['nombre']}.png"
            destino.write_bytes(base64.b64decode(url[len(PREFIJO_PNG):]))
            exportadas += 1
            log.info("  OK  %s/%s.png", t["dim"], t["nombre"])

        navegador.close()

    log.info("Listo: %d PNG exportados en graficos/{eco,env,soc}/%s",
             exportadas, f" ({omitidas} omitidos)" if omitidas else "")


if __name__ == "__main__":
    main()
