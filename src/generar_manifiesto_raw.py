"""
generar_manifiesto_raw.py — Manifiesto legible de los datos crudos
====================================================
Etapa del pipeline : configuración (documentación, no alimenta al resto)
Entradas           : src/catalogo_datos_raw.py
Salidas            : data/raw/MANIFIESTO.md
Fuente de datos    : —

Escribe la versión en Markdown del catálogo de `catalogo_datos_raw.py`:
qué archivo espera cada ETL, de dónde se descarga, si su fuente permite
redistribuirlo y el hash SHA-256 de la copia verificada. Es la pieza que
permite que el pipeline siga siendo reproducible aunque algunos archivos
crudos no vivan en el repositorio (ver notas de licenciamiento en
`catalogo_datos_raw.py`): quien clona el proyecto descarga su propia
copia y corre `verificar_datos_raw.py` para confirmar que es la misma.

Uso:  python src/generar_manifiesto_raw.py   (ejecutar desde la raíz)

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import logging
import sys
from datetime import date
from pathlib import Path

from catalogo_datos_raw import CATALOGO_RAW
from config_siepac import DIR_RAW

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(Path(__file__).stem)

RUTA_MANIFIESTO = DIR_RAW / "MANIFIESTO.md"

ETIQUETA_REDIST = {
    "no": "**No** (verificado)",
    "si": "**Sí** (CC-BY 4.0)",
}


def _tabla_resumen() -> list[str]:
    lineas = ["| Variable | Fuente | ¿Redistribuible? | En este repositorio |",
              "|---|---|---|---|"]
    for e in CATALOGO_RAW:
        en_repo = "No — ver más abajo" if e.redistribuible == "no" else "Sí"
        lineas.append(f"| {e.variable} | {e.fuente} | "
                      f"{ETIQUETA_REDIST[e.redistribuible]} | {en_repo} |")
    return lineas


def _ficha(e) -> list[str]:
    return [
        f"\n### `data/raw/{e.carpeta}/`\n",
        f"- **Variable:** {e.variable}",
        f"- **Fuente:** {e.fuente}",
        f"- **¿Redistribuible?:** {ETIQUETA_REDIST[e.redistribuible]}",
        f"- **Cobertura:** {e.cobertura}",
        f"- **Patrón que localiza el ETL:** `{e.patron}` (el nombre exacto "
        f"cambia en cada descarga: los exports llevan timestamp)",
        f"- **Dónde descargarlo:** {e.ruta_navegacion}",
        f"- **SHA-256 de la copia verificada:** `{e.sha256}`",
        f"- **Tamaño de esa copia:** {e.tamano_bytes:,} bytes",
    ]


def main() -> None:
    contenido = [
        "# Manifiesto de datos crudos\n",
        "Generado automáticamente por `src/generar_manifiesto_raw.py` el "
        f"{date.today().isoformat()} a partir de `src/catalogo_datos_raw.py` "
        "— no editar a mano.\n",
        "Documenta, para cada variable de entrada del pipeline, de dónde se "
        "descarga, si su fuente permite redistribuir el archivo y el hash "
        "SHA-256 de la copia con la que se verificaron los cálculos de este "
        "proyecto. Después de descargar un archivo, correr "
        "`python src/verificar_datos_raw.py` confirma que es exactamente esa "
        "copia (o avisa si difiere, por ejemplo porque la fuente actualizó "
        "la serie).\n",
        "No cubre `data/raw_equipo/` (entregables propios del equipo de "
        "tesis, no descargas de una fuente externa) ni las fichas técnicas "
        "en PDF (documentación de referencia, no entrada del pipeline).\n",
    ]
    contenido += _tabla_resumen()
    contenido.append(
        "\nLos archivos marcados **No** no están en este repositorio: los "
        "términos de sus fuentes prohíben redistribuir el archivo "
        "descargado. OLADE/SIELAC veda el «almacenamiento en cualquier otro "
        "sistema» y la «distribución por cualquier medio»; CEPAL permite "
        "bajar y copiar sus materiales «para su uso personal, sin fines "
        "comerciales, sin ningún derecho a revender, redistribuir, o crear "
        "otros trabajos a partir de los mismos» (agenda2030lac lo opera "
        "CEPAL y hereda ese acuerdo). Ambos verificados el 2026-07-26; las "
        "citas completas están en `src/catalogo_datos_raw.py`.\n"
        "\nEso no impide usar los datos: las dos fuentes contemplan su uso "
        "citando la procedencia, que es lo que hace este proyecto. Lo que "
        "no se puede es republicar sus archivos. Siguen siendo el insumo "
        "real del pipeline — cada quien descarga su propia copia desde la "
        "ruta indicada en su ficha.\n")
    contenido.append("## Fichas por variable\n")
    for e in CATALOGO_RAW:
        contenido += _ficha(e)

    DIR_RAW.mkdir(parents=True, exist_ok=True)
    RUTA_MANIFIESTO.write_text("\n".join(contenido) + "\n", encoding="utf-8")
    log.info("Exportado: %s (%d variables)", RUTA_MANIFIESTO, len(CATALOGO_RAW))


if __name__ == "__main__":
    main()
