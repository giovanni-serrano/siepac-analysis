"""
catalogo_datos_raw.py — Catálogo de los archivos crudos que alimentan los ETL
====================================================
Etapa del pipeline : configuración (módulo común, no se ejecuta directo)
Entradas           : —
Salidas            : — (lo usan generar_manifiesto_raw.py y verificar_datos_raw.py)

Fuente única de verdad de qué archivo espera cada ETL dentro de
data/raw/<variable>/, en qué reporte del portal de origen se descarga y
qué hash SHA-256 tenía la copia con la que se verificó el pipeline.

No incluye data/raw_equipo/ (entregables propios del equipo, no datos de
una fuente externa) ni las fichas técnicas en PDF (documentación, no
entrada del pipeline).

Notas metodológicas:
  - De las nueve fuentes, ocho NO viven en el repositorio porque sus
    términos prohíben redistribuir el archivo descargado. Siguen siendo
    el insumo real del pipeline: cada quien descarga su propia copia y
    `verificar_datos_raw.py` confirma que es la misma con la que se
    calculó todo, comparando el hash.
  - OLADE/SIELAC (consumo_final_total, consumo_industrial,
    generacion_por_tipo_de_fuente, importaciones_exportaciones,
    produccion_bruta): sus Términos y Condiciones prohíben expresamente
    el "almacenamiento en cualquier otro sistema" y la "distribución por
    cualquier medio" (verificado el 2026-07-26 en
    https://sielac.olacde.org/WebForms/Utilidades/contenido.aspx?archivo=contenido5.1.html).
  - CEPALSTAT y agenda2030lac (poblacion_total, tarifa_electrica_media,
    valor_agregado_industrial): el acuerdo de uso del sitio de CEPAL
    permite bajar y copiar los materiales "para su uso personal, sin
    fines comerciales, sin ningún derecho a revender, redistribuir, o
    crear otros trabajos a partir de los mismos" (verificado el
    2026-07-26 en https://www.cepal.org/es/terminos-y-condiciones-sobre-el-uso-del-sitio-web-entre-la-cepal-y-el-usuario).
    agenda2030lac lo opera CEPAL y no publica términos propios, así que
    hereda ese acuerdo. No se encontró una licencia abierta explícita
    para los datos de CEPALSTAT pese a que el portal se promociona como
    datos abiertos y ofrece API pública.
    Sobre la cláusula de "crear otros trabajos": leída al pie de la letra
    prohibiría el análisis mismo, lo que contradice la misión del
    organismo, su API para desarrolladores y la práctica académica de
    citar estadísticas oficiales. Se interpreta como lenguaje de sitio
    web referido a contenidos y publicaciones, no como impedimento para
    calcular indicadores a partir de datos citados. Lo inequívoco, y lo
    que se acata aquí, es la prohibición de redistribuir los archivos.
  - Banco Mundial (pib): CC-BY 4.0, redistribuible con atribución
    (verificado el 2026-07-26 en
    https://datacatalog.worldbank.org/public-licenses). Es la única
    fuente cruda que sí se versiona.
  - Los nombres de archivo llevan un timestamp de exportación (cambian en
    cada descarga); por eso los ETL localizan el archivo por patrón glob
    (`*.xlsx`), no por nombre exacto.

Autor: Luis Giovanni Serrano Bello — Tesis SIEPAC, UNI Nicaragua
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ArchivoRaw:
    carpeta: str            # subcarpeta bajo data/raw/
    patron: str              # patrón glob que usa el ETL para localizarlo
    variable: str            # qué mide
    fuente: str               # organización que lo publica
    redistribuible: str      # "no" | "si" (verificado; ver notas de arriba)
    ruta_navegacion: str     # cómo llegar al reporte en el portal de origen
    sha256: str               # hash de la copia verificada por este pipeline
    tamano_bytes: int
    cobertura: str            # periodo/países que cubre el extracto


CATALOGO_RAW = [
    ArchivoRaw(
        carpeta="consumo_final_total", patron="*.xlsx",
        variable="Consumo final total de electricidad",
        fuente="OLADE / SIELAC", redistribuible="no",
        ruta_navegacion="SIELAC / Estadísticas Energéticas de ALC / Reportes "
                        "/ Oferta y demanda / Series de oferta y demanda "
                        "(filtrar: 6 países SIEPAC, 2020/2024, consumo final "
                        "total, electricidad)",
        sha256="ba835b419233242d39d0208f3c1b16adabf4c3c264554073ecd8e6a3b0b0ae8b",
        tamano_bytes=20036, cobertura="6 países SIEPAC, 2020-2024",
    ),
    ArchivoRaw(
        carpeta="consumo_industrial", patron="*.xlsx",
        variable="Consumo final de electricidad de la industria",
        fuente="OLADE / SIELAC", redistribuible="no",
        ruta_navegacion="SIELAC / Estadísticas Energéticas de ALC / Reportes "
                        "/ Oferta y demanda / Series de oferta y demanda "
                        "(filtrar: 6 países SIEPAC, 2020/2024, industrial, "
                        "electricidad)",
        sha256="c2b48d33cabbc54f308e82c7b8669eecf9225588cf31584701bc884c1d56b31f",
        tamano_bytes=20005, cobertura="6 países SIEPAC, 2020-2024",
    ),
    ArchivoRaw(
        carpeta="generacion_por_tipo_de_fuente", patron="*.xlsx",
        variable="Generación eléctrica por tipo de fuente",
        fuente="OLADE / SIELAC", redistribuible="no",
        ruta_navegacion="SIELAC / Estadísticas Energéticas de ALC / Reportes "
                        "/ Oferta y demanda / Eléctrico / Generación "
                        "eléctrica por fuente - Anual (filtrar: 6 países, "
                        "2020-2024)",
        sha256="33eaf042c918c9bac2b4216c899c6d632bc9a386808f54cb1ceafe65a5361e6f",
        tamano_bytes=41601, cobertura="6 países SIEPAC, 2020-2024",
    ),
    ArchivoRaw(
        carpeta="importaciones_exportaciones", patron="*.xlsx",
        variable="Matriz de balance energético (importaciones/exportaciones)",
        fuente="OLADE / SIELAC", redistribuible="no",
        ruta_navegacion="SIELAC / Estadísticas Energéticas de ALC / Reportes "
                        "/ Oferta y demanda / Matriz de balance energético "
                        "(organizar por: eléctrico, 6 países, 2020-2024)",
        sha256="4648cca681b3c7c2b30ed1578b3aff479312b1b2c14d7bbe95e29abdaacb2d05",
        tamano_bytes=189229, cobertura="6 países SIEPAC, 2020-2024",
    ),
    ArchivoRaw(
        carpeta="produccion_bruta", patron="*.xlsx",
        variable="Producción bruta de electricidad",
        fuente="OLADE / SIELAC", redistribuible="no",
        ruta_navegacion="SIELAC / Estadísticas Energéticas de ALC / Reportes "
                        "/ Oferta y demanda / Series de oferta y demanda "
                        "(organizar por: eléctrico, 6 países, 2020-2024)",
        sha256="0135cdc16ba6e75926582aea409f02d1b53761693b0dabb16a918127b5136d4a",
        tamano_bytes=25926, cobertura="6 países SIEPAC, 2020-2024",
    ),
    ArchivoRaw(
        carpeta="pib", patron="*.csv",
        variable="PIB real (USD constantes de 2015)",
        fuente="Banco Mundial (WDI)", redistribuible="si",
        ruta_navegacion="datos.bancomundial.org/indicador/NY.GDP.MKTP.KD "
                        "(descarga completa, se filtra en el ETL)",
        sha256="4caefd74bb19ed6cc827a116f555ee8a0535ce24bca8bca225cef3368f94b0d4",
        tamano_bytes=301964, cobertura="Todos los países, serie histórica completa",
    ),
    ArchivoRaw(
        carpeta="poblacion_total", patron="*.xlsx",
        variable="Población total",
        fuente="CEPALSTAT (CEPAL-CELADE)", redistribuible="no",
        ruta_navegacion="CEPALSTAT / Estadísticas e indicadores / Población / "
                        "Estimaciones y proyecciones de población / "
                        "Población total por sexo (filtrar: 6 países SIEPAC, "
                        "2020-2024, ambos sexos; hoja \"datos\" del export, "
                        "valores en miles de habitantes)",
        sha256="707881f9cdef002f1f982a1a42d89a33d4f77de5d220c52089afba8eb533acba",
        tamano_bytes=10695, cobertura="6 países SIEPAC, 2020-2024",
    ),
    ArchivoRaw(
        carpeta="tarifa_electrica_media", patron="*.xlsx",
        variable="Precio medio de la electricidad",
        fuente="CEPALSTAT", redistribuible="no",
        ruta_navegacion="statistics.cepal.org/portal/cepalstat/dashboard.html"
                        "?indicator_id=4758&area_id=2454&lang=es (filtrar: "
                        "6 países SIEPAC y años disponibles)",
        sha256="5f847978bc5838a7e24f6e3d82be7623b87b4de3d92339261c8b24e299d68adf",
        tamano_bytes=10730, cobertura="6 países SIEPAC, 2020-2024",
    ),
    ArchivoRaw(
        carpeta="valor_agregado_industrial", patron="*.xlsx",
        variable="Valor agregado industrial (% del PIB)",
        fuente="agenda2030lac (ODS-NU / UNIDO)", redistribuible="no",
        ruta_navegacion="agenda2030lac.org/estadisticas/banco-datos-regional-"
                        "seguimiento-ods.html?indicator_id=4353&lang=es",
        sha256="97f92db3fd94eb0f19fb6dd89ce8f0729618101db79739f0ecea68c0849e8ba1",
        tamano_bytes=9484, cobertura="6 países SIEPAC, 2020-2024",
    ),
]
