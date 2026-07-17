# Matriz consolidada de indicadores — SIEPAC 2020–2024

**Proyecto:** Evaluación del suministro de energía eléctrica en el SIEPAC:
perspectivas económicas, sociales y ambientales. Monográfico de
Ingeniería Eléctrica, Universidad Nacional de Ingeniería (Nicaragua).
**Metodología:** indicadores IEDS (*Energy Indicators for Sustainable
Development*, OIEA/NU, 2005).
**Cobertura:** Costa Rica, El Salvador, Guatemala, Honduras, Nicaragua, Panamá — los seis países interconectados por
el SIEPAC — ventana 2020–2024.
**Fuentes de datos:** SIELAC·OLADE, CEPALSTAT·CEPAL, Banco Mundial (WDI)
y EOR (Mercado Eléctrico Regional).
**Documento generado automáticamente** por
`src/generar_resumen_indicadores.py` el 2026-07-17;
los valores provienen del mismo pipeline que alimenta los visualizadores.

## Cómo leer este documento

Cada indicador incluye su ficha (unidad, fórmula, descripción y notas
metodológicas) y su tabla de valores por país y año, con el promedio
regional (media simple de los seis países) y la variación 2020→2024
(relativa en % para magnitudes; en puntos porcentuales, pp, para
indicadores que ya son porcentajes). "s.d." = sin dato.
Los indicadores con varias salidas (p. ej. per cápita y por PIB)
presentan una tabla por sub-serie.


## Dimensión económica


### ECO1 · Uso de energía per cápita

Consumo final total dividido entre la población. Refleja el nivel de acceso y uso efectivo de la electricidad por persona.

**ECO1** · Unidad: kWh/habitante · Fórmula: Consumo final total (kWh) ÷ Población

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 1,966 | 1,958 | 2,096 | 2,133 | 2,151 | +9.4 % |
| El Salvador | 961 | 1,051 | 1,073 | 1,124 | 1,290 | +34.3 % |
| Guatemala | 598 | 668 | 630 | 675 | 698 | +16.8 % |
| Honduras | 655 | 754 | 727 | 737 | 800 | +22.1 % |
| Nicaragua | 556 | 587 | 594 | 609 | 613 | +10.2 % |
| Panamá | 2,568 | 2,798 | 2,876 | 3,001 | 2,318 | -9.7 % |
| **Promedio regional** | **1,217** | **1,303** | **1,333** | **1,380** | **1,312** | **+7.8 %** |


### ECO2 · Uso de energía por unidad de PIB

Cuánta energía consume la economía por cada dólar de PIB real. Bajar en el tiempo sugiere desacople entre crecimiento y consumo energético.

**ECO2** · Unidad: kWh/USD const. 2015 · Fórmula: Consumo final total (kWh) ÷ PIB real (USD constantes 2015)

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 0.1606 | 0.1489 | 0.1531 | 0.1490 | 0.1447 | -9.9 % |
| El Salvador | 0.2522 | 0.2474 | 0.2462 | 0.2504 | 0.2814 | +11.5 % |
| Guatemala | 0.1493 | 0.1565 | 0.1438 | 0.1509 | 0.1530 | +2.5 % |
| Honduras | 0.2992 | 0.3110 | 0.2928 | 0.2915 | 0.3109 | +3.9 % |
| Nicaragua | 0.2853 | 0.2760 | 0.2731 | 0.2719 | 0.2678 | -6.1 % |
| Panamá | 0.2030 | 0.1923 | 0.1802 | 0.1778 | 0.1354 | -33.3 % |
| **Promedio regional** | **0.2250** | **0.2220** | **0.2149** | **0.2153** | **0.2155** | **-4.2 %** |


### ECO3 · Eficiencia de conversión y distribución

Porcentaje de la producción bruta que llega como consumo final. La brecha son pérdidas técnicas, autoconsumo y saldo de intercambios.

> Nota metodológica: Aproximación generación→consumo final; no cubre la cadena energética primaria completa.

**ECO3** · Unidad: % · Fórmula: (Consumo final total ÷ Producción bruta) × 100

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 85.3 | 78.5 | 85.7 | 90.7 | 87.8 | +2.6 pp |
| El Salvador | 94.5 | 101.4 | 89.0 | 82.3 | 93.8 | -0.7 pp |
| Guatemala | 81.1 | 81.7 | 85.6 | 89.8 | 87.0 | +5.9 pp |
| Honduras | 66.5 | 70.8 | 68.2 | 66.2 | 68.2 | +1.7 pp |
| Nicaragua | 95.9 | 92.8 | 93.8 | 87.0 | 87.0 | -8.8 pp |
| Panamá | 83.7 | 87.0 | 90.0 | 91.7 | 77.8 | -5.9 pp |
| **Promedio regional** | **84.5** | **85.4** | **85.4** | **84.6** | **83.6** | **-0.9 pp** |


### ECO6 · Intensidad energética de la industria

Energía que necesita la industria por cada dólar de valor agregado industrial. Menor = industria que genera más valor por kWh.

**ECO6** · Unidad: kWh/USD const. 2015 · Fórmula: Consumo industrial (kWh) ÷ Valor agregado industrial (USD 2015)

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 0.2401 | 0.1923 | 0.4318 | 0.4320 | 0.4409 | +83.7 % |
| El Salvador | 0.5428 | 0.4808 | 0.5978 | 0.6439 | 0.8776 | +61.7 % |
| Guatemala | 0.3666 | 0.4295 | 0.3866 | 0.4153 | 0.4235 | +15.5 % |
| Honduras | 0.5792 | 0.6403 | 0.6445 | 0.6210 | 0.6888 | +18.9 % |
| Nicaragua | 0.5823 | 0.5814 | 0.5908 | 0.5524 | 0.5810 | -0.2 % |
| Panamá | 0.1457 | 0.1729 | 0.1033 | 0.2550 | 0.2520 | +72.9 % |
| **Promedio regional** | **0.4094** | **0.4162** | **0.4591** | **0.4866** | **0.5440** | **+32.9 %** |


### ECO11 · Fósiles en la electricidad

Participación de la generación térmica fósil en la generación total. El espejo de ECO13.

**ECO11** · Unidad: % · Fórmula: (Generación térmica fósil ÷ Generación total) × 100

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 0.2 | 0.0 | 0.7 | 5.1 | 10.6 | +10.4 pp |
| El Salvador | 16.0 | 15.8 | 22.6 | 39.1 | 31.1 | +15.1 pp |
| Guatemala | 24.7 | 28.6 | 21.7 | 33.8 | 40.8 | +16.1 pp |
| Honduras | 44.2 | 38.3 | 40.2 | 47.7 | 47.7 | +3.5 pp |
| Nicaragua | 30.2 | 30.8 | 34.4 | 41.4 | 48.2 | +18.0 pp |
| Panamá | 35.0 | 31.5 | 32.7 | 45.3 | 26.9 | -8.0 pp |
| **Promedio regional** | **25.0** | **24.2** | **25.4** | **35.4** | **34.2** | **+9.2 pp** |


### ECO13 · Renovables en la electricidad

Hidro + geotermia + eólica + solar + biomasa como porcentaje de la generación total.

**ECO13** · Unidad: % · Fórmula: (Hidro + Geotermia + Eólica + Solar + Biomasa) ÷ Generación total × 100

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 99.8 | 100.0 | 99.3 | 94.9 | 89.4 | -10.4 pp |
| El Salvador | 84.0 | 84.2 | 77.4 | 60.9 | 68.9 | -15.1 pp |
| Guatemala | 75.3 | 71.4 | 78.3 | 66.2 | 59.2 | -16.1 pp |
| Honduras | 55.8 | 61.7 | 59.8 | 52.3 | 52.3 | -3.5 pp |
| Nicaragua | 69.8 | 69.2 | 65.6 | 58.6 | 51.8 | -18.0 pp |
| Panamá | 65.0 | 68.5 | 67.3 | 54.7 | 73.1 | +8.0 pp |
| **Promedio regional** | **75.0** | **75.8** | **74.6** | **64.6** | **65.8** | **-9.2 pp** |


### ECO14 · Precio medio de la electricidad

Ingresos por energía regulada vendida entre energía regulada consumida. En dólares corrientes de cada año.

> Nota metodológica: Los puntos huecos son valores imputados vía CAGR (2023–2024 en cinco países; 2022–2024 en El Salvador), no observaciones reales.

**ECO14** · Unidad: USD corrientes/MWh · Fórmula: Ingresos por energía regulada (USD) ÷ Energía regulada (MWh)

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 155.2 | 131.0 | 130.7 | 126.9\* | 123.2\* | -20.6 % |
| El Salvador | 172.1 | 181.3 | 179.7\* | 178.1\* | 176.6\* | +2.6 % |
| Guatemala | 198.4 | 205.1 | 223.9 | 228.1\* | 232.4\* | +17.1 % |
| Honduras | 177.6 | 183.4 | 235.4 | 250.5\* | 266.5\* | +50.1 % |
| Nicaragua | 218.0 | 195.3 | 196.5 | 195.4\* | 194.4\* | -10.8 % |
| Panamá | 179.0 | 162.7 | 180.9 | 177.7\* | 174.6\* | -2.5 % |
| **Promedio regional** | **183.4** | **176.5** | **191.2** | **192.8** | **194.6** | **+6.1 %** |


### ECO15 · Dependencia de importaciones netas

Importaciones netas sobre la oferta total. Positivo = importador neto; negativo = EXPORTADOR neto ese año (no es un error del dato).

> Nota metodológica: La línea punteada en 0 separa importadores (arriba) de exportadores netos (abajo).

**ECO15** · Unidad: % · Fórmula: (Importaciones − Exportaciones) ÷ (Producción bruta + Importaciones − Exportaciones) × 100

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | -4.6 | -8.6 | -6.2 | 2.9 | 1.8 | +6.3 pp |
| El Salvador | 9.2 | 16.5 | 4.6 | -4.8 | -0.5 | -9.7 pp |
| Guatemala | -0.6 | 0.2 | 2.8 | 6.1 | 5.4 | +5.9 pp |
| Honduras | 2.8 | 1.8 | 1.7 | 1.2 | 1.1 | -1.7 pp |
| Nicaragua | 21.9 | 19.3 | 19.9 | 14.6 | 15.0 | -6.9 pp |
| Panamá | -3.5 | -3.2 | -1.1 | -1.0 | -4.2 | -0.6 pp |
| **Promedio regional** | **4.2** | **4.3** | **3.6** | **3.2** | **3.1** | **-1.1 pp** |


## Dimensión ambiental


### ENV1 · Emisiones de GEI del sector eléctrico

Emisiones de gases de efecto invernadero (GEI) por la producción y uso de energía, per cápita y por unidad de PIB. Cubre las emisiones de las centrales eléctricas.

**ENV1_PC — Per cápita** · Unidad: t CO₂eq/habitante · Fórmula: Emisiones GEI de centrales eléctricas ÷ Población

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 0.0043 | 0.0010 | 0.0124 | 0.0331 | 0.0807 | +1783.4 % |
| El Salvador | 0.0936 | 0.0913 | 0.1253 | 0.2401 | 0.1857 | +98.4 % |
| Guatemala | 0.1923 | 0.2296 | 0.0885 | 0.1521 | 0.2125 | +10.5 % |
| Honduras | 0.2268 | 0.1706 | 0.2040 | 0.2595 | 0.2834 | +24.9 % |
| Nicaragua | 0.1288 | 0.1429 | 0.1567 | 0.2128 | 0.2106 | +63.4 % |
| Panamá | 0.2689 | 0.3309 | 0.2740 | 0.5004 | 0.5274 | +96.1 % |
| **Promedio regional** | **0.1525** | **0.1610** | **0.1435** | **0.2330** | **0.2501** | **+64.0 %** |

**ENV1_PIB — Por unidad de PIB** · Unidad: kg CO₂eq/USD constantes 2015 · Fórmula: Emisiones GEI (kg) ÷ PIB real (USD constantes 2015)

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 0.0003 | 0.0001 | 0.0009 | 0.0023 | 0.0054 | +1441.7 % |
| El Salvador | 0.0238 | 0.0208 | 0.0278 | 0.0518 | 0.0393 | +65.1 % |
| Guatemala | 0.0446 | 0.0499 | 0.0187 | 0.0316 | 0.0432 | -3.0 % |
| Honduras | 0.1022 | 0.0694 | 0.0811 | 0.1013 | 0.1085 | +6.2 % |
| Nicaragua | 0.0684 | 0.0695 | 0.0746 | 0.0983 | 0.0952 | +39.2 % |
| Panamá | 0.0202 | 0.0216 | 0.0163 | 0.0282 | 0.0293 | +44.9 % |
| **Promedio regional** | **0.0432** | **0.0386** | **0.0366** | **0.0522** | **0.0535** | **+23.7 %** |


### ENV2 · Contaminantes atmosféricos urbanos

Concentraciones ambientales de contaminantes atmosféricos en zonas urbanas: SO₂ y partículas emitidas por las centrales eléctricas, per cápita y por unidad de PIB.

**ENV2_SO2_PC — SO₂ per cápita** · Unidad: kg/habitante · Fórmula: Emisiones SO₂ de centrales eléctricas ÷ Población

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 0.048 | 0.009 | 0.121 | 0.336 | 0.364 | +665.2 % |
| El Salvador | 1.116 | 1.089 | 0.629 | 0.875 | 0.520 | -53.4 % |
| Guatemala | 1.529 | 1.806 | 0.702 | 1.247 | 1.732 | +13.3 % |
| Honduras | 2.598 | 1.992 | 2.406 | 3.056 | 3.182 | +22.5 % |
| Nicaragua | 1.513 | 1.660 | 1.703 | 1.928 | 1.921 | +27.0 % |
| Panamá | 0.413 | 0.548 | 1.216 | 2.330 | 1.997 | +383.8 % |
| **Promedio regional** | **1.203** | **1.184** | **1.130** | **1.629** | **1.619** | **+34.6 %** |

**ENV2_PAR_PC — Partículas per cápita** · Unidad: kg/habitante · Fórmula: Emisiones de partículas ÷ Población

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 0.0021 | 0.0004 | 0.0054 | 0.0149 | 0.0167 | +694.6 % |
| El Salvador | 0.0493 | 0.0481 | 0.0278 | 0.0385 | 0.0229 | -53.5 % |
| Guatemala | 0.0069 | 0.0055 | 0.0033 | 0.0101 | 0.0165 | +137.7 % |
| Honduras | 0.1148 | 0.0880 | 0.1062 | 0.1349 | 0.1385 | +20.7 % |
| Nicaragua | 0.0668 | 0.0733 | 0.0753 | 0.0858 | 0.0854 | +27.9 % |
| Panamá | 0.0182 | 0.0244 | 0.0543 | 0.1036 | 0.0873 | +378.5 % |
| **Promedio regional** | **0.0430** | **0.0399** | **0.0454** | **0.0646** | **0.0612** | **+42.3 %** |

**ENV2_SO2_PIB — SO₂ por PIB** · Unidad: g/USD constantes 2015 · Fórmula: Emisiones SO₂ (g) ÷ PIB real

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 0.0039 | 0.0007 | 0.0087 | 0.0233 | 0.0244 | +526.4 % |
| El Salvador | 0.2835 | 0.2480 | 0.1397 | 0.1887 | 0.1100 | -61.2 % |
| Guatemala | 0.3544 | 0.3926 | 0.1486 | 0.2590 | 0.3522 | -0.6 % |
| Honduras | 1.1702 | 0.8105 | 0.9558 | 1.1926 | 1.2187 | +4.1 % |
| Nicaragua | 0.8031 | 0.8073 | 0.8102 | 0.8907 | 0.8685 | +8.1 % |
| Panamá | 0.0311 | 0.0359 | 0.0726 | 0.1314 | 0.1110 | +257.3 % |
| **Promedio regional** | **0.4410** | **0.3825** | **0.3559** | **0.4476** | **0.4475** | **+1.5 %** |

**ENV2_PAR_PIB — Partículas por PIB** · Unidad: g/USD constantes 2015 · Fórmula: Emisiones de partículas (g) ÷ PIB real

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 0.00017 | 0.00003 | 0.00039 | 0.00103 | 0.00112 | +550.0 % |
| El Salvador | 0.01251 | 0.01094 | 0.00616 | 0.00832 | 0.00485 | -61.3 % |
| Guatemala | 0.00161 | 0.00119 | 0.00070 | 0.00211 | 0.00335 | +108.5 % |
| Honduras | 0.05170 | 0.03579 | 0.04220 | 0.05265 | 0.05305 | +2.6 % |
| Nicaragua | 0.03546 | 0.03565 | 0.03585 | 0.03962 | 0.03862 | +8.9 % |
| Panamá | 0.00137 | 0.00159 | 0.00324 | 0.00584 | 0.00485 | +253.5 % |
| **Promedio regional** | **0.01714** | **0.01420** | **0.01475** | **0.01826** | **0.01764** | **+2.9 %** |


### ENV3 · Emisiones atmosféricas del sistema

Emisiones de contaminantes atmosféricos procedentes de los sistemas energéticos, en escala eléctrica: gramos emitidos por cada kWh de producción bruta.

**ENV3 — Escala eléctrica** · Unidad: g/kWh · Fórmula: (SO₂ + NOx + CO + Partículas) ÷ Producción bruta

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 0.025 | 0.005 | 0.060 | 0.174 | 0.182 | +622.7 % |
| El Salvador | 1.340 | 1.283 | 0.760 | 1.029 | 0.672 | -49.9 % |
| Guatemala | 2.257 | 2.393 | 1.038 | 1.826 | 2.388 | +5.8 % |
| Honduras | 3.217 | 2.283 | 2.755 | 3.352 | 3.304 | +2.7 % |
| Nicaragua | 3.181 | 3.201 | 3.281 | 3.362 | 3.329 | +4.7 % |
| Panamá | 0.314 | 0.377 | 0.544 | 1.020 | 1.064 | +238.7 % |
| **Promedio regional** | **1.722** | **1.590** | **1.406** | **1.794** | **1.823** | **+5.9 %** |


### ENV6 · Biomasa vs Saldo MER (ilustrativo)

**Unidad:** GWh.

Comparativo de inyección de biomasa vs saldo neto en el Mercado Eléctrico Regional, por país. Saldo negativo = importador neto en el MER ese año.

> Nota metodológica: Indicador ilustrativo: contrasta dos series observadas, no calcula un cociente.

| País | Serie | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| Costa Rica | Inyección Biomasa | 58.6 | 67.3 | 55.5 | 55.2 | 59.9 |
| Costa Rica | Saldo MER | 506.1 | 1,002.7 | 719.8 | -361.6 | -231.3 |
| El Salvador | Inyección Biomasa | 1,099.3 | 1,250.0 | 1,104.6 | 1,064.5 | 1,056.1 |
| El Salvador | Saldo MER | -642.6 | -1,283.0 | -367.8 | 391.5 | 43.6 |
| Guatemala | Inyección Biomasa | 1,042.1 | 1,042.2 | 994.8 | 985.9 | 966.6 |
| Guatemala | Saldo MER | 973.9 | 1,035.0 | 772.1 | 846.6 | 795.6 |
| Honduras | Inyección Biomasa | 424.1 | 465.6 | 443.6 | 520.3 | 274.9 |
| Honduras | Saldo MER | -292.0 | -202.0 | -190.2 | -139.8 | -144.0 |
| Nicaragua | Inyección Biomasa | 468.9 | 588.7 | 578.8 | 601.0 | 602.5 |
| Nicaragua | Saldo MER | -1,070.7 | -1,005.2 | -1,062.2 | -817.2 | -976.7 |
| Panamá | Inyección Biomasa | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Panamá | Saldo MER | 482.9 | 439.5 | 157.6 | 143.3 | 538.6 |

## Dimensión social


### SOC1 · Población sin electricidad

Porcentaje de hogares (o de población) sin electricidad o energía comercial, o muy dependientes de energías no comerciales.

**SOC1** · Unidad: % · Fórmula: 100 − Tasa de electrificación total

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 0.60 | 0.60 | 0.60 | 0.60 | 0.60 | +0.0 pp |
| El Salvador | 2.20 | 2.10 | 1.80 | 1.70 | 1.70 | -0.5 pp |
| Guatemala | 10.10 | 10.74 | 10.06 | 9.61 | 9.11 | -1.0 pp |
| Honduras | 14.78 | 14.23 | 14.37 | 13.72 | 13.64 | -1.1 pp |
| Nicaragua | 1.50 | 0.91 | 0.74 | 0.59 | 0.44 | -1.1 pp |
| Panamá | 5.60 | 5.10 | 4.80 | 4.40 | 4.00 | -1.6 pp |
| **Promedio regional** | **5.80** | **5.61** | **5.39** | **5.10** | **4.92** | **-0.9 pp** |


### SOC2 · Ingreso destinado a electricidad

Porcentaje de ingresos de los hogares dedicado a combustibles y electricidad, para el hogar de ingreso promedio y para el quintil de menores ingresos.

> Nota metodológica: Guatemala: valores ~1000× menores que el resto del bloque (posible inconsistencia de unidades en la fuente); verificar con el equipo antes de interpretar.

**SOC2_PROM — Hogar promedio** · Unidad: % · Fórmula: Cargo anual de electricidad ÷ Ingreso anual promedio × 100

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 2.41 | 1.88 | 1.80 | 1.83 | 1.89 | -0.5 pp |
| El Salvador | 2.06 | 2.03 | 1.87 | 1.73 | 1.76 | -0.3 pp |
| Guatemala | 1.67 | 1.70 | 1.68 | 1.69 | 1.70 | +0.0 pp |
| Honduras | 5.10 | 5.14 | 5.88 | 6.30 | 6.55 | +1.5 pp |
| Nicaragua | 8.71 | 7.27 | 7.08 | 6.09 | 5.31 | -3.4 pp |
| Panamá | 0.81 | 0.75 | 0.80 | 0.78 | 0.87 | +0.1 pp |
| **Promedio regional** | **3.46** | **3.13** | **3.19** | **3.07** | **3.01** | **-0.4 pp** |

**SOC2_POBRE — Quintil más pobre** · Unidad: % · Fórmula: Cargo anual ÷ Ingreso anual del quintil más pobre × 100

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 21.72 | 15.75 | 14.82 | 15.35 | 13.97 | -7.7 pp |
| El Salvador | 7.24 | 7.55 | 7.01 | 6.91 | 7.23 | -0.0 pp |
| Guatemala | 6.23 | 6.34 | 6.23 | 6.29 | 6.33 | +0.1 pp |
| Honduras | 49.08 | 51.34 | 61.73 | 65.87 | 73.49 | +24.4 pp |
| Nicaragua | 22.79 | 19.02 | 18.53 | 15.92 | 13.91 | -8.9 pp |
| Panamá | 10.47 | 9.76 | 10.13 | 8.96 | 11.05 | +0.6 pp |
| **Promedio regional** | **19.59** | **18.29** | **19.74** | **19.88** | **21.00** | **+1.4 pp** |


### SOC3 · Hogares con acceso a energía renovable

Uso de energía en los hogares por grupo (rural/urbano) y combinación de combustibles: hogares con acceso eléctrico ponderado por la participación renovable de la generación.

> Nota metodológica: Proxy elaborado por el equipo: asume que el mix de la red es uniforme entre zonas.

**SOC3_RURAL — Rural** · Unidad: % · Fórmula: Tasa de electrificación rural × % renovable de la generación

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 99.6 | 99.8 | 97.8 | 94.3 | 88.9 | -10.7 pp |
| El Salvador | 80.0 | 80.5 | 74.6 | 58.8 | 66.6 | -13.4 pp |
| Guatemala | 61.2 | 60.1 | 65.1 | 55.8 | 50.3 | -11.0 pp |
| Honduras | 38.6 | 45.9 | 44.5 | 39.7 | 40.1 | +1.5 pp |
| Nicaragua | 50.9 | 50.5 | 47.8 | 42.7 | 37.8 | -13.1 pp |
| Panamá | 54.0 | 58.1 | 61.0 | 51.2 | 71.2 | +17.3 pp |
| **Promedio regional** | **64.1** | **65.8** | **65.1** | **57.1** | **59.1** | **-4.9 pp** |

**SOC3_URB — Urbano** · Unidad: % · Fórmula: Tasa de electrificación urbana × % renovable de la generación

| País | 2020 | 2021 | 2022 | 2023 | 2024 | Δ 2020→2024 |
|---|---|---|---|---|---|---|
| Costa Rica | 99.7 | 99.8 | 99.1 | 94.3 | 88.9 | -10.8 pp |
| El Salvador | 83.4 | 83.5 | 76.8 | 60.5 | 67.1 | -16.3 pp |
| Guatemala | 72.4 | 69.3 | 75.9 | 64.3 | 57.6 | -14.8 pp |
| Honduras | 54.8 | 58.4 | 56.5 | 49.3 | 49.2 | -5.6 pp |
| Nicaragua | 69.8 | 69.2 | 65.6 | 58.6 | 51.8 | -18.0 pp |
| Panamá | 64.8 | 68.4 | 67.2 | 54.6 | 73.0 | +8.2 pp |
| **Promedio regional** | **74.2** | **74.8** | **73.5** | **63.6** | **64.6** | **-9.6 pp** |


## Trazabilidad

Los valores de este documento se calculan con las fórmulas indicadas a
partir de las variables base del pipeline (`data/processed/`), en
unidades homologadas: energía en kWh, PIB y valor agregado industrial en
USD constantes de 2015, tarifa en USD corrientes/MWh. Las mismas cifras,
con sus tablas de datos base, pueden auditarse en los visualizadores del
proyecto (`graficos/`). La versión máquina de esta matriz está en
`data/processed/indicadores_consolidados_tidy.csv`.

\* Valor imputado vía CAGR (no observación directa de la fuente).
