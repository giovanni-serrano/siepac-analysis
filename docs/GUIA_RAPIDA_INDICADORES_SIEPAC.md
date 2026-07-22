## Indicadores ECO y SOC a nivel SIEPAC

Qué indicadores ya se pueden usar "a nivel SIEPAC", cómo se
calcularon, qué hipótesis sugieren y qué gráfico los ilustra.
Cifras: `graficos/region/tabla_agregados.csv`. Figuras: `graficos/region/`.

---

## Matematica

> **"A nivel SIEPAC" = agregado regional (razón de sumas), NUNCA promedio simple.**

- **Agregado regional** = Σ numerador ÷ Σ denominador de los 6 países.
  Es aplicar la fórmula IEDS al bloque como si fuera un solo país.
- **Promedio de países** = media simple (peso 1/6). Responde otra pregunta
  ("el país típico"). Solo para comparar países entre sí.
- Pueden divergir mucho. Ejemplo: SOC1 2024 es **6.72 %** del bloque, no 4.92 %.
  La diferencia son 940 mil personas.

## Cómo leer los gráficos (aplica a todos los `*_agregado_vs_promedio.png`)

- **Tipo:** líneas 2020–2024, dos series.
- **Azul gruesa** = agregado regional → la cifra que se cita en la tesis.
- **Gris punteada** = promedio de países → referencia de contraste.
- **Por qué líneas:** el objeto de análisis es la *tendencia* del bloque en 5
  años; dos líneas muestran además cuánto sesga el promedio simple.
- El valor 2024 va etiquetado sobre cada línea.

---

## ✅ Validados a nivel SIEPAC (listo para usar)

### ECO1 · Uso de energía per cápita

- **Cálculo:** Σ consumo final (kWh) ÷ Σ población. **959 → 1 063 kWh/hab (+10.9 %).**
- **Hipótesis:** la demanda eléctrica del bloque crece más rápido que su
  población. La región se electrifica de forma sostenida.
- **Gráfico:** `ECO1_agregado_vs_promedio.png`. Complemento en magnitud:
  `REGION_consumo_final.png` (47.6 → 55.4 TWh).

### ECO2 · Energía por unidad de PIB

- **Cálculo:** Σ consumo final ÷ Σ PIB (USD 2015). **0.195 → 0.179 kWh/USD (−8.3 %).**
- **Hipótesis:** desacople incipiente: la economía del bloque crece más rápido
  que su consumo eléctrico. Señal positiva de eficiencia macro.
- **Gráfico:** `ECO2_agregado_vs_promedio.png`.

### ECO3 · Eficiencia de conversión y distribución

- **Cálculo:** Σ consumo final ÷ Σ producción bruta × 100. **82.4 → 82.6 % (+0.2 pp).**
- **Hipótesis:** estancamiento: la brecha (~17 %, pérdidas + autoconsumo) no
  mejoró en 5 años. Ojo: el promedio simple sugiere *caída* (−0.9 pp) — usar el
  agregado.
- **Gráfico:** `ECO3_agregado_vs_promedio.png`.

### ECO6 · Intensidad energética de la industria

- **Cálculo:** Σ consumo industrial ÷ Σ valor agregado industrial. **0.370 → 0.497 kWh/USD (+34.4 %).**
- **Hipótesis:** la industria del bloque genera menos valor por kWh: se
  electrifica más rápido de lo que crece su valor agregado. Discutir causas con
  el equipo (¿electrificación de procesos o VAI débil?).
- **Gráfico:** `ECO6_agregado_vs_promedio.png`.

### ECO11 · Fósiles en la electricidad

- **Cálculo:** Σ generación fósil ÷ Σ generación total × 100. **25.0 → 33.0 % (+8.0 pp).**
- **Hipótesis:** retroceso: el bloque quemó más térmica, con salto en 2023
  (13.8 → 21.5 TWh fósiles; consistente con año seco e hidro a la baja).
- **Gráfico:** `ECO11_agregado_vs_promedio.png` +
  `REGION_renovable_vs_fosil.png` (barras apiladas: magnitud y % en una vista).

### ECO13 · Renovables en la electricidad

- **Cálculo:** espejo de ECO11. **75.0 → 67.0 % (−8.0 pp).**
- **Hipótesis:** el bloque sigue siendo mayoritariamente renovable, pero perdió
  8 pp en 5 años. La matriz es vulnerable a la hidrología.
- **Gráfico:** `ECO13_agregado_vs_promedio.png` +
  `REGION_generacion_fuentes.png` (6 paneles, mismo eje: hidro domina, fósil
  crece, solar/eólica aún marginales).

### ECO15 · Dependencia de importaciones netas ⚠ interpretar bien

- **Cálculo:** Σ(imp − exp) ÷ Σ oferta × 100. **1.65 → 2.17 % (+0.5 pp, +31 %).**
- **CLAVE:** al sumar el bloque, el comercio interno del MER se cancela.
  El agregado mide **dependencia EXTRARREGIONAL** (≈ México→Guatemala).
- **Hipótesis:** el bloque casi duplicó su compra neta al exterior
  (0.97 → 1.49 TWh). El promedio simple dice lo contrario (−26 %): es el caso
  demostrativo de por qué el método importa (paradoja de agregación).
- **Gráfico:** `ECO15_agregado_vs_promedio.png` (la divergencia se ve sola) +
  `REGION_intercambios.png` (Σimp, Σexp y saldo neto en TWh).

### SOC1 · Población sin electricidad

- **Cálculo:** media de % nacionales ponderada por población
  (= personas sin luz ÷ población del bloque). **7.57 → 6.72 % (−0.8 pp).**
- **Hipótesis:** el acceso avanza pero lento (~0.2 pp/año). Quedan
  **3.50 millones** de personas sin electricidad, concentradas en Guatemala y
  Honduras (90 % del total).
- **Gráfico:** `SOC1_agregado_vs_promedio.png` +
  `REGION_personas_sin_electricidad.png` (barras: personas son magnitud
  absoluta, las barras comunican "cuántos", no tendencia relativa).

---

## Ejemplo de cálculo tipo — SOC1, año 2024

Este ejemplo se detalla **una sola vez** en la tesis y respalda todos los
agregados validados: solo cambian numerador y denominador según la ficha de
cada indicador (ver "Cálculo" en cada bloque de arriba).

**De dónde salen los datos:**

- **% sin electricidad** por país: hoja "SOC 1" de `SOCs.xlsx` (equipo de
  tesis) = 100 − tasa de electrificación total.
  Procesado: `data/processed/indicadores_SOC_SIEPAC.xlsx`.
- **Población** por país: CEPALSTAT (CEPAL-CELADE), "Población total por
  sexo", ambos sexos, miles de habitantes a mitad de año.
  Raw + ficha técnica: `data/raw/poblacion_total/`.
  Procesado: `data/processed/poblacion_total.csv`.
- Las **personas sin electricidad** no son dato observado: se calculan
  (% × población).

**Paso 1 — personas sin electricidad por país** (N_i = I_i × D_i ÷ 100):

| País | I_i = % sin elec. | D_i = población | N_i = personas |
|---|---:|---:|---:|
| Costa Rica | 0.60 % | 5 129 900 | 30 779 |
| El Salvador | 1.70 % | 6 338 200 | 107 749 |
| Guatemala | 9.11 % | 18 406 400 | 1 676 823 |
| Honduras | 13.64 % | 10 825 700 | 1 476 626 |
| Nicaragua | 0.443 % | 6 916 100 | 30 638 |
| Panamá | 4.00 % | 4 515 600 | 180 624 |
| **Σ** | | **52 131 900** | **3 503 240** |

**Paso 2 — agregado regional (razón de sumas):**

> SOC1_SIEPAC = Σ N_i ÷ Σ D_i = 3 503 240 ÷ 52 131 900 × 100 = **6.72 %**

**Paso 3 — contraste con el promedio simple (control):**

> Ī = (0.60 + 1.70 + 9.11 + 13.64 + 0.443 + 4.00) ÷ 6 = 4.92 %

4.92 % ≠ 6.72 % porque los países grandes (Guatemala, Honduras) tienen los %
más altos y la media simple los pesa igual que a los pequeños. El agregado es
la cifra correcta para "el bloque": equivale a contar personas.

**Para replicar en otro indicador:** sustituir N y D según su fórmula
(ej. ECO1: N = consumo final kWh, D = población → 55.4 TWh ÷ 52.13 M hab =
1 063 kWh/hab). Verificación automática: `graficos/region/tabla_agregados.csv`.

---

## ❌ NO validados a nivel SIEPAC (no citar cifra regional)

| Indicador | Por qué no | Estado |
|---|---|---|
| **ECO14** (tarifa) | Sin MWh regulados para ponderar. Y 2023–2024 es 100 % imputación CAGR, no dato. | Solo promedio de países, con nota. Solución propuesta: ponderar por consumo final (proxy) + buscar tarifas reales 2023–24. |
| **SOC2** (% ingreso en electricidad) | Insumos en moneda local, sin nº de hogares. Guatemala con anomalía ~1000× **sin resolver**. | Bloqueado hasta aclarar Guatemala con el equipo. |
| **SOC3** (acceso renovable rural/urb.) | Falta población rural/urbana para ponderar. | Arreglable: dato público (Banco Mundial SP.RUR/URB.TOTL) + ETL pequeño. |

---

*Metodología completa: `docs/resumen_indicadores_SIEPAC.md`, sección "Cómo leer
este documento". Respaldo formal: el agregado es la única agregación
consistente con la definición IEDS; difiere del promedio en n·Cov(peso, valor)
— con tamaño y desempeño correlacionados (como en CA) el promedio simple
sesga, y puede invertir tendencias (Yule–Simpson, caso ECO15).*
