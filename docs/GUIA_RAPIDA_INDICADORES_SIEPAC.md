# Guía de agregación regional — indicadores SIEPAC

Este documento resume el criterio de agregación empleado para representar
los seis países del SIEPAC como un bloque. Las cifras completas se encuentran
en `graficos/region/tabla_agregados.csv` y las figuras en
`graficos/region/`.

## Criterios de cálculo

- **Agregado regional:** razón entre la suma de los numeradores y la suma de
  los denominadores nacionales. Representa al SIEPAC como sistema.
- **Promedio de países:** media simple de los seis valores nacionales.
  Representa el comportamiento del país típico del conjunto.
- Ambos resultados se identifican por separado porque responden a unidades
  de análisis distintas.

Los gráficos `*_agregado_vs_promedio.png` presentan el agregado regional en
azul y el promedio de países en gris punteado. El valor del último año se
etiqueta directamente sobre cada serie.

## Indicadores con agregado regional

### ECO1 · Uso de energía per cápita

- **Cálculo:** Σ consumo final (kWh) ÷ Σ población.
- **Resultado:** 959 → 1 063 kWh/hab (+10.9 %).
- **Gráficos:** `ECO1_agregado_vs_promedio.png` y
  `REGION_consumo_final.png`.

### ECO2 · Energía por unidad de PIB

- **Cálculo:** Σ consumo final ÷ Σ PIB real en USD constantes de 2015.
- **Resultado:** 0.195 → 0.179 kWh/USD (−8.3 %).
- **Gráfico:** `ECO2_agregado_vs_promedio.png`.

### ECO3 · Eficiencia de conversión y distribución

- **Cálculo:** Σ consumo final ÷ Σ producción bruta × 100.
- **Resultado:** 82.4 → 82.6 % (+0.2 pp).
- **Gráfico:** `ECO3_agregado_vs_promedio.png`.

### ECO6 · Intensidad energética de la industria

- **Cálculo:** Σ consumo industrial ÷ Σ valor agregado manufacturero.
- **Resultado:** 0.370 → 0.497 kWh/USD (+34.4 %).
- **Gráfico:** `ECO6_agregado_vs_promedio.png`.

### ECO11 · Participación fósil

- **Cálculo:** Σ generación fósil ÷ Σ generación total × 100.
- **Resultado:** 25.0 → 33.0 % (+8.0 pp).
- **Gráficos:** `ECO11_agregado_vs_promedio.png` y
  `REGION_renovable_vs_fosil.png`.

### ECO13 · Participación renovable

- **Cálculo:** Σ generación renovable ÷ Σ generación total × 100.
- **Resultado:** 75.0 → 67.0 % (−8.0 pp).
- **Gráficos:** `ECO13_agregado_vs_promedio.png` y
  `REGION_generacion_fuentes.png`.

### ECO15 · Dependencia de importaciones netas

- **Cálculo:** Σ(importaciones − exportaciones) ÷ Σ oferta × 100.
- **Resultado:** 1.65 → 2.17 % (+0.5 pp).
- Los intercambios internos del MER se cancelan al sumar el bloque; el saldo
  agregado representa el intercambio extrarregional.
- **Gráficos:** `ECO15_agregado_vs_promedio.png` y
  `REGION_intercambios.png`.

### SOC1 · Población sin electricidad

- **Cálculo:** personas sin electricidad del bloque ÷ población total del
  bloque × 100.
- **Resultado:** 7.57 → 6.72 % (−0.8 pp).
- **Gráficos:** `SOC1_agregado_vs_promedio.png` y
  `REGION_personas_sin_electricidad.png`.

### SOC3 · Acceso a energía renovable rural y urbano

- **Cálculo rural:** media de los porcentajes nacionales ponderada por
  población rural. Resultado: 58.0 → 51.2 % (−6.8 pp).
- **Cálculo urbano:** media de los porcentajes nacionales ponderada por
  población urbana. Resultado: 73.2 → 61.9 % (−11.3 pp).
- Cada serie combina la tasa de electrificación de la zona con la
  participación renovable de la generación nacional.
- **Gráficos:** `SOC3_RURAL_agregado_vs_promedio.png`,
  `SOC3_URB_agregado_vs_promedio.png` y
  `SOC3_brecha_rural_urbana_agregado.png`.

## Ejemplo de cálculo — SOC1, año 2024

La tasa nacional de población sin electricidad se multiplica por la
población de cada país para obtener el numerador nacional. Los numeradores y
denominadores se suman antes de calcular el porcentaje regional.

| País | Tasa sin electricidad | Población | Personas sin electricidad |
|---|---:|---:|---:|
| Costa Rica | 0.60 % | 5 129 900 | 30 779 |
| El Salvador | 1.70 % | 6 338 200 | 107 749 |
| Guatemala | 9.11 % | 18 406 400 | 1 676 823 |
| Honduras | 13.64 % | 10 825 700 | 1 476 626 |
| Nicaragua | 0.443 % | 6 916 100 | 30 638 |
| Panamá | 4.00 % | 4 515 600 | 180 624 |
| **Total SIEPAC** | | **52 131 900** | **3 503 240** |

> SOC1 SIEPAC = 3 503 240 ÷ 52 131 900 × 100 = **6.72 %**

El promedio simple de los seis porcentajes nacionales es 4.92 %. La
diferencia corresponde al peso poblacional de cada país en el agregado.

Fuentes del cálculo: `data/raw_equipo/SOCs.xlsx` para las tasas nacionales y
CEPALSTAT-CELADE para la población total. El pipeline conserva los resultados
en `data/processed/indicadores_SOC_SIEPAC.xlsx` y
`graficos/region/tabla_agregados.csv`.

## Series representadas mediante promedio de países

- **ECO14:** presenta el promedio simple de las tarifas nacionales. Los
  valores calculados mediante CAGR se identifican en las tablas y los
  visualizadores. La razón de sumas requiere energía regulada vendida por
  país y año.
- **SOC2:** presenta estadísticas descriptivas y promedio simple de los
  resultados nacionales. Los insumos monetarios permanecen expresados en el
  marco de cada país, por lo que no se construye una razón de sumas regional.

La definición completa de cada indicador se mantiene en
`docs/resumen_indicadores_SIEPAC.md` y en `src/viz_comun.py`.
