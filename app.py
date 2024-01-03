import streamlit as st
from st_pages import Page, show_pages, add_page_title

# Specify what pages should be shown in the sidebar, and what their titles and icons
# should be
show_pages(
    [
        Page("app.py", "Introducción", "🏠"),
        Page("vista/02_obtener_series_inegi.py", "Obtener datos INEGI", "📉"),
        Page("vista/03_obtener_series_banxico.py", "Obtener datos BANXICO", ":chart_with_upwards_trend:"),
        Page("vista/04_buscar.py", "Buscar rutas", "🔎")
    ]
)

# Optional -- adds the title and icon to the current page
#add_page_title()


import pandas as pd
import streamlit as st
from io import BytesIO

muestra_rutas: pd.DataFrame = pd.read_excel("./catalogo/muestra5-rutas.xlsx")
muestra_claves: pd.DataFrame = pd.read_excel("./catalogo/muestra5-claves.xlsx")

# Titulo principal y pequeña explicación
st.title(":red[Modelos Internos]")
st.header("API de :green[INEGI] y :blue[BANXICO]")
text = '''
Con esta interfaz se podrá obtener información de variables economicas de INEGI y BANXICO de una manera automatizada, optimizando la busqueda de las variables en sus sitios de internet. Con esto se busca ahorrar tiempo en las busquedas de series economicas.

Para el uso de la aplicación se debe tener una lista de variables a buscar de los sitios de Inegi o Banxico. Debe estar guardadas en un archivo de trabajo de Excel y deben seguir el formato que se describe a continuación. 
'''

st.markdown(text)

st.subheader("Estructura por rutas")
text = """
Para obtener informacion de las variables con esta estructura debe indicarse la ruta que se debe seguir para obtener la variable y asi sucesivamente para cada variables. Ejemplo:
"""
st.write(text)
st.write(muestra_rutas)

st.subheader("Estructura por claves")
text = """
Para obtener informacion de las variables con esta estructura debe indicar sólo la clave de las variables a buscar. Ejemplo:
"""
st.write(text)
st.write(muestra_claves)


text = """
Para ampliar el conocimineto de todas las variables que son posibles buscar, se proporciona un catalogo con las variables que se tienen registradas en nuestra aplicación de los sitios de INEGI y BANXICO.
"""
st.write(text)

def convertir_df_a_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=True, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'}) 
    worksheet.set_column('A:A', None, format1)  
    writer.close()
    processed_data = output.getvalue()
    return processed_data

catalogo_inegi = pd.read_excel(r"./catalogo/catalogoCompletoINEGI.xlsx")
excel_final = convertir_df_a_excel(catalogo_inegi)

st.subheader("Descargar Catalogos", divider="gray")
st.download_button(
                label='Descargar catalogo INEGI 📥',
                data=excel_final,
                file_name= 'catalogo-inegi.xlsx'
                )

text = '''
Adional, si se desea buscar por palabras en particulas del conjunto de variables para encontrar las rutas de manera más efectiva, hemos proporcionado la seccion de "Buscar rutas 🔎".
'''
st.write(text)
