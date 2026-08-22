# Salidas oficiales de la tesis

Esta es la única carpeta de entrega de la fase cuantitativa que alimenta la
monografía.

- `figuras/`: 22 figuras PNG regionales, numeradas de forma sugerida en
  `manifiesto_figuras.csv`.
- `tablas/`: documento HTML consolidado con 75 tablas APA 7, versión sin notas
  e índice; cada fila del índice enlaza al ancla de su tabla. Incluye además la
  Tabla 7 regional de SOC2 usada en el cuerpo de la tesis.
- `manifiesto.csv`: inventario conjunto de figuras y tablas con rutas
  relativas, títulos, códigos y criterio de agregación o sección. Las tablas
  apuntan al HTML consolidado mediante fragmentos `#tabla-NN`, no a copias
  individuales.

Todo el contenido se regenera desde la raíz del repositorio:

```bash
python src/run_pipeline.py
```

No edite manualmente una cifra o leyenda de esta carpeta. Corrija el dato,
`FICHAS` o el generador correspondiente y vuelva a ejecutar el pipeline.

La numeración de figuras es una ayuda para insertar los archivos siguiendo el
índice vigente de la tesis; el documento final conserva la autoridad sobre la
numeración definitiva.
