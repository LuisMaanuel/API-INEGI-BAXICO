import pickle
import numpy as np
import pandas as pd
import streamlit as st 
from io import BytesIO
from numpy import nan 
from sie_banxico import SIEBanxico
from datetime import datetime
import plotly.express as px
import plotly.io as pio


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

@st.cache_data
def load_excel(url):
    df = pd.read_excel(url)
    return df

@st.cache_data
def load_data_objeto(url):
    with open(url, 'rb') as f:
        # Cargar el objeto desde el archivo
        catalogo_inegi = pickle.load(f)
    return catalogo_inegi


def subtract_two_df(ruta1, ruta2):
    df1 = pd.read_excel(ruta1)
    df1.set_index(df1.columns[0],inplace=True)

    df2 = pd.read_excel(ruta2)
    df2.set_index(df2.columns[0],inplace=True)

    return df1.subtract(df2)







# -----------------------------
# -----------------------------
# -----------------------------                 INTERFAZ
# -----------------------------
# -----------------------------




# -----------------------------
# -----------------------------                 Sidebar con archivos de muestra
# -----------------------------

with st.sidebar:
    st.write('Ejemplo de datos nuevos:')
    datos_nuevos = load_excel('./catalogo/comparacion/datos_nuevos.xlsx')
    excel_file = BytesIO()
    datos_nuevos.to_excel(excel_file, index=False, engine='xlsxwriter')
    excel_file.seek(0)

    st.download_button(label='datos_nuevos.xlsx',
                       data = excel_file,
                       file_name='datos_nuevos.xlsx',
                       key='download_button_r')
    
with st.sidebar:
    st.write('Ejemplo de datos anteriores:')
    datos_ant = load_excel('./catalogo/comparacion/datos_anteriores.xlsx')
    excel_file = BytesIO()
    datos_ant.to_excel(excel_file, index=False, engine='xlsxwriter')
    excel_file.seek(0)

    st.download_button(label='datos_anteriores.xlsx',
                       data = excel_file,
                       file_name='datos_anteriores.xlsx',
                       key='download_button_l')

# -----------------------------
# -----------------------------                 Titulo principal y pequeña explicación
# -----------------------------


st.title("Comparacion de datos 🆚")

st.write('''Esta sección tiene la finalidad de comparar dos marcos de datos o _dataframes_, uno de ellos contiene los datos 
         que ya se tenian con anterioridad (en caso de exista) y otro con nuevos datos obtenidos por esta misma plataforma.
         Ya que al realizar una consulta y obtener nuevos datos pueden existir ciertas discrepancias entre datos anteriores y
         los nuevos, esto es debido a que INEGI y BANXICO actualizan sus series existentes para proporcionar informacion mas 
         certera.''')

# Estructura de los datos a subir
st.subheader("Estructura de los datos a subir", divider="orange")
st.write('''Para un correcto funcionamiento, es importante que ambos archivos excel (.xlsx) **tenga la misma estructura, tanto en el nombre de
         las columnas como en el numero total de registros a comparar y el mismo formato de fecha.** ya que si se tienen fechas separadas con "-" en un archivo y 
         en otro archivo separadas con "_" no vamos a tener un resultado satisfactorio.''')

st.write('''La primer columna debe corresponder a la fecha de los datos, en ambos archivos la siguiente columna hace referencia a la misma serie de datos económicos,
         la tercer columna de ambos archivos hacen referencia a la misma serie de datos económicos, etc.''')

st.write('- Datos anteriores')
df1 = load_excel('./catalogo/comparacion/datos_anteriores.xlsx')
df1.set_index(df1.columns[0], inplace=True)
st.write(df1)

st.write('- Datos nuevos')
df2 = load_excel('./catalogo/comparacion/datos_nuevos.xlsx')

df2.set_index(df2.columns[0], inplace=True)
st.write(df2)

st.write('- Resultado')
st.write(df1.subtract(df2))





st.subheader('Cargar archivos',divider='orange')

file1 = st.file_uploader("Escoger el archivo de datos anteriores (Sólo se admite archivos de Excel .xlsx)",key='a')
st.write("Archivo que seleccionaste: ", "" if file1 is None else file1.name)

file2 = st.file_uploader("Escoger el archivo de los datos nuevos (Sólo se admite archivos de Excel .xlsx)",key='b')
st.write("Archivo que seleccionaste: ", "" if file2 is None else file2.name)

if file1 and file2:
    df = subtract_two_df(file1, file2)
    st.write('- Resultado')
    st.write(df)

    # descarga de los datos en caso de ser necesario
    excel_file = BytesIO()
    df.reset_index().to_excel(excel_file, index=False, engine='xlsxwriter')
    excel_file.seek(0)
    st.download_button(label='Descarga de datos Excel 📥',
                       data=excel_file,
                       file_name='comparacion.xlsx',
                       key='donwload_button_3')