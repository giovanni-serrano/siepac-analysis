# Manifiesto de datos crudos

Generado automáticamente por `src/generar_manifiesto_raw.py` el 2026-08-03 a partir de `src/catalogo_datos_raw.py` — no editar a mano.

Documenta, para cada variable de entrada del pipeline, de dónde se descarga, si su fuente permite redistribuir el archivo y el hash SHA-256 de la copia con la que se verificaron los cálculos de este proyecto. Después de descargar un archivo, correr `python src/verificar_datos_raw.py` compara la copia local con el hash registrado y detecta cambios en el archivo de origen.

No cubre `data/raw_equipo/` (matrices de entrada del estudio) ni las fichas técnicas en PDF (documentación de referencia, no entradas del pipeline).

| Variable | Fuente | ¿Redistribuible? | En este repositorio |
|---|---|---|---|
| Consumo final total de electricidad | OLADE / SIELAC | **No** (verificado) | No — ver más abajo |
| Consumo final de electricidad de la industria | OLADE / SIELAC | **No** (verificado) | No — ver más abajo |
| Generación eléctrica por tipo de fuente | OLADE / SIELAC | **No** (verificado) | No — ver más abajo |
| Matriz de balance energético (importaciones/exportaciones) | OLADE / SIELAC | **No** (verificado) | No — ver más abajo |
| Producción bruta de electricidad | OLADE / SIELAC | **No** (verificado) | No — ver más abajo |
| PIB real (USD constantes de 2015) | Banco Mundial (WDI) | **Sí** (CC-BY 4.0) | Sí |
| Población rural y urbana | Banco Mundial (WDI) | **Sí** (CC-BY 4.0) | Sí |
| Población total | CEPALSTAT (CEPAL-CELADE) | **No** (verificado) | No — ver más abajo |
| Precio medio de la electricidad | CEPALSTAT | **No** (verificado) | No — ver más abajo |
| Valor agregado manufacturero (% del PIB, ODS 9.2.1) | agenda2030lac (ODS-NU / UNIDO) | **No** (verificado) | No — ver más abajo |

Los archivos marcados **No** no están en este repositorio: los términos de sus fuentes prohíben redistribuir el archivo descargado. OLADE/SIELAC veda el «almacenamiento en cualquier otro sistema» y la «distribución por cualquier medio»; CEPAL permite bajar y copiar sus materiales «para su uso personal, sin fines comerciales, sin ningún derecho a revender, redistribuir, o crear otros trabajos a partir de los mismos» (agenda2030lac lo opera CEPAL y hereda ese acuerdo). Ambos verificados el 2026-07-26; las citas completas están en `src/catalogo_datos_raw.py`.

El uso analítico conserva la atribución de procedencia. Los archivos descargados no se republican; el pipeline utiliza copias locales obtenidas desde la ruta indicada en cada ficha.

## Fichas por variable


### `data/raw/consumo_final_total/`

- **Variable:** Consumo final total de electricidad
- **Fuente:** OLADE / SIELAC
- **¿Redistribuible?:** **No** (verificado)
- **Cobertura:** 6 países SIEPAC, 2020-2024
- **Patrón que localiza el ETL:** `*.xlsx` (el nombre exacto cambia en cada descarga: los exports llevan timestamp)
- **Dónde descargarlo:** SIELAC / Estadísticas Energéticas de ALC / Reportes / Oferta y demanda / Series de oferta y demanda (filtrar: 6 países SIEPAC, 2020/2024, consumo final total, electricidad)
- **SHA-256 de la copia verificada:** `ba835b419233242d39d0208f3c1b16adabf4c3c264554073ecd8e6a3b0b0ae8b`
- **Tamaño de esa copia:** 20,036 bytes

### `data/raw/consumo_industrial/`

- **Variable:** Consumo final de electricidad de la industria
- **Fuente:** OLADE / SIELAC
- **¿Redistribuible?:** **No** (verificado)
- **Cobertura:** 6 países SIEPAC, 2020-2024
- **Patrón que localiza el ETL:** `*.xlsx` (el nombre exacto cambia en cada descarga: los exports llevan timestamp)
- **Dónde descargarlo:** SIELAC / Estadísticas Energéticas de ALC / Reportes / Oferta y demanda / Series de oferta y demanda (filtrar: 6 países SIEPAC, 2020/2024, industrial, electricidad)
- **SHA-256 de la copia verificada:** `c2b48d33cabbc54f308e82c7b8669eecf9225588cf31584701bc884c1d56b31f`
- **Tamaño de esa copia:** 20,005 bytes

### `data/raw/generacion_por_tipo_de_fuente/`

- **Variable:** Generación eléctrica por tipo de fuente
- **Fuente:** OLADE / SIELAC
- **¿Redistribuible?:** **No** (verificado)
- **Cobertura:** 6 países SIEPAC, 2020-2024
- **Patrón que localiza el ETL:** `*.xlsx` (el nombre exacto cambia en cada descarga: los exports llevan timestamp)
- **Dónde descargarlo:** SIELAC / Estadísticas Energéticas de ALC / Reportes / Oferta y demanda / Eléctrico / Generación eléctrica por fuente - Anual (filtrar: 6 países, 2020-2024)
- **SHA-256 de la copia verificada:** `33eaf042c918c9bac2b4216c899c6d632bc9a386808f54cb1ceafe65a5361e6f`
- **Tamaño de esa copia:** 41,601 bytes

### `data/raw/importaciones_exportaciones/`

- **Variable:** Matriz de balance energético (importaciones/exportaciones)
- **Fuente:** OLADE / SIELAC
- **¿Redistribuible?:** **No** (verificado)
- **Cobertura:** 6 países SIEPAC, 2020-2024
- **Patrón que localiza el ETL:** `*.xlsx` (el nombre exacto cambia en cada descarga: los exports llevan timestamp)
- **Dónde descargarlo:** SIELAC / Estadísticas Energéticas de ALC / Reportes / Oferta y demanda / Matriz de balance energético (organizar por: eléctrico, 6 países, 2020-2024)
- **SHA-256 de la copia verificada:** `4648cca681b3c7c2b30ed1578b3aff479312b1b2c14d7bbe95e29abdaacb2d05`
- **Tamaño de esa copia:** 189,229 bytes

### `data/raw/produccion_bruta/`

- **Variable:** Producción bruta de electricidad
- **Fuente:** OLADE / SIELAC
- **¿Redistribuible?:** **No** (verificado)
- **Cobertura:** 6 países SIEPAC, 2020-2024
- **Patrón que localiza el ETL:** `*.xlsx` (el nombre exacto cambia en cada descarga: los exports llevan timestamp)
- **Dónde descargarlo:** SIELAC / Estadísticas Energéticas de ALC / Reportes / Oferta y demanda / Series de oferta y demanda (organizar por: eléctrico, 6 países, 2020-2024)
- **SHA-256 de la copia verificada:** `0135cdc16ba6e75926582aea409f02d1b53761693b0dabb16a918127b5136d4a`
- **Tamaño de esa copia:** 25,926 bytes

### `data/raw/pib/`

- **Variable:** PIB real (USD constantes de 2015)
- **Fuente:** Banco Mundial (WDI)
- **¿Redistribuible?:** **Sí** (CC-BY 4.0)
- **Cobertura:** Todos los países, serie histórica completa
- **Patrón que localiza el ETL:** `*.csv` (el nombre exacto cambia en cada descarga: los exports llevan timestamp)
- **Dónde descargarlo:** datos.bancomundial.org/indicador/NY.GDP.MKTP.KD (descarga completa, se filtra en el ETL)
- **SHA-256 de la copia verificada:** `4caefd74bb19ed6cc827a116f555ee8a0535ce24bca8bca225cef3368f94b0d4`
- **Tamaño de esa copia:** 301,964 bytes

### `data/raw/poblacion_rural_urbana/`

- **Variable:** Población rural y urbana
- **Fuente:** Banco Mundial (WDI)
- **¿Redistribuible?:** **Sí** (CC-BY 4.0)
- **Cobertura:** 6 países SIEPAC, 2020-2024
- **Patrón que localiza el ETL:** `*.csv` (el nombre exacto cambia en cada descarga: los exports llevan timestamp)
- **Dónde descargarlo:** datos.bancomundial.org/indicador/SP.RUR.TOTL y datos.bancomundial.org/indicador/SP.URB.TOTL (filtrar: 6 países SIEPAC, 2020-2024)
- **SHA-256 de la copia verificada:** `e59daec091a133f8f16c1b825a3576b72fcd67febcc7327779c984adb6c2f8fe`
- **Tamaño de esa copia:** 1,388 bytes

### `data/raw/poblacion_total/`

- **Variable:** Población total
- **Fuente:** CEPALSTAT (CEPAL-CELADE)
- **¿Redistribuible?:** **No** (verificado)
- **Cobertura:** 6 países SIEPAC, 2020-2024
- **Patrón que localiza el ETL:** `*.xlsx` (el nombre exacto cambia en cada descarga: los exports llevan timestamp)
- **Dónde descargarlo:** CEPALSTAT / Estadísticas e indicadores / Población / Estimaciones y proyecciones de población / Población total por sexo (filtrar: 6 países SIEPAC, 2020-2024, ambos sexos; hoja "datos" del export, valores en miles de habitantes)
- **SHA-256 de la copia verificada:** `707881f9cdef002f1f982a1a42d89a33d4f77de5d220c52089afba8eb533acba`
- **Tamaño de esa copia:** 10,695 bytes

### `data/raw/tarifa_electrica_media/`

- **Variable:** Precio medio de la electricidad
- **Fuente:** CEPALSTAT
- **¿Redistribuible?:** **No** (verificado)
- **Cobertura:** 6 países SIEPAC, 2020-2024
- **Patrón que localiza el ETL:** `*.xlsx` (el nombre exacto cambia en cada descarga: los exports llevan timestamp)
- **Dónde descargarlo:** statistics.cepal.org/portal/cepalstat/dashboard.html?indicator_id=4758&area_id=2454&lang=es (filtrar: 6 países SIEPAC y años disponibles)
- **SHA-256 de la copia verificada:** `5f847978bc5838a7e24f6e3d82be7623b87b4de3d92339261c8b24e299d68adf`
- **Tamaño de esa copia:** 10,730 bytes

### `data/raw/valor_agregado_industrial/`

- **Variable:** Valor agregado manufacturero (% del PIB, ODS 9.2.1)
- **Fuente:** agenda2030lac (ODS-NU / UNIDO)
- **¿Redistribuible?:** **No** (verificado)
- **Cobertura:** 6 países SIEPAC, 2020-2024
- **Patrón que localiza el ETL:** `*.xlsx` (el nombre exacto cambia en cada descarga: los exports llevan timestamp)
- **Dónde descargarlo:** agenda2030lac.org/estadisticas/banco-datos-regional-seguimiento-ods.html?indicator_id=4353&lang=es
- **SHA-256 de la copia verificada:** `97f92db3fd94eb0f19fb6dd89ce8f0729618101db79739f0ecea68c0849e8ba1`
- **Tamaño de esa copia:** 9,484 bytes
