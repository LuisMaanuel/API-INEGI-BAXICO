
import os
import sys
import pandas as pd 
from INEGIpy import Indicadores

catalogo_path: str = "catalogo/catalogoCompletoINEGI.xlsx"
catalogo: pd.DataFrame = pd.read_excel(catalogo_path)


def construir_catalogo(formato: str):
  if formato.strip() == "Rutas":
    columna_formato = "Variables"
  elif format.strip() == "Claves":
    columna_formato = "Claves"
  return catalogo[["Variables", "Claves"]].set_index(columna_formato).squeeze()

def buscar_rutas(keyword):
  busqueda_se: pd.Series = catalogo["Variables"].apply(lambda x: x.lower().strip().find(keyword))
  keyword = "aluminio"
  indices_busqueda = busqueda_se[busqueda_se != -1].index
  return catalogo.iloc[indices_busqueda]["Variables"].tolist()


def obtener_serie(ruta_archivo: str, formato:str, token:str = "f6a7b69c-5c48-bf0c-b191-5ca98c6a6cc0"):
  # Tomamos siempre la primera columna
  variables_usuario: pd.DataFrame = pd.read_excel(ruta_archivo).iloc[:,0]
  catalogo_se: pd.Series = construir_catalogo(formato)
  
  # Se instancia la interfaz que se counicara con INEGI
  inegi = Indicadores(token)  

  if formato == "Rutas":
    #Para cada variable tendremos que sacar su clave y nombre de la variable
    claves_variables =  variables_usuario.apply(lambda x: catalogo_se[x])
    nombres_variables = variables_usuario.apply(lambda x: x.split(">")[-1])

    # Se obtiene la serie a partir de la API
    variables_df = inegi.obtener_df(indicadores=claves_variables, nombres=nombres_variables)
  
  elif formato == "Claves":
    claves_variables =  variables_usuario["Claves"]
    nombres_variables = variables_usuario.apply(lambda x: catalogo_se[x].split(">")[-1])
    variables_df = inegi.obtener_df(indicadores=claves_variables, nombres=nombres_variables)
  return variables_df

