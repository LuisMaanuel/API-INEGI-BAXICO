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
                    fecha_inicio = None, fecha_fin = datetime.now()):
    df1 = pd.read_excel(ruta1)
    df1[df1.columns[0]] = df1[df1.columns[0]].apply(lambda x: str(x)[:10])
    st.write('- Datos anteriores')
    st.write(df1)

    df2 = pd.read_excel(ruta2)
    df2[df2.columns[0]] = df2[df2.columns[0]].apply(lambda x: str(x)[:10])
    st.write('- Datos nuevos')
    st.write(df2)

    formato_1 = infer_format(df1.iloc[0,0])
    formato_2 = infer_format(df2.iloc[0,0])
    
    # convertimos ambas fechas en el mismo formato
    try:
        df1[df1.columns[0]] = pd.to_datetime(df1[df1.columns[0]], format= formato_1).dt.date#strftime(formato_1)
        df2[df2.columns[0]] = pd.to_datetime(df2[df2.columns[0]], format= formato_1).dt.date#strftime(formato_1)
    except:
        df1[df1.columns[0]] = pd.to_datetime(df1[df1.columns[0]], format= formato_2).dt.date#strftime(formato_2)
        df2[df2.columns[0]] = pd.to_datetime(df2[df2.columns[0]], format= formato_2).dt.date#strftime(formato_2)


    if fecha_inicio:
        df1 = df1[ (fecha_inicio <= df1[df1.columns[0]] ) & ( df1[df1.columns[0]] <= fecha_fin)]
        df2 = df2[ (fecha_inicio <= df2[df2.columns[0]] ) & ( df2[df2.columns[0]] <= fecha_fin)]

    df1.set_index(df1.columns[0],inplace=True)
    df2.set_index(df2.columns[0],inplace=True)

    return df1.subtract(df2)#.abs()







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
    datos_ant[datos_ant.columns[0]] = pd.to_datetime(datos_ant[datos_ant.columns[0]], format='Y%-m%-d%').dt.date

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
         las columnas.** Con excepcion del nombre asigando a la columna de la fecha y debe seguir la siguiente estructura:''')

st.write('- La primer columna de ambos archivos debe corresponder a la fecha de los datos. ') 

st.write('- la siguiente columna en ambos archivos debe hacer referencia a la misma serie de datos económicos (supongamos PIB).')
st.write('''- la tercer columna en  ambos archivos hacen referencia a la misma serie de datos económicos (supongamos el precio de venta del dolar)
            y asi sucesivamente con las demas columnas''')

st.subheader('Ejemplo de estructura de los archivos')

st.write('- Datos anteriores')
df1 = load_excel('./catalogo/comparacion/datos_anteriores.xlsx')
df1[df1.columns[0]] = df1[df1.columns[0]].apply(lambda x: str(x)[:10])
st.write(df1)

st.write('- Datos nuevos')
df2 = load_excel('./catalogo/comparacion/datos_nuevos.xlsx')
df2[df2.columns[0]] = df2[df2.columns[0]].apply(lambda x: str(x)[:10])
st.write(df2)

st.write('- Resultado')


formato_1 = infer_format(df1.iloc[0,0])
formato_2 = infer_format(df2.iloc[0,0])
    
# convertimos ambas fechas en el mismo formato
try:
    df1[df1.columns[0]] = pd.to_datetime(df1[df1.columns[0]], format= formato_1).dt.date#strftime(formato_1)
    df2[df2.columns[0]] = pd.to_datetime(df2[df2.columns[0]], format= formato_1).dt.date#strftime(formato_1)
except:
    df1[df1.columns[0]] = pd.to_datetime(df1[df1.columns[0]], format= formato_2).dt.date#strftime(formato_2)
    df2[df2.columns[0]] = pd.to_datetime(df2[df2.columns[0]], format= formato_2).dt.date#strftime(formato_2)


df1.set_index(df1.columns[0],inplace=True)
df2.set_index(df2.columns[0],inplace=True)

st.write( df1.subtract(df2))




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

    file1 = st.file_uploader("Escoger el archivo de datos anteriores o desactualizados (Sólo se admite archivos de Excel .xlsx)",key='a')
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
    st.write('''**OBSERVACION** Si el resultado marca filas con valores nulos (None) quiere decir que los rangos de fechas
                entre los archivos son distintos, es decir, un archivo si tiene registros en esas fechas pero el otro archivo
                no, **por lo cual es importante especificar el rango de las fechas**''')



# -----------------------------
# -----------------------------                 Graficas de estadisticas y del historico
# -----------------------------

    st.subheader('Visualización', divider='orange')

    df_abs = df.abs()
    desc_stats_ =  df_abs.describe() 
    #describe = desc_stats_.copy()

    col1, col2 = st.columns(2)
    with col1:
        variables = st.multiselect('Seleccione las variables a graficar', ['Seleccionar todas'] + df.columns.to_list())
        variables  = df.columns if 'Seleccionar todas' in variables  or not variables else variables
    with col2:
        estadisticos = st.multiselect('Seleccione las estadisticas deseadas', ['Todos los estadisticos','promedio','min','max'])
        estadisticos = ['promedio','min','max'] if 'Todos los estadisticos' in estadisticos or not estadisticos else estadisticos


    # -----------------------------             Estadisticas, minimo, maximo, promedio
    desc_stats = desc_stats_[variables].T
    desc_stats_ = desc_stats_.T

    #desc_stats = desc_stats.merge(df.sum().to_frame('sum'), left_index=True, right_index=True)
    fig = px.bar(
        df_abs[variables].sum().to_frame('sum').reset_index().rename(columns={'index':'Variables'}),
        x="Variables",  # Estadísticas en el eje X
        y="sum",  # Valores en el eje Y
        title="Suma de las diferencias",
        )
    st.plotly_chart(fig)

    # seleccionando las estadisticas
    desc_stats = desc_stats.rename(columns={'mean':'promedio'})[estadisticos + ['std']].T
    desc_stats_ = desc_stats_.rename(columns={'mean':'promedio'})[['min','max','promedio','std']].T

    desc_stats.reset_index(inplace=True)
    desc_stats_.reset_index(inplace=True)


    # transformando el DF para poder graficar
    desc_stats_long = desc_stats.melt(id_vars='index',var_name='Column',value_name='Value')

    # Filtrando solo la desviación estándar y reorganizando los datos
    desviacion_data = desc_stats.loc[desc_stats['index'] == 'std']
    desviacion_melted = desviacion_data.melt(id_vars='index', var_name='Column', value_name='Error')

    # Filtrando solo el promedio y añadiendo la desviación estándar como error
    promedios = desc_stats_long[desc_stats_long['index'] == 'promedio'].copy()

    # Fusionar la desviación estándar con los promedios
    promedios = promedios.merge(desviacion_melted[['Column', 'Error']], on='Column', how='left')


    fig = px.bar(
        desc_stats_long[desc_stats_long['index'] != 'std'],
        x="index",  # Estadísticas en el eje X
        y="Value",  # Valores en el eje Y
        color="Column",  # Diferenciación por columna (hue)
        barmode="group",  # Agrupar barras
        title="Gráfico de estadísticas descriptivas",
        labels={"index": "Estadística", "Value": "Valor", "Column": "Columna"},
        )
    
    # Filtrar las barras de promedio y añadir barras de error
    for trace in fig.data:
        if 'promedio' in desc_stats_long[desc_stats_long['Column'] == trace.name]['index'].values:
            promedio_data = promedios[promedios['Column'] == trace.name]
            trace.error_y = dict(type='data', array=promedio_data['Error'])
    
    st.plotly_chart(fig)




    # -----------------------------             historico
    st.subheader('Historicos',divider='orange')
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
                text='',
                showarrow=False,
                font=dict(size=14)  # Tamaño de fuente del subtítulo
        )
        for i, nombre in enumerate(df.columns)
      ]
    )

    st.plotly_chart(fig)
    
    

    
    st.subheader("Descargar variables", divider="orange")
    # Crearemos un archivo de Excel con BytesIO (Para cargarlo en memoria)
    excel_file = BytesIO()
   
    # Obtenemos todas sus graficas
    imgs_bytes = []
    for i, col in enumerate(df.columns):       
        fig_ = px.line(df[col].dropna(), y=col,  title=" ".join(col.split(" ")[1:]))
        imgs_bytes.append(BytesIO())
        fig_.write_image(imgs_bytes[i], format='png')

   # Crear un objeto pd.ExcelWriter que escribe en el objeto BytesIO
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
      # Agregar el DataFrame a la primera hoja
      df.to_excel(writer, sheet_name='Datos', index=True)
      desc_stats_.rename(columns={'index':'Estadistica'}).to_excel(writer, sheet_name= 'Estadisticas', index=False)
      # Agregamos imagenes
      for i, img_bytes1 in enumerate(imgs_bytes):
        df_img1 = pd.DataFrame({'image': [img_bytes1.getvalue()]})
        #df_img1.to_excel(writer, sheet_name='Graficas', index=False, header=False, startrow=i*15, startcol=0)
        
        workbook = writer.book
        worksheet = writer.sheets['Graficas']
        # Crear objetos Image para cada gráfica y agregarlos a la hoja
        worksheet.insert_image(f'A{1 if i==0 else i*26}', 'grafica_linea_{i}.png', {'image_data': img_bytes1})

  #     pio.write_excel(fig, excel_file, sheet_name='graficas')
   
    #df.to_excel(excel_file, index=True, engine='xlsxwriter')
    excel_file.seek(0)
    # Descargar el archivo Excel
    st.download_button(
        label="Descargar variables Excel 📥",
        data=excel_file,
        file_name='comparacion.xlsx',
        key='download_button'
     )
