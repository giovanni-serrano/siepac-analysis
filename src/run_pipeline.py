"""
run_pipeline.py — Orquestador del pipeline completo
====================================================
Etapa del pipeline : orquestación (ejecuta los scripts en orden)
Entradas           : — (cada script lee sus propias entradas)
Salidas            : — (las de cada script: CSVs, Excel, HTML y PNG)

Ejecuta los ETL, la consolidación, los generadores de indicadores, las
tablas APA, las figuras oficiales, su manifiesto y los visualizadores en el
orden correcto de dependencias. Se detiene en el primer script con error
(incluida una VALIDACIÓN FALLIDA). El visualizador regional único se genera
junto a las dos aplicaciones anteriores mientras se verifica su paridad.

Uso:  python src/run_pipeline.py   (ejecutar desde la raíz del proyecto)

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent

# Orden de ejecución: la población por zona se contrasta con población total
# y el valor agregado industrial requiere el PIB procesado.
ORDEN = [
    "etl_consumo_final_total.py",
    "etl_consumo_industrial.py",
    "etl_poblacion_total.py",
    "etl_poblacion_rural_urbana.py",
    "etl_pib.py",
    "etl_valor_agregado_industrial.py",
    "etl_produccion_bruta.py",
    "etl_importaciones_exportaciones.py",
    "etl_tarifa_electrica_media.py",
    "etl_generacion_por_fuente.py",
    "etl_soc2.py",
    "consolidar_matriz.py",
    "generar_matriz_indicadores.py",
    "procesar_dimensiones.py",
    "generar_resumen_indicadores.py",
    "generar_tablas_apa.py",
    "generar_figuras_tesis.py",
    "generar_manifiesto_tesis.py",
    "generar_visualizador.py",
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
