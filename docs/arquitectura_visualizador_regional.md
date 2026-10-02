# Arquitectura del visualizador regional SIEPAC

## Estado y propósito

Este documento es el contrato de diseño de la aplicación pública única,
`graficos/visualizador_siepac.html`. El visualizador regional sustituyó el
panel y el explorador anteriores después de alcanzar paridad funcional. El
contrato preserva las decisiones útiles de la antigua exploración
`version-alt/` sin conservar su código, sus gráficos duplicados ni sus
supuestos desactualizados.

La aplicación debe comunicar la misma lectura cuantitativa que la tesis:
evaluar el SIEPAC como bloque en 2020–2024, permitir la comparación entre los
seis países y explicar con transparencia cómo se calculó cada indicador.

## Autoridad de datos y redacción

El visualizador será una salida generada. No se editarán cifras, unidades,
fórmulas ni notas directamente en el HTML.

- `src/metadatos_indicadores.py`, diccionario `FICHAS`: nombres, unidades, fórmulas y notas
  metodológicas de los 15 indicadores IEDS.
- `src/presentacion_indicadores.py`: formato de las fichas públicas;
  `viz_comun.py` conserva la paleta y las reexportaciones compatibles.
- `src/resultados_indicadores.py`: lectura de CSV ECO y de los tres JSON
  intermedios regenerables; no relee los libros Excel generados.
- `data/processed/`: matrices y series que alimentan los cálculos.
- `salidas/tesis/figuras/` y `salidas/tesis/tablas/`: productos oficiales
  enlazados mediante nombres deterministas e índice de tablas.
- Documento final de la tesis: autoridad sobre la selección, interpretación y
  numeración definitiva de las salidas que aparecen en el texto.
- ECO-CG se presentará como serie económica complementaria, separada de los 15
  IEDS, nunca como un indicador IEDS adicional.

## Producto único

La meta es generar un único archivo autocontenido:

```text
src/generar_visualizador.py
        ↓
graficos/visualizador_siepac.html
```

Ese producto absorbe la función ejecutiva del panel y la función documental
del explorador. No se recomienda crear otro repositorio: el historial y la
trazabilidad de este proyecto son activos profesionales.

## Arquitectura de información

1. **Inicio regional.** Resumen del bloque por dimensión y selector 2020–2024.
2. **Dimensión.** Económica, social o ambiental, con sus indicadores y lectura
   sintética de nivel, tendencia y heterogeneidad.
3. **Detalle del indicador.** Tres vistas coordinadas:
   - **Región:** agregado del bloque, promedio de países, banda mínimo–máximo
     y una conclusión sintética tomada de los resultados de la tesis.
   - **Países:** comparación nacional y, cuando aporte valor, pequeños
     múltiplos con igual prominencia visual.
   - **Datos y método:** tabla accesible, fórmula, unidad, fuente, cobertura,
     descarga y advertencias.
4. **Acerca de los datos.** Alcance, reproducibilidad, fuentes y enlace a las
   salidas oficiales de la tesis.

La navegación inicial será regional. La comparación por país será contexto y
detalle, no el punto de entrada ni un ranking implícito.

## Gramática visual

- Agregado regional por razón de sumas: línea sólida y mayor jerarquía.
- Promedio simple de países: línea discontinua y etiqueta explícita.
- Dispersión nacional: banda mínimo–máximo con transparencia suficiente para no
  ocultar las líneas de referencia.
- Países: paleta de igual prominencia; ninguna nación se presenta como valor
  normativo del bloque.
- El orden narrativo será agregado regional, promedio de países, dispersión y
  detalle nacional.
- No se llamará «regional» al promedio simple. Si una serie no admite agregado,
  la interfaz mostrará la ausencia y su causa, no una aproximación silenciosa.
- Los indicadores principales no serán «país máximo» y «país mínimo»; se
  priorizarán nivel regional, cambio 2020–2024 y dispersión entre países.

## Reglas especiales por indicador

- **ECO14:** no tiene agregado regional. Debe distinguir datos observados de
  imputaciones CAGR y advertir que 2023–2024 es totalmente imputado.
- **ECO15:** los valores negativos identifican exportadores netos; no son un
  error ni deben recodificarse.
- **SOC2:** debe mostrar SOC2_PROM, SOC2_VULNERABLE y su brecha. El agregado es
  la razón de sumas de costos e ingresos de los hogares; se mantendrá la nota de
  proxy y la heterogeneidad de sus insumos.
- **SOC3:** los agregados rural y urbano se ponderan por sus poblaciones
  respectivas.
- **ENV6:** compara dos series observadas; no se representará como cociente.
- **ECO-CG:** tendrá rotulación y sección de serie complementaria.

## Contrato mínimo de datos

Cada serie entregada a la interfaz debe exponer, como mínimo:

```text
codigo, dimension, serie, unidad, anios, paises,
promedio_paises, agregado_regional, minimo, maximo,
fuente, cobertura, nota_metodologica
```

`agregado_regional` puede ser nulo, pero debe incluir el motivo. Los datos
embebidos se construirán una sola vez para evitar duplicar cargas y lógica entre
componentes.

## Accesibilidad y presentación

- HTML semántico, navegación completa con teclado y foco visible.
- Contraste mínimo de 4.5:1 para texto normal y 3:1 para elementos gráficos.
- El color nunca será el único canal: líneas, marcadores y etiquetas reforzarán
  la distinción entre series.
- Diseño adaptable desde 360 px y tablas con encabezados asociados.
- Texto alternativo o resumen equivalente para cada gráfico.
- Descarga de los datos visibles en CSV y enlace directo a la tabla o figura
  correspondiente en `salidas/tesis/`.
- Formato numérico, abreviaturas y unidades coherentes con las tablas APA 7.

## Reproducibilidad y publicación

- El generador formará parte de `src/run_pipeline.py`.
- La aplicación se reconstruirá desde los datos procesados y `FICHAS`; no
  dependerá de copias manuales de JSON, PNG o texto.
- Un solo paquete de la biblioteca gráfica se incluirá en el HTML.
- El HTML autocontenido será apto para GitHub Pages y para consulta sin conexión.
- GitHub Pages publica mediante una lista permitida únicamente el visualizador
  y sus salidas documentales, después de aprobar las pruebas del clon público.
  Solo `main` despliega; el workflow no ejecuta los ETL sin las fuentes.

## Criterios de aceptación

- Contiene los 15 IEDS y separa con claridad ECO-CG.
- Abre en la vista regional y diferencia agregado, promedio y rango.
- Reproduce exactamente las cifras y advertencias vigentes de la tesis.
- No conserva nombres antiguos de SOC2 ni afirma que SOC2 o SOC3 carecen de
  agregado regional.
- ECO14, SOC2, SOC3, ENV6 y ECO15 pasan comprobaciones específicas.
- Todos los enlaces a figuras y tablas oficiales existen tras clonar el repo.
- Funciona con teclado, en móvil y sin conexión.
- No duplica el mismo conjunto de datos o la biblioteca gráfica entre vistas.

## Secuencia de migración

1. **Completado:** crear el contrato de datos y comprobaciones estructurales.
2. **Completado:** implementar navegación regional y detalle para los 15 IEDS
   y ECO-CG, con vistas de región, países, datos y método.
3. **Completado:** validar la paridad con la tesis y retirar el panel y el
   explorador anteriores.
4. **Completado:** añadir conclusiones regionales y preparar la publicación
   controlada en GitHub Pages.

Las decisiones rescatadas de `version-alt/` son la prioridad regional, la banda
mínimo–máximo, la separación entre agregado y promedio, los pequeños múltiplos
y la accesibilidad. Se descartan su código duplicado, sus 88 PNG y sus notas
anteriores a los agregados regionales vigentes.
