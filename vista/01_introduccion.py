import pickle
import numpy as np
import pandas as pd
import streamlit as st
from io import BytesIO



@st.cache_data
def load_data_objeto(url):
    with open(url, 'rb') as f:
        # Cargar el objeto desde el archivo
        catalogo_inegi = pickle.load(f)
    return catalogo_inegi


@st.cache_data
def load_data(url):
    df = pd.read_excel(url)
    return df


@st.cache_data
def convert_df_to_excel(df, rutas):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    excel_file = BytesIO()
    # Crear un objeto ExcelWriter que escribe en el objeto BytesIO
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        # Escribir el primer DataFrame en la hoja 'Hoja1'
        df.to_excel(writer, sheet_name='Completo', index=False)
        
        # Escribir el segundo DataFrame en la hoja 'Hoja2'
        rutas.to_excel(writer, sheet_name='Desglosado', index=False)

    #catalogo_inegi.to_excel(excel_file, sheet_name='Completo', index=False, engine='xlsxwriter')
    excel_file.seek(0)
    return excel_file


muestra_rutas: pd.DataFrame = load_data("./pruebas/inegi-muestra-5rutas.xlsx")
muestra_claves: pd.DataFrame = load_data("./pruebas/inegi-muestra-5claves.xlsx")


# Ventajas de hacerlo de esta forma, la primera vez siempre correra rapido
catalogo_inegi: pd.DataFrame = load_data_objeto('./catalogo/catalogoINEGI.pkl')
catalogo_banxico: pd.DataFrame =  load_data_objeto('./catalogo/catalogoBANXICO.pkl')

# Titulo principal y pequeña explicación
st.title(":red[Dirección de Metodologías y Modelos de Riesgos]")
text = """
Para el desarrollo de diversos proyectos y modelos se ha requeridos información macroeconómica que emiten diversas entidades como
el [Instituto Nacional de Estadística y Geografía](https://www.inegi.org.mx/default.html) (INEGI) y el [Banco de México](https://www.banxico.org.mx) (BANXICO). Ante la necesidad de poder consultar información de manera rápida y eficiente se creó la presente interfaz para la recolección de información de manera automatizada.
"""

st.write(text)

st.header("API de :green[INEGI] y :blue[BANXICO]")
text = '''
A través de la interfaz se puede obtener información de variables economicas de [INEGI](https://www.inegi.org.mx/app/indicadores/?tm=0) y [BANXICO](https://www.banxico.org.mx/SieAPIRest/service/v1/doc/catalogoSeries), optimizando la búsqueda de las variables de sus sitios de internet. Con esto se logró ahorrar tiempo en las búsquedas de series económicas y automatizar el proceso.

La interfaz hace uso de las API's (Application Programming Interface) las cuales se conectan con INEGI y BANXICO para extraer la información, estas API's son proporcionadas por los mismo sitios, por lo que la extracción de información es confiable y segura.
'''

st.markdown(text)

st.subheader("Proporción de indicadores recolectados")

text ="""
Se creó un catálogo con todos los indicadores que se pudieron recolectar de cada uno de los sitios. A continuación se mostrará el total de indicadores por categoría de cada uno de los catálogos.
"""
st.write(text)

st.markdown("#### INEGI")
# Desglose por nivel
tab1, tab2, tab3 = st.tabs(["Nivel1", "Nivel2", "Nivel3"])
catalogo_inegi.dropna(inplace=True)
rutas_separadas: pd.DataFrame = catalogo_inegi["Variables"].str.split('>', expand=True)
old_names = range(0, 11)
new_names = [f"Nivel {i}" for i in range(1, 12)]
new_col: dict = dict(zip(old_names, new_names))
rutas_separadas.rename(new_col, axis=1, inplace=True)

with tab1:
    st.write(rutas_separadas.groupby(["Nivel 1"]).size().reset_index(name="Número de variables"))

with tab2:
    two_nivels:pd.DataFrame = rutas_separadas.groupby(["Nivel 1", "Nivel 2"]).size().reset_index(name="Número de variables")
    
    two_nivels["Nivel 1"] = np.where(two_nivels.duplicated(subset="Nivel 1"), "", two_nivels["Nivel 1"])
    
    st.write(two_nivels)

with tab3:   
    three_nivels: pd.DataFrame = rutas_separadas.groupby(["Nivel 1", "Nivel 2", "Nivel 3"]).size().reset_index(name="Número de variables") 
    three_nivels["Nivel 1"] = np.where(three_nivels.duplicated(subset="Nivel 1"), "", three_nivels["Nivel 1"])
    three_nivels["Nivel 2"] = np.where(three_nivels.duplicated(subset="Nivel 2"), "", three_nivels["Nivel 2"])
    st.write(three_nivels)


catalogo_inegi.rename(columns={'Nivel1': "Categoria"}, inplace=True)

st.markdown("#### BANXICO")
tab1_ban, tab2_ban, tab3_ban = st.tabs(["Nivel1", "Nivel2", "Nivel3"])
# Eliminamos posibles filas vacias
catalogo_banxico.dropna(inplace=True)
rutas_separadas_ban: pd.DataFrame = catalogo_banxico["Ruta"].str.split(">", expand=True)
rutas_separadas_ban.rename(new_col, axis=1, inplace=True)

with tab1_ban:
    st.write(rutas_separadas_ban.groupby(["Nivel 2"]).size().reset_index(name="Número de variables"))

with tab2_ban:
    two_nivels_ban:pd.DataFrame = rutas_separadas_ban.groupby(["Nivel 2", "Nivel 3"]).size().reset_index(name="Número de variables")
    
    two_nivels_ban["Nivel 2"] = np.where(two_nivels_ban.duplicated(subset="Nivel 2"), "", two_nivels_ban["Nivel 2"])
    
    st.write(two_nivels_ban)

with tab3_ban:   
    three_nivels_ban: pd.DataFrame = rutas_separadas_ban.groupby(["Nivel 2", "Nivel 3", "Nivel 4"]).size().reset_index(name="Número de variables") 
    three_nivels_ban["Nivel 2"] = np.where(three_nivels_ban.duplicated(subset="Nivel 2"), "", three_nivels_ban["Nivel 2"])
    three_nivels_ban["Nivel 3"] = np.where(three_nivels_ban.duplicated(subset="Nivel 3"), "", three_nivels_ban["Nivel 3"])
    st.write(three_nivels_ban)


text = """Para el uso de la extracción de la información a través de esta interfaz web se debe tener una lista de variables a buscar de los sitios de INEGI y BANXICO. Esta lista debe estar guardada en un archivo de trabajo de Excel y debe seguir al menos alguno de los formatos especificados a continuación. """

st.write(text)

st.subheader("Búsqueda por rutas")
text = """
Para obtener información de las variables por ruta debe indicarse en cada fila la ruta que se debe seguir para buscar cada variable deseada. Ejemplo:
"""
st.write(text)
st.write(muestra_rutas)

st.subheader("Búsqueda por claves")
text = """
Para obtener información de las variables por claves debe indicarse en cada fila la clave de las variables a buscar. Ejemplo:
"""
st.write(text)
st.write(muestra_claves)


st.subheader("Catálogos")
text = """
A continuación, se muestran dos catálogos que incluyen la ruta y clave de todos los indicadores recolectados del portal de INEGI y BANXICO con la finalidad que sea más fácil
estructurar los archivos de consulta con los formatos especificados.
"""
st.write(text)


excel = convert_df_to_excel(catalogo_inegi, rutas_separadas)

# Descargar el archivo Excel
st.download_button(label="Descargar catálogo INEGI Excel 📥",
                    data=excel,
                    file_name='catalogo_inegi.xlsx',
                    key='download_button1')

excel2 = convert_df_to_excel(catalogo_banxico, rutas_separadas_ban)

st.download_button(label="Descargar catálogo BANXICO Excel 📥",
                    data=excel2,
                    file_name='catalogo_banxico.xlsx',
                    key='download_button2')

st.divider()
text = '''
Adicional, hemos proporcionado una sección llamada "🔎 BUSCAR RUTAS" para encontrar las rutas de indicadores a través de palabras claves.
'''
st.write(text)
