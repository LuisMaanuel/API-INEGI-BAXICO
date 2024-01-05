import streamlit as st
import pandas as pd
import numpy as np
import pickle
import re 
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

def eliminar_puntuacion(texto_minuscula):
    texto_m_sp = re.sub(r'\W+', ' ', texto_minuscula)
    return texto_m_sp


# 2) La primera vez siempre correra rapido, las siguientes seran muy veloces
catalogo: pd.DataFrame = load_data_objeto('./catalogo/catalogoINEGI.pkl')
#st.write(catalogo.shape)
pd.set_option("styler.render.max_elements", 2491280)

# Titulo principal y pequeña explicación
st.title("Buscar rutas 🔎")
st.write("A partir de una palabra buscaremos todas rutas donde aparecen.")

texto = """

__Guía de uso__

- Se puede utilizar una palabra para la busqueda.

> Ej. Desempleo

Esto buscará todas las rutas con la palabra desempleo.

- Se puede usar con más de una palabra utilizando el separador coma(,).
    
 > Ej. Desempleo, mujeres

Esto buscará todas las rutas donde se encuentre desempleo y muejeres.
"""

# Configuración inicial
st.subheader("Configuración inicial", divider="blue")
keyword = st.text_input('Escribir palabra', placeholder='Ej. aluminio')
st.write("Palabra escrita:", keyword)
st.write(texto)


# Le damos un formato uniforme
keyword = keyword.lower().strip()


def estan_oracion(frase_completa, list_keywords):
   texto_minuscula: str = frase_completa.lower().strip()
   texto_sin_puntuacion: list = eliminar_puntuacion(texto_minuscula).split()
   # Deben de estar ambas palabras en la oracion
   return all([keyword.lower().strip() in texto_sin_puntuacion for keyword in list_keywords])

# 1) Primero buscamos por la sentencia completa - [optimizacion]
def buscar_rutas(keyword:str):
  global catalogo
  if ',' in keyword:
    # Contiene más de 2 malabras
    list_keywords = keyword.split(",")
    busqueda_se: pd.Series = catalogo["Variables"].apply(lambda frase_completa: estan_oracion(frase_completa, list_keywords))
  else:
    # Contiene una palabra
    busqueda_se: pd.Series = catalogo["Variables"].apply(lambda frase_completa: estan_oracion(frase_completa, [keyword]))
  indices_busqueda = busqueda_se[busqueda_se].index
  return catalogo.iloc[indices_busqueda][["Variables"]]

# Función de formato que acepta argumentos adicionales
def colorear_celda(value, keyword):   
   if value is not None:
    # Normalizamos el texto
    texto_minuscula: str = value.lower().strip()
    keyword = keyword.lower().strip()
    texto_sin_puntuacion: list = eliminar_puntuacion(texto_minuscula).split()
    #st.write(texto_sin_puntuacion)
    #st.write(keyword)
    if ',' in keyword:
       # Mas de 2 palabras
       list_keywords = keyword.split(",")
       list_keywords = [keyword.lower().strip() for keyword in list_keywords]
       # Dos enfoque en la oracion que contengan las dos palabras
       if all(keyword in texto_sin_puntuacion for keyword  in list_keywords):
          return 'background-color: yellow'
       # En los niveles tengas las dos palaabras
       if any(keyword in texto_sin_puntuacion for keyword  in list_keywords):
          return 'background-color: yellow'
    else:
       # Una palabra   
       if keyword in texto_sin_puntuacion:
          return 'background-color: yellow'
    
if keyword != "":
  
  # Buscamos en la cadena completa que este la keyword 
  keyword = keyword.lower().strip()
  data_keyword: pd.DataFrame = buscar_rutas(keyword)
  # 2) Despues por nivel
  rutas_separadas: pd.DataFrame = data_keyword["Variables"].str.split('>', expand=True)
      
  # Aplicar la función de formato con argumentos adicionales usando applymap
  #styled_df = rutas_separadas.style.applymap(colorear_celda)
  styled_df = rutas_separadas.style.map(lambda value: colorear_celda(value, keyword))
  st.subheader("Rutas encontradas", divider="blue")
  st.dataframe(styled_df)
  
  st.subheader("Descargar rutas", divider="blue")
  # csv = convert_df(data_keyword)  
#   st.download_button(
#                     label='Descargar rutas como CSV 📥',
#                     data=csv,
#                     file_name= 'rutas-usuarios-inegi.csv',
#                     mime='text/csv'
#                     )
  # Crear un archivo Excel en BytesIO
  excel_file = BytesIO()
  data_keyword.to_excel(excel_file, index=False, engine='xlsxwriter')
  excel_file.seek(0)
  
  # Descargar el archivo Excel
  st.download_button(
    label="Descargar rutas Excel 📥",
    data=excel_file,
    file_name='rutas_usuario_inegi.xlsx',
    key='download_button'
    )


# Reiniciamos ambiente
keyword = ""

