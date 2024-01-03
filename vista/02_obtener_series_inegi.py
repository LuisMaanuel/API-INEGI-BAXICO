from pyxlsb import open_workbook as open_xlsb
from INEGIpy import Indicadores
from io import BytesIO

import streamlit as st 
import pandas as pd

#/Users/guillermo/Documents/trabajo/API-INEGI-BANXICO/vista/catalogoCompletoINEGI.xlsx
catalogo_path: str = r"./catalogo/catalogoCompletoINEGI.xlsx"
catalogo: pd.DataFrame = pd.read_excel(catalogo_path)

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

  if formato == "Rutas":
    #Para cada variable tendremos que sacar su clave y nombre de la variable
    claves_variables =  variables_usuario.apply(lambda x: catalogo_se[x])
    nombres_variables = variables_usuario.apply(lambda x: x.split(">")[-1])

    # Se obtiene la serie a partir de la API
    variables_df = inegi.obtener_df(indicadores=claves_variables, nombres=nombres_variables)
  
  elif formato == "Claves":
    claves_variables =  variables_usuario
    nombres_variables = variables_usuario.apply(lambda x: catalogo_se[x].split(">")[-1])
    variables_df = inegi.obtener_df(indicadores=claves_variables, nombres=nombres_variables)
  return variables_df


# Titulo principal y pequeña explicación
st.title("Obtener datos :green[INEGI] :chart_with_downwards_trend:")
st.write("Aqui se obtendra las series de Inegi")

# Configuración inicial
st.subheader("Configuración inicial", divider="green")
token = st.text_input('Escribir token', placeholder='Ej. f6a7b69c-5c48-bf0c-b191-5ca98c6a6cc0')
token = 'f6a7b69c-5c48-bf0c-b191-5ca98c6a6cc0' if not token else token

st.write("Token escrito: ", token)

formato_excel = st.radio(
    "Seleccionar formato",
    ["Rutas", "Claves"],
    captions = ["Ej. Manufactura > extracción > ... ", "802342"])

st.write("Tu seleccionaste:", formato_excel)

# Seleecion de archivos
st.subheader("Cargar archivos", divider="green")
uploaded_file = st.file_uploader("Escoger un archivo")

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
   except:
      mensaje_estado = "Hugo un error, verifique sus datos :( ❌"
   st.write(mensaje_estado)
   
   # # Descargar las series
   def convertir_df_a_excel(df):
      output = BytesIO()
      writer = pd.ExcelWriter(output, engine='xlsxwriter')
      #df.set_index(pd.to_datetime(df.index.get_level_values("fechas")),inplace=True, drop=True)
      df.to_excel(writer, index=True, sheet_name='Sheet1')
      workbook = writer.book
      worksheet = writer.sheets['Sheet1']
      #format1 = workbook.add_format({'num_format': '0.00'}) 
      #worksheet.set_column('A:A', None, format1)  
      writer.close()
      processed_data = output.getvalue()
      return processed_data
   
   # excel_final = convertir_df_a_excel(df)

   # st.subheader("Descargar variables", divider="green")
   
   # st.download_button(
   #                    label='Descargar series en Excel📥',
   #                    data=excel_final,
   #                    file_name= 'variables-usuario.xlsx'
   #                    )


