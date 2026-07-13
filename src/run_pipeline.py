"""
run_pipeline.py — Orquestador del pipeline completo
====================================================
Etapa del pipeline : orquestación (ejecuta los 14 scripts en orden)
Entradas           : — (cada script lee sus propias entradas)
Salidas            : — (las de cada script: CSVs, Excel y HTML)

Ejecuta los ETL, la consolidación, los generadores de indicadores y los
dos visualizadores en el orden correcto de dependencias, y se detiene en
el primer script que termine con error (incluida una VALIDACIÓN FALLIDA).

Uso:  python src/run_pipeline.py   (ejecutar desde la raíz del proyecto)

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent

# Orden de ejecución. La única dependencia entre ETL es que
# etl_valor_agregado_industrial necesita pib.csv (por eso va después).
ORDEN = [
    "etl_consumo_final_total.py",
    "etl_consumo_industrial.py",
    "etl_poblacion_total.py",
    "etl_pib.py",
    "etl_valor_agregado_industrial.py",
    "etl_produccion_bruta.py",
    "etl_importaciones_exportaciones.py",
    "etl_tarifa_electrica_media.py",
    "etl_generacion_por_fuente.py",
    "consolidar_matriz.py",
    "generar_matriz_indicadores.py",
    "procesar_dimensiones.py",
    "generar_explorador.py",
    "generar_panel.py",
]


def main() -> None:
    for i, nombre in enumerate(ORDEN, start=1):
        print(f"\n=== [{i:2d}/{len(ORDEN)}] {nombre} " + "=" * 30)
        resultado = subprocess.run([sys.executable, str(SRC / nombre)])
        if resultado.returncode != 0:
            sys.exit(f"\nPipeline DETENIDO: {nombre} terminó con código "
                     f"{resultado.returncode}. Revisar los mensajes de arriba.")
    print(f"\nPipeline completo: {len(ORDEN)}/{len(ORDEN)} scripts OK.")


if __name__ == "__main__":
    main()
