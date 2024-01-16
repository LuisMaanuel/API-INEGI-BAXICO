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

# 2) La primera vez siempre correra rapido, las siguientes seran muy veloces
catalogo: pd.DataFrame = load_data_objeto('./catalogo/catalogoBANXICO.pkl')
rutas_variables_usuario = None

def construir_catalogo(formato: str):
  if formato.strip() == "Rutas":
    columna_formato = "Ruta"
  elif formato.strip() == "Claves":
    columna_formato = "Clave"
  tmp = catalogo[["Ruta", "Clave"]].set_index(columna_formato).squeeze()
  return tmp 

def obtener_serie(ruta_archivo: str, formato:str, token:str = ""):
  global rutas_variables_usuario
  # Tomamos siempre la primera columna
  variables_usuario: pd.Series = pd.read_excel(ruta_archivo).iloc[:,0]
  # Las claves son cadenas
  # Las rutas seran cadenas

  #st.write(variables_usuario.iloc[0])
  catalogo_se: pd.Series = construir_catalogo(formato)

  #st.write(catalogo_se[variables_usuario.iloc[3]])

  # Se instancia la interfaz que se counicara con INEGI
  #inegi = Indicadores(token)  
  #api = SIEBanxico(token = token, id_series = claves.tolist(), language = 'en')

  variables_df = pd.DataFrame({"Mensaje": ["No entro en ninguno de los condicionales programadas (if) reportar"]})
  if formato == "Rutas":
    #Para cada variable tendremos que sacar su clave y nombre de la variable    
    # En el caso que haya más de dos claves se seleciona la longitud maxima (SOLUCION PROVISIONAL)
    #st.write(catalogo_se[variables_usuario.iloc[3]])
    # Cada ruta debe debe tener una clave unica
    # Como solucion provisional en el caso tengas más de una clave se toma la primero(ESTO SE DEBE REVISAR PORQUE SE TIENE MÁS DE UNA CLAVE)
    claves_variables =  variables_usuario.apply(lambda x: catalogo_se[x] if  type(catalogo_se[x]) is str else catalogo_se[x].iloc[0])
    nombres_variables = variables_usuario.apply(lambda x: x.split(">")[-1])

  elif formato == "Claves":
    # En esta parte se trata cuando se tiene la misma clave con diferentes rutas
    claves_variables =  variables_usuario
    #nombres_variables = variables_usuario.apply(lambda x: catalogo_se[x].split(">")[-1])
    
    # Conservaremos el mismo nombre de la variable
    nombres_variables = claves_variables
  
  # Convertir todo cadena
  claves_variables = claves_variables.astype(str)

  # Hace unico los nombres, pero no esta excento que la ruta la pongan dos veces
  #nombres_variables = [str(clave) + " " + nombre for clave, nombre in zip(claves_variables, nombres_variables)]
  
  # Mayor verificacion, quitar los duplicados de la lista si es que existen
  #claves_variables = list(set(claves_variables))
  #nombres_variables = list(set(nombres_variables))
  rutas_variables_usuario = pd.DataFrame({"RutaCompleta": variables_usuario, "NombreVariable": nombres_variables})
  
  # Uso de la API de BANXICO
  api = SIEBanxico(token = token, id_series = claves_variables.tolist(), language = 'en')
  data: dict = api.get_timeseries()

  # Ahora que tenemos la serie tenemos que prevenir aquellas series que no contienen datos por x razon
  # y rellenaremos aquellos titulos vacios que nos proporciona la api con nuestros nombres
  clave_nombre_cat = dict(zip(claves_variables, nombres_variables))
  data_tmp = []
  for serie in data["bmx"]["series"]:
    if "datos" not in serie:
      serie["datos"]= []
    serie["titulo"] = clave_nombre_cat[serie["idSerie"]]
    data_tmp.append(serie)
  data_df = pd.json_normalize(data["bmx"]["series"], record_path='datos', meta = ['idSerie', 'titulo'])
  # Si no aparecen en la serie es porque para esas fechas no se encuntran valores
  df = data_df.pivot(index='fecha', columns='titulo', values='dato')

  # Limpieza del dataframe caso partircula banxico
  for columna in df.columns:
    df[columna].replace("N/E", np.nan, inplace=True)
  return df


# -------------------------- Interfaz ---------------------------
with st.sidebar:
    st.write("Ejemplos de rutas: ")
    muestra_rutas: pd.DataFrame = load_excel("./pruebas/banxico-muestra-5rutas.xlsx")   
    # Crear un archivo Excel en BytesIO
    excel_file = BytesIO()
    muestra_rutas.to_excel(excel_file, index=False, engine='xlsxwriter')
    excel_file.seek(0)
    # Descargar el archivo Excel
    st.download_button(
        label="banxico-muestra-5rutas.xlsx",
        data=excel_file,
        file_name='banxico-muestra-5rutas.xlsx',
        key='download_button_r'
    )

with st.sidebar:
    st.write("Ejemplos de claves: ")
    muestra_claves: pd.DataFrame = load_excel("./pruebas/banxico-muestra-5claves.xlsx")   
    # Crear un archivo Excel en BytesIO
    excel_file = BytesIO()
    muestra_claves.to_excel(excel_file, index=False, engine='xlsxwriter')
    excel_file.seek(0)
    # Descargar el archivo Excel
    st.download_button(
        label="banxico-muestra-5claves.xlsx",
        data=excel_file,
        file_name='banxico-muestra-5claves.xlsx',
        key='download_button_c'
    )

# Titulo principal y pequeña explicación
st.title("Obtener datos :blue[BANXICO] :chart_with_downwards_trend:")

# Configuración inicial
st.subheader("Configuración inicial", divider="blue")
token = st.text_input('Escribir token', placeholder='Ej. f7201901f872ab5be5aa20a0105037a601ba7733d07d0ee5f3efe6a94cc446d9')
token = 'f7201901f872ab5be5aa20a0105037a601ba7733d07d0ee5f3efe6a94cc446d9' if not token else token
st.write("Token escrito: ", token)

st.markdown("Si no se tiene token generarlo en: https://www.banxico.org.mx/SieAPIRest/service/v1/token")



col1, col2 = st.columns(2)
with col1:
   formato_excel = st.radio(
    "Seleccionar formato",
    ["Rutas", "Claves"],
    captions = ["Ej. Sector > Financiamiento e información ... > ", "SF68616"])
   st.write("Tu seleccionaste:", formato_excel)
  

with col2:
   st.write("(Campos opcionales)")
   fecha_inicio = st.date_input("Fecha de inicio", value=None, min_value=datetime(1990, 1, 1), format="DD/MM/YYYY")
   st.write('Tu fecha escrita fue:', fecha_inicio)

   fecha_fin = st.date_input("Fecha final", value=datetime.now(), min_value=datetime(1990, 1, 1), format="DD/MM/YYYY")
   st.write('Tu fecha escrita fue:', fecha_fin)

st.markdown('_Si no se especifica ninguna fecha por defecto se obtiene todo el historial._')

# Seleecion de archivos
st.subheader("Cargar archivos", divider="blue")
uploaded_file = st.file_uploader("Escoger un archivo (Sólo se admite archivos de Excel .xlsx)")
st.write("Archivo que seleccionaste: ", "" if uploaded_file is None else uploaded_file.name)

if uploaded_file is not None:
   mensaje_estado = ""
   
   #progress_text = "Obteniendo series. Espere por favor"
   #my_bar = st.progress(0, text=progress_text)
   try:
      # Obtener series
      # df = pd.read_excel(uploaded_file)
      #[my_bar.progress(percent_complete + 1, text=progress_text) for percent_complete in range(50)]
      df = obtener_serie(uploaded_file, formato_excel, token)
      #[my_bar.progress(percent_complete + 1, text=progress_text) for percent_complete in range(50, 100)]
      
      # Aquii es donde haremos el corte
      if fecha_inicio is not None:
        # Convertir la serie de índices a tipo fecha
        df.index = pd.to_datetime(df.index)

        # Convertir el objeto de tipo date a datetime
        fecha_inicio = datetime.combine(fecha_inicio, datetime.min.time())
        fecha_fin = datetime.combine(fecha_fin, datetime.min.time())

        # Filtrar el DataFrame para obtener solo las filas dentro del intervalo de fechas
        df = df.loc[(df.index >= fecha_inicio) & (df.index <= fecha_fin)]

      st.write(f"Resumen de los datos")
      st.write(df)
      mensaje_estado = "Se obtuvieron con éxito :) ✅"
   except Exception as e:
      st.write(e)
      mensaje_estado = "Hubo un error, verifique sus datos :( ❌"
   st.write(mensaje_estado)
   
   st.subheader("Visualización", divider="blue")
   
   # Selección de la variable
   selected_variable = st.selectbox('Selecciona la variable a graficar:', df.columns)
   
   ruta_completa_variable: str = rutas_variables_usuario[rutas_variables_usuario["NombreVariable"] == selected_variable]["RutaCompleta"].iloc[0]

   # Crear y mostrar la gráfica de líneas
   df_sin_nans = df[selected_variable].dropna()
   #st.line_chart(data=df_sin_nans, y=selected_variable, height=450)
   fig = px.line(df_sin_nans, y=selected_variable)#, title=" ".join(selected_variable.split(" ")[1:]))
   fig.update_layout(
    title=ruta_completa_variable,  # Título principal
    xaxis_title='Eje X',  # Título del eje X
    yaxis_title='Eje Y',  # Título del eje Y
    title_font=dict(size=14),  # Tamaño de fuente del título principal
    title_x=0.06,  # Posición del título principal en el eje X (0.5 = centrado)
    title_y=0.95,  # Posición del título principal en el eje Y
    #title_text=ruta_completa_variable,  # Texto del subtítulo   
)
   # Agregar el subtítulo mediante annotations
   if formato_excel=="Rutas":
      fig.update_layout(
      annotations=[
          dict(
              x=0.0,  # Posición en el eje X (0.5 = centrado)
              y=1.2,  # Posición en el eje Y (negativo para colocarlo debajo del título principal)
              xref="paper",
              yref="paper",
              text="Últimos dos framentos de su ruta:",
              showarrow=False,
              font=dict(size=14)  # Tamaño de fuente del subtítulo
          )
      ]
  )
   st.plotly_chart(fig)

   # Dash
   df_dash = pd.DataFrame(
    {
              "Variable": df.columns,                            
              "Historia": [(df[col].dropna()).tolist() for col in df.columns],
              "Ruta": rutas_variables_usuario["RutaCompleta"],
          }
      )
   st.dataframe(
    df_dash,
    column_config={
        "Variable": "Nombre de la variable",
        "Historia": st.column_config.LineChartColumn(
            "Historia"
        ),
    },
    hide_index=True,
    )
   
   st.subheader("Descargar variables", divider="blue")
   # Crear un archivo Excel en BytesIO
   excel_file = BytesIO()
   imgs_bytes = []
   # Obtenemos todas las graficas
   for i, col in enumerate(df.columns):       
    fig_ = px.line(df[col].dropna(), y=col,  title=" ".join(col.split(" ")[1:]))
    imgs_bytes.append(BytesIO())
    fig_.write_image(imgs_bytes[i], format='png')
   
   with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
  #     # Agregar el DataFrame a la primera hoja
      df.to_excel(writer, sheet_name='Datos', index=True)
      # Agregamos imagenes
      for i, img_bytes1 in enumerate(imgs_bytes):    
        df_img1 = pd.DataFrame({'image': [img_bytes1.getvalue()]})
        df_img1.to_excel(writer, sheet_name='Graficas', index=False, header=False, startrow=i*15, startcol=0)
        
        workbook = writer.book
        worksheet = writer.sheets['Graficas']
        # Crear objetos Image para cada gráfica y agregarlos a la hoja
        worksheet.insert_image(f'A{1 if i==0 else i*26}', 'grafica_linea_{i}.png', {'image_data': img_bytes1})
   
   #df.to_excel(excel_file, index=True, engine='xlsxwriter')
   excel_file.seek(0)
   # Descargar el archivo Excel
   st.download_button(
    label="Descargar variables Excel 📥",
    data=excel_file,
    file_name='variables_usuario_banxico.xlsx',
    key='download_button'
    )
# Reiniciamos ambiente
uploaded_file = None
   



