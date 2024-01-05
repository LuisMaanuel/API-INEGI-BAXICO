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
        Page("vista/02_obtener_series_inegi.py", "Obtener datos INEGI", "📉"),
        #Page("vista/03_obtener_series_banxico.py", "Obtener datos BANXICO", ":chart_with_upwards_trend:"),
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

muestra_rutas: pd.DataFrame = load_data("./catalogo/muestra5-rutas.xlsx")
muestra_claves: pd.DataFrame = load_data("./catalogo/muestra5-claves.xlsx")

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
st.title(":red[Dirección de Metodologías y Modelos Riesgos]")
st.header("API de :green[INEGI] y :blue[BANXICO]")
text = '''
Con esta interfaz se podrá obtener información de variables economicas de INEGI y BANXICO de una manera automatizada, optimizando la busqueda de las variables en sus sitios de internet. Con esto se busca ahorrar tiempo en las busquedas de series economicas.

Para el uso de la aplicación se debe tener una lista de variables a buscar de los sitios de Inegi o Banxico. Debe estar guardadas en un archivo de trabajo de Excel y deben seguir el formato que se describe a continuación. 
'''

st.markdown(text)

st.subheader("Busqueda por rutas")
text = """
Para obtener informacion de las variables con esta estructura debe indicarse la ruta que se debe seguir para obtener la variable y asi sucesivamente para cada variables. Ejemplo:
"""
st.write(text)
st.write(muestra_rutas)

st.subheader("Busqueda por claves")
text = """
Para obtener informacion de las variables con esta estructura debe indicar sólo la clave de las variables a buscar. Ejemplo:
"""
st.write(text)
st.write(muestra_claves)


text = """
Para ampliar el conocimineto de todas las variables que son posibles buscar, se proporciona un catalogo con las variables que se tienen registradas en nuestra aplicación de los sitios de INEGI y BANXICO.
"""
st.write(text)

# csv = convert_df(catalogo_inegi)
# st.subheader("Descargar Catalogos", divider="gray")
# st.download_button(
#                 label='Descargar catalogo INEGI como CSV 📥',
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
label="Descargar catalogo INEGI Excel 📥",
data=excel,
file_name='catalogo_inegi.xlsx',
key='download_button'
)



text = '''
Adional, si se desea buscar por palabras en particulas del conjunto de variables para encontrar las rutas de manera más efectiva, hemos proporcionado la seccion de "Buscar rutas 🔎".
'''
st.write(text)
