import pickle
import pandas as pd
import streamlit as st
from st_pages import Page, show_pages
from io import BytesIO

# Specify what pages should be shown in the sidebar, and what their titles and icons
# should be
show_pages(
    [
        Page("app.py", "Introducción", "🏠"),
        Page("vista/02_obtener_series_inegi.py", "Obtener datos INEGI", "📗"),
        Page("vista/03_obtener_series_banxico.py", "Obtener datos BANXICO", "📘"),
        Page("vista/04_buscar.py", "Buscar rutas", "🔎")
    ]
)

@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

@st.cache_data
def load_data(url):
    df = pd.read_excel(url)
    return df

muestra_rutas: pd.DataFrame = load_data("./pruebas/inegi-muestra-5rutas.xlsx")
muestra_claves: pd.DataFrame = load_data("./pruebas/inegi-muestra-5claves.xlsx")

# Opciones para leer el catalogo
# 1) Leyendo el excel por primera vez y despues serializarlo
#catalogo_inegi: pd.DataFrame = load_data(r"./catalogo/catalogoCompletoINEGI.xlsx")


# 2) Abrir el archivo en modo lectura binaria y guardarlo en cache por si lo vuelve abrir el enlace
@st.cache_data
def load_data_objeto(url):
    with open(url, 'rb') as f:
        # Cargar el objeto desde el archivo
        catalogo_inegi = pickle.load(f)
    return catalogo_inegi

# Ventakas de hacerlo de esta forma, la primera vez siempre correra rapido
catalogo_inegi = load_data_objeto('./catalogo/catalogoINEGI.pkl')

# Titulo principal y pequeña explicación
st.title(":red[Dirección de Metodologías y Modelos de Riesgos]")
text = """
Para el desarrollo de diversos proyectos se requieré información macroeconómica que emiten diversas entidades como
el Instituto Nacional de Estadística y Geografía (INEGI) y el Banco de México (BANXICO). Ante la necesidad de poder consultar información de manera rápida y eficiente se propuso crear una interfaz para la recolección de información de manera automatizada.
"""

st.write(text)

st.header("API de :green[INEGI] y :blue[BANXICO]")
text = '''
A través de la interfaz se podrá obtener información de variables económicas de INEGI y BANXICO, optimizando la búsqueda de las variables de sus sitios de internet. Con esto se busca ahorrar tiempo en las búsquedas de series económicas y automatizar el proceso.

La interfaz hace uso de las API's(Application Programming Interface) las cuales se conectan con INEGI y BANXICO para extraer la información, estas API's son proporcionadas por los mismo sitios, por lo que la extracción de informacion es confiable y segura.
'''

st.markdown(text)

st.subheader("Proporción de indicadores recolectados")

text ="""
Se creó un catálogo con todos los indicadores que se pudieron recolectar de cada uno de los sitios. A continuación se mostrará el total de indicadores por categoría de nuestro catálogo que podrá ser descargado en la parte de abajo.
"""
st.write(text)

# Calcular las frecuencias
catalogo_inegi.rename(columns={'Nivel1': "Categoria"}, inplace=True)
frecuencias = catalogo_inegi['Categoria'].value_counts().sort_index()
frecuencias.name = "Total de variables"
st.write(frecuencias)


text = """Para el uso de la extracción de la información a través de esta interfaz web se debe tener una lista de variables a buscar de los sitios de INEGI o BANXICO. Esta lista debe estar guardada en un archivo de trabajo de Excel y debe seguir al menos alguno de los formatos especificados a continuación. """

st.write(text)

st.subheader("Búsqueda por rutas")
text = """
Para obtener información de las variables con esta estructura debe indicarse la ruta que se debe seguir para obtener la variable y así sucesivamente para cada variables. Ejemplo:
"""
st.write(text)
st.write(muestra_rutas)

st.subheader("Búsqueda por claves")
text = """
Para obtener información de las variables con esta estructura debe indicar sólo la clave de las variables a buscar. Ejemplo:
"""
st.write(text)
st.write(muestra_claves)


st.subheader("Catálogo de INEGI")
text = """
Dejamos a tu disposición un catálogo de todos los indicadores que recolectamos con la ruta de cada variable con su respectiva clave unica con la finalidad que puede ser más facil estructurar sus archivos con los formatos especificados. 
"""
st.write(text)

# csv = convert_df(catalogo_inegi)
# st.subheader("Descargar Catalogos", divider="gray")
# st.download_button(
#                 label='Descargar catálogo INEGI como CSV 📥',
#                 data=csv,
#                 file_name= 'catalogo-inegi.csv',
#                 mime='text/csv'
#                 )

@st.cache_data
def convert_df_to_excel(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    excel_file = BytesIO()
    catalogo_inegi.to_excel(excel_file, index=False, engine='xlsxwriter')
    excel_file.seek(0)
    return excel_file

excel = convert_df_to_excel(catalogo_inegi)

# Descargar el archivo Excel
st.download_button(
label="Descargar catálogo INEGI Excel 📥",
data=excel,
file_name='catalogo_inegi.xlsx',
key='download_button'
)



text = '''
Adicional, hemos proporcionado una sección llamada "Buscar rutas 🔎" para encontrar las rutas de indicadores a través de palabras claves.
'''
st.write(text)
