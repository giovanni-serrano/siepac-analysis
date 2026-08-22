# SOC2 SIEPAC — base única de cálculo (2020–2024)

Este conjunto proviene de `SOC2_SIEPAC_BASE_UNICA_2020_2024.xlsx`. El libro
original mezclaba títulos, párrafos y varias subtablas por hoja. La carpeta
conserva únicamente los cuatro insumos canónicos que no se derivan entre sí;
los cálculos, auditorías y sensibilidades se regeneran con `src/etl_soc2.py`.

## Propósito del dataset

Concentra los datos nacionales de SOC2 (indicador de asequibilidad energética: gasto
residencial de electricidad / ingreso), la serie autoritativa de clientes residenciales, los
cálculos reproducibles del agregado regional SIEPAC y los resultados que acompañan la sección
de metodología e interpretación de la tesis.

## Fórmulas del cálculo principal (método: razón de sumas)

```
SOC2_PROM-SIEPAC = Σ(cargo_anual_usd × clientes) / Σ(ingreso_prom_usd × clientes) × 100
SOC2_VUL-SIEPAC  = Σ(cargo_anual_usd × clientes_vulnerables_proxy) /
                   Σ(ingreso_vulnerable_usd × clientes_vulnerables_proxy) × 100
```

- `clientes_vulnerables_proxy = clientes_residenciales × proporcion_vulnerable`
- `proporcion_vulnerable = 0.20` para los 6 países, **excepto Nicaragua = 0.296** (adaptación
  metodológica aceptada; el escenario 20% para Nicaragua solo se usa en la prueba de
  sensibilidad 2, nunca en el resultado principal).
- El resultado es un **proxy regional agregado**. No equivale a una estimación censal de
  hogares ni al promedio del país típico.

## Reglas críticas / supuestos

- **Clientes residenciales** se usan como proxy de unidades residenciales consumidoras
  conectadas; no son hogares censales exactos.
- **Estrato vulnerable**: p = 20% para cinco países; Nicaragua conserva 29.6% en el resultado
  principal.
- **Interpretación**: la sección de resultados de la tesis interpreta únicamente al SIEPAC
  como bloque regional; los valores por país (en `base_integrada` y `metodologia_pais`)
  quedan solo para trazabilidad y cálculo, no para comparación entre países.
- **Precisión**: las magnitudes de gasto e ingreso agregadas son proxies construidos a partir
  de valores unitarios nacionales multiplicados por clientes, no observaciones contables.
- **Criterio de dominancia** (ver `sensibilidad_4a/4b`): ningún país supera 50% del peso en
  clientes, numerador o denominador en 2020–2024.
- **Limitación central**: el ingreso de referencia nacional no proviene de una encuesta
  regional armonizada; en algunos países representa quintiles 2–5 en vez del promedio de
  todos los hogares.

## Insumos canónicos versionados

| Archivo | Contenido |
|---|---|
| `base_integrada.csv` | Tabla maestra país-año (30 filas = 6 países × 5 años) con todos los insumos y resultados nacionales. Llave única: `pais` + `anio`. |
| `diccionario.csv` | Diccionario de datos: definición, tipo y fuente de cada variable/método usado en el proyecto. |
| `metodologia_pais.csv` | Trazabilidad metodológica por país: qué encuesta/fuente se usó para ingreso PROM, ingreso vulnerable, cargo residencial, y qué tratamiento temporal se aplicó a los datos faltantes. |

## Productos regenerables

El ETL escribe en `data/processed/`:

- `soc2_pais_anio.csv`: valores nacionales y componentes auditables.
- `soc2_regional.csv`: serie regional principal y brecha vulnerable–promedio.
- `soc2_sensibilidad.csv`: escenarios de robustez.
- `soc2_auditoria.csv`: controles de cobertura y consistencia.

La prueba `tests/test_soc2.py` compara la serie principal contra una fixture de
regresión independiente. Las figuras y tablas finales se publican únicamente
en `salidas/tesis/`.

## Notas de trazabilidad no tabulares

- Honduras 2023: el SOC2 corregido ya documenta un ajuste de consistencia monetaria; no se
  reabre ni se modifica en este dataset.
- Clientes fraccionarios detectados (se preservan sin redondear): Nicaragua 2024 = 1,299,136.2;
  Panamá 2020 = 1,061,959.5.
- `metodologia_pais.csv` no se usa para interpretar resultados país por país;
  la interpretación se hace únicamente a nivel de bloque SIEPAC.
