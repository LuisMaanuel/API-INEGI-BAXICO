# API-INEGI-BANXICO
**Por: GUILLERMO GERARDO ANDRES URBANO Y LUIS MANUEL GONZALEZ HIDALGO**

## PROPOSITO
Este repositorio fue creado con la finalidad de tener una interfaz grafica y una manera mas rapida y sencilla de obtener datos economicos dtanto del Instituto Nacional de Estadistica y Geografia (INEGI) como del Banco de Mexico (BANXICO) sin la necesidad de ingresar manualmente a cada uno de los distintos repositorios de datos y asi obtenerlos.

**NOTA:** Si ya se cuenta con el repositorio descargado y se quiere visualizar la interfaz es importante acceder mediante terminal a la carpeta donde se encuentra el archivo **app.py**  (o en dicha carpeta abrir una terminal) y ejecutar el siguiente comando

```bash
streamlit run app.py
```

Al igual que tener una **version de python** superior o igual a la **3.8**
 
## Estructura
* app.py

Este archivo .py es el encargado de desplegar la pagina base de la interfaz, cada una de las vistas para poder visualizar y descargar datos del INEGI y de BANXICO asi como el menu izquierdo de navegacion.


* Notebook

Contiene distintos notebooks los cuales muestran el ejemplo de uso de distintas funciones que son usados para obtener los datos de las vistas que son desplegadas para INEGI y para BANXICO

* pages_sections.toml

Es usado para que las vistas sean desplegadas cuando son seleccionadas en el menu izquierdo de las vistas.

* pruebas

Contiene archvos .xlsx los cuales son usados para hacer pruebas de obtencion de los datos mediante clave o por ruta de la serie, tanto para BANXICO como para INEGI.

* requirements.txt

Contiene el nombre de las distintas bibliotecas que se necesitan para poder ejecutar app.py

* vistas

En esta carpeta se encuentras las vistas o interfaces que son desplegadas cuando se va a buscar una serie de INEGI, BANXICO o simplemente cuando se requiere buscar una serie.

* catalogo

Contiene los catalogos de las rutas para las series correspondientes a BANXICO e INEGI, los archivos .pkl son los mismos que los archivos excel solo que de esta manera se cargan para obtener las serires ya que es mas facil con .pkl
