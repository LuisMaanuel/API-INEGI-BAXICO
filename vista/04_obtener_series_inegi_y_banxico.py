import pickle
import numpy as np
import pandas as pd
import streamlit as st 

from notebook.INEGI import Indicadores

from io import BytesIO
from numpy import nan 
import warnings
import requests
import json
from datetime import datetime
import plotly.express as px
import plotly.io as pio

import xlsxwriter
from openpyxl import Workbook
from openpyxl.drawing.image import Image


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





def obtener_serie(ruta_archivo: str, formato:str, token:str = ""):
  global rutas_variables_usuario
  # Tomamos siempre la primera columna

  archivo = pd.read_excel(ruta_archivo)
  variables_usuario: pd.Series = archivo.iloc[:,0]
  # Las claves son cadenas
  # Las rutas seran cadenas

  #st.write(variables_usuario.iloc[0])
  catalogo_se: pd.Series = construir_catalogo(formato)


  variables_df = pd.DataFrame({"Mensaje": ["No entro en ninguno de los condicionales programadas (if) reportar"]})

  variables_usuario_ = variables_usuario[variables_usuario.isin(catalogo_se.index)]

  if formato == "Rutas":
    #Para cada variable tendremos que sacar su clave y nombre de la variable


    # Filtramos aquellas variables que son validas-------------------
    variables_filtro = variables_usuario.isin(catalogo_se.index)
    variables_usuario_ = variables_usuario[variables_filtro]
    
    # En el caso que haya más de dos claves se seleciona la longitud maxima (SOLUCION PROVISIONAL)
    claves_variables =  variables_usuario_.apply(lambda x: max(catalogo_se[x]) if type(catalogo_se[x]) is not np.int64 else catalogo_se[x])
    #st.write(claves_variables)
  

    if len(archivo.columns) > 1:
        ## obtenemos los nombres de las columnas en caso de que existan,
        ## por defecto se estan considerando que los nombres estan en la segunda columna
        nombres_variables = archivo.iloc[:,1].values
        nombres_variables = nombres_variables[variables_filtro]

        
    else:
        nombres_variables = variables_usuario_.apply(lambda x: x.split(">")[-1])
        #st.write(nombres_variables)
        # Hace unico los nombres, pero no esta excento que la ruta la pongan dos veces
        nombres_variables = [str(clave) + nombre for clave, nombre in zip(claves_variables, nombres_variables)]

    if len(variables_usuario_) != len(variables_usuario):
       col1, col2 = st.columns(2)
       with col1:
          st.write(f"Claves que no se puedieron encontrar: {len(variables_usuario)-len(variables_usuario_)}")
       with col2:          
          excel_file = BytesIO()
          no_encontradas = archivo[-variables_usuario.isin(catalogo_se.index)]
          no_encontradas.to_excel(excel_file, index=False, engine='xlsxwriter')
          excel_file.seek(0)
          # Descargar el archivo Excel
          st.download_button(
              label="Variables no encontradas 📥",
              data=excel_file,
              file_name='variables_no_encontradas.xlsx',
              key='download_button_nofind'
          )
          

  # Convertir todo cadena
  claves_variables = claves_variables.astype(str)
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
    df[columna] = df[columna].replace("N/E", np.nan)
  return df