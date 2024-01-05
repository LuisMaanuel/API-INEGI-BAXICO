import pickle
import pandas as pd
import streamlit as st 
from INEGIpy import Indicadores
from io import BytesIO

@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

@st.cache_data
def load_data(url):
    df = pd.read_excel(url)
    return df

@st.cache_data
def load_data_objeto(url):
    with open(url, 'rb') as f:
        # Cargar el objeto desde el archivo
        catalogo_inegi = pickle.load(f)
    return catalogo_inegi

# 1) La primera vez tardara, las siguientes seran muy veloces
#catalogo_path: str = r"./catalogo/catalogoCompletoINEGI.xlsx"
#catalogo: pd.DataFrame = load_data(catalogo_path)

# 2) La primera vez siempre correra rapido, las siguientes seran muy veloces
catalogo: pd.DataFrame = load_data_objeto('./catalogo/catalogoINEGI.pkl')


def construir_catalogo(formato: str):
  if formato.strip() == "Rutas":
    columna_formato = "Variables"
  elif formato.strip() == "Claves":
    columna_formato = "Claves"
  return catalogo[["Variables", "Claves"]].set_index(columna_formato).squeeze()


def obtener_serie(ruta_archivo: str, formato:str, token:str = "f6a7b69c-5c48-bf0c-b191-5ca98c6a6cc0"):
  # Tomamos siempre la primera columna
  variables_usuario: pd.Series = pd.read_excel(ruta_archivo).iloc[:,0]
  catalogo_se: pd.Series = construir_catalogo(formato)
  
  # Se instancia la interfaz que se counicara con INEGI
  inegi = Indicadores(token)  
  variables_df = pd.DataFrame({"Mensaje": ["No entro en ninguno de los condicionales programadas (if) reportar"]})
  if formato == "Rutas":
    #Para cada variable tendremos que sacar su clave y nombre de la variable
    claves_variables =  variables_usuario.apply(lambda x: catalogo_se[x])
    nombres_variables = variables_usuario.apply(lambda x: x.split(">")[-1])
    nombres_variables = [str(clave) + nombre for clave, nombre in zip(claves_variables, nombres_variables)]
    # Se obtiene la serie a partir de la API
    variables_df = inegi.obtener_df(indicadores=claves_variables, nombres=nombres_variables)
  
  elif formato == "Claves":
    claves_variables =  variables_usuario
    nombres_variables = variables_usuario.apply(lambda x: catalogo_se[x].split(">")[-1])
    nombres_variables = [str(clave) + nombre for clave, nombre in zip(claves_variables, nombres_variables)]
    variables_df = inegi.obtener_df(indicadores=claves_variables, nombres=nombres_variables)
  return variables_df


# Titulo principal y pequeña explicación
st.title("Obtener datos :green[INEGI] :chart_with_downwards_trend:")
st.write("Aqui se obtendra las series de Inegi")

# Configuración inicial
st.subheader("Configuración inicial", divider="green")
token = st.text_input('Escribir token', placeholder='Ej. f6a7b69c-5c48-bf0c-b191-5ca98c6a6cc0')
token = 'c64be54e-1842-acb9-0843-baad4ab4aa56' if not token else token
st.write("Token escrito: ", token)

st.markdown("Si no se tiene token generarlo en: https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify")

formato_excel = st.radio(
    "Seleccionar formato",
    ["Rutas", "Claves"],
    captions = ["Ej. Manufactura > extracción > ... ", "802342"])

st.write("Tu seleccionaste:", formato_excel)

# Seleecion de archivos
st.subheader("Cargar archivos", divider="green")
uploaded_file = st.file_uploader("Escoger un archivo")
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
      
      st.write(f"Resumen de los datos")
      st.write(df)
      mensaje_estado = "Se obtuvieron con éxito :) ✅"
   except Exception as e:
      st.write(e)
      mensaje_estado = "Hubo un error, verifique sus datos :( ❌"
   st.write(mensaje_estado)
      
   st.subheader("Descargar variables", divider="green")
  #  csv = convert_df(df)
  #  st.download_button(
  #                   label='Descargar variables como CSV 📥',
  #                   data=csv,
  #                   file_name= 'variables-usuario-inegi.csv',
  #                   mime='text/csv'
  #                   )
   
   # Crear un archivo Excel en BytesIO
   excel_file = BytesIO()
   df.to_excel(excel_file, index=True, engine='xlsxwriter')
   excel_file.seek(0)
   # Descargar el archivo Excel
   st.download_button(
    label="Descargar variables Excel 📥",
    data=excel_file,
    file_name='variables_usuario_inegi.xlsx',
    key='download_button'
    )
# Reiniciamos ambiente
uploaded_file = None
   



