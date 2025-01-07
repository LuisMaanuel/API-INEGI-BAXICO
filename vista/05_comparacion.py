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


def infer_format(date_str):
    formats = ['%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m', '%m/%Y',
               '%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y', '%Y-%m', '%m-%Y',
               '%Y_%m_%d', '%d_%m_%Y', '%m_%d_%Y', '%Y_%m', '%m_%Y',]
    for fmt in formats:
        try:
            datetime.strptime(date_str, fmt)
            return fmt
        except ValueError:
            continue
    return None


def subtract_two_df(ruta1: pd.DataFrame = None, ruta2: pd.DataFrame = None, 
                    fecha_inicio = None, fecha_fin = None):
    df1 = pd.read_excel(ruta1)
    st.write('- Datos anteriores')
    st.write(df1)

    df2 = pd.read_excel(ruta2)
    st.write('- Datos nuevos')
    st.write(df2)
    
    df1[df1.columns[0]] = pd.to_datetime(df1[df1.columns[0]], ).dt.date
    df2[df2.columns[0]] = pd.to_datetime(df2[df2.columns[0]], ).dt.date


    if fecha_inicio:
        df1 = df1[ (fecha_inicio <= df1[df1.columns[0]] ) & ( df1[df1.columns[0]] <= fecha_fin)]
        df2 = df2[ (fecha_inicio <= df2[df2.columns[0]] ) & ( df2[df2.columns[0]] <= fecha_fin)]

    df1.set_index(df1.columns[0],inplace=True)

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
st.write('''Para un correcto funcionamiento, es importante que ambos archivos excel (.xlsx) **tenga el mismo nombrado de
         las columnas. Con excepcion del nombre asigando a la columna de la fecha y seguir la siguiente estructura:''')

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




# -----------------------------
# -----------------------------                 Configuracion inicial
# -----------------------------


st.subheader('Configuracion inicial',divider='orange')


col1, col2 = st.columns(2)
with col1:
    st.write('Fecha de filtrado')
    fecha_inicio = st.date_input('Fecha de inicio', value = None, min_value=datetime(1990,1,1), format='DD/MM/YYYY')
    st.write('Tu fecha escrita fue:', fecha_inicio)

    fecha_fin = st.date_input('Fecha final', value=datetime.now(), min_value=datetime(1990,1,1), format='DD/MM/YYYY')
    st.write('Tu fecha esscrita fue:', fecha_fin)



with col2:
    st.write('Cargar archivos')

    file1 = st.file_uploader("Escoger el archivo de datos anteriores o desactializados (Sólo se admite archivos de Excel .xlsx)",key='a')
    st.write("Archivo que seleccionaste: ", "" if file1 is None else file1.name)

    file2 = st.file_uploader("Escoger el archivo de los datos nuevos o actualizados (Sólo se admite archivos de Excel .xlsx)",key='b')
    st.write("Archivo que seleccionaste: ", "" if file2 is None else file2.name)





# -----------------------------
# -----------------------------                 Resultados
# -----------------------------


if file1 and file2:
    df = subtract_two_df(file1, file2,fecha_inicio, fecha_fin)
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
    



# -----------------------------
# -----------------------------                 Graficas
# -----------------------------

    st.subheader('Visualización', divider='orange')

    selected_variable = st.selectbox('Selecciona la variable a graficar:', df.columns)
    # Crear y mostrar la gráfica de líneas
    df_sin_nans = df[selected_variable].dropna()
    fig = px.line(df_sin_nans, y=selected_variable) #title=" ".join(selected_variable.split(" ")[1:]))
    # Agregar el subtítulo mediante annotations
    fig.update_layout(
        annotations = [
            dict(
                x=0.0,  # Posición en el eje X (0.5 = centrado)
                y=1.21 - (0.05*(i+1)),  # Posición en el eje Y (negativo para colocarlo debajo del título principal)
                xref="paper",
                yref="paper",
                text= nombre + ">",
                showarrow=False,
                font=dict(size=14)  # Tamaño de fuente del subtítulo
        )
        for i, nombre in enumerate(df.columns)
      ]
    )

    st.plotly_chart(fig)
