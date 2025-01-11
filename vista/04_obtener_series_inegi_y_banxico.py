import pickle
import numpy as np
import pandas as pd
import streamlit as st 

from notebook.INEGI import Indicadores
from sie_banxico import SIEBanxico


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


## obtener serie INEGI
catalogo_INEGI: pd.DataFrame = load_data_objeto('./catalogo/catalogoINEGI.pkl')
def construir_catalogo(formato: str):
  if formato.strip() == "Rutas":
    columna_formato = "Variables"
  elif formato.strip() == "Claves":
    columna_formato = "Claves"
  tmp = catalogo_INEGI[["Variables", "Claves"]].set_index(columna_formato).squeeze()
  return tmp 


def obtener_serie_INEGI(ruta_archivo: pd.DataFrame, formato:str, token:str = "f6a7b69c-5c48-bf0c-b191-5ca98c6a6cc0"):
  global rutas_variables_usuario_1
  
  # archivo = pd.read_excel(ruta_archivo)
  archivo = ruta_archivo
  # Tomamos siempre la primera columna
  variables_usuario: pd.Series = archivo.iloc[:,0]
  catalogo_se: pd.Series = construir_catalogo(formato)

  # Se instancia la interfaz que se counicara con INEGI
  inegi = Indicadores(token)  
  variables_df = pd.DataFrame({"Mensaje": ["No entro en ninguno de los condicionales programadas (if) reportar"]})
  if formato == "Rutas":
    #Para cada variable tendremos que sacar su clave y nombre de la variable


    # Filtramos aquellas variables que son validas
    variables_filtro = variables_usuario.isin(catalogo_se.index)
    variables_usuario_ = variables_usuario[variables_filtro]
    
    # En el caso que haya más de dos claves se seleciona la longitud maxima (SOLUCION PROVISIONAL)
    claves_variables =  variables_usuario_.apply(lambda x: max(catalogo_se[x]) if type(catalogo_se[x]) is not np.int64 else catalogo_se[x])
    #st.write(claves_variables)
  

    if len(archivo.columns) > 2:
        ## obtenemos los nombres de las columnas en caso de que existan,
        ## por defecto se estan considerando que los nombres estan en la segunda columna
        nombres_variables = archivo.iloc[:,-1].values
        nombres_variables = nombres_variables[variables_filtro]

        
    else:
        nombres_variables = variables_usuario_.apply(lambda x: x.split(">")[-1])
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

    # Se obtiene la serie a partir de la API
    variables_df = inegi.obtener_df(indicadores=claves_variables.tolist(), nombres=nombres_variables, banco="BIE")
    
    rutas_variables_usuario_1 = pd.DataFrame({"RutaCompleta": variables_usuario_, "NombreVariable": nombres_variables})
  
  elif formato == "Claves":
    claves_variables =  variables_usuario

    # Filtramos aquellas variables que son validas-------------------
    claves_filtro = claves_variables.isin(catalogo_se.index)
    claves_variables = claves_variables[claves_filtro]

    if len(claves_variables) != len(variables_usuario):
       col1, col2 = st.columns(2)
       with col1:
          st.write(f"Claves que no se puedieron encontrar: {len(variables_usuario)-len(claves_variables)}")
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
              key='download_button_nofind_'
          )
    if len(archivo.columns) > 2:
        ## obtenemos los nombres de las columnas en caso de que existan,
        ## por defecto se estan considerando que los nombres estan en la segunda columna
        nombres_variables = archivo.iloc[:,-1].values
        nombres_variables = nombres_variables[claves_filtro]

        
    else:
        nombres_variables = claves_variables.apply(lambda x: catalogo_se[x].split(">")[-1])
        nombres_variables = [str(clave) + nombre for clave, nombre in zip(claves_variables, nombres_variables)]

    rutas_variables_usuario_1 = pd.DataFrame({"RutaCompleta": claves_variables.apply(lambda x: catalogo_se[x]), "NombreVariable": nombres_variables})

    # Convertir todo cadena
    claves_variables = claves_variables.astype(str)
    claves_variables = claves_variables.tolist()

    # Quitamos duplicados
    # claves_variables = list(set(claves_variables))
    # nombres_variables = list(set(nombres_variables))

    variables_df = inegi.obtener_df(indicadores=claves_variables, nombres=nombres_variables, banco="BIE")
        
  # damos el formato adecuado de las fechas para inegi
  variables_df.reset_index(inplace=True)
  
  variables_df['fechas'] = variables_df['fechas'].apply(lambda x: x+'/01/01' if len(x) == 4 else x + '/01')
  variables_df = variables_df.groupby('fechas', as_index=False).agg('first').sort_values(by='fechas',ascending=True)

  variables_df.fechas = pd.to_datetime(variables_df.fechas, format='%Y/%m/%d').dt.date#datestrftime('%Y-%m-%d')
  variables_df.rename({'fechas':'fecha'}, axis=1, inplace=True)
  #variables_df.set_index('fecha',inplace=True)

  return variables_df









## obtener serie de banxico
catalogo_banxico: pd.DataFrame = load_data_objeto('./catalogo/catalogoBANXICO.pkl')

def construir_catalogo_BANXICO(formato: str):
  if formato.strip() == "Rutas":
    columna_formato = "Ruta"
  elif formato.strip() == "Claves":
    columna_formato = "Clave"
  tmp = catalogo_banxico[["Ruta", "Clave"]].set_index(columna_formato).squeeze()
  return tmp 


def obtener_serie_BANXICO(ruta_archivo: pd.DataFrame, formato:str, token:str = ""):
  global rutas_variables_usuario_2
  # Tomamos siempre la primera columna
  #variables_usuario: pd.Series = pd.read_excel(ruta_archivo).iloc[:,0]
  archivo = ruta_archivo
  variables_usuario: pd.Series = archivo.iloc[:,0]
  # Las claves son cadenas
  # Las rutas seran cadenas

  catalogo_se: pd.Series = construir_catalogo_BANXICO(formato)


  variables_df = pd.DataFrame({"Mensaje": ["No entro en ninguno de los condicionales programadas (if) reportar"]})

  variables_usuario_ = variables_usuario[variables_usuario.isin(catalogo_se.index)]

  variables_filtro = variables_usuario.isin(catalogo_se.index)
  variables_usuario_ = variables_usuario[variables_filtro]


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
  
  variables_usuario = variables_usuario_  
  # Filtramos 
  if formato == "Rutas":
    #Para cada variable tendremos que sacar su clave y nombre de la variable    
    # En el caso que haya más de dos claves se seleciona la longitud maxima (SOLUCION PROVISIONAL)
    # Cada ruta debe debe tener una clave unica
    # Como solucion provisional en el caso tengas más de una clave se toma la primero(ESTO SE DEBE REVISAR PORQUE SE TIENE MÁS DE UNA CLAVE)
    claves_variables =  variables_usuario.apply(lambda x: catalogo_se[x] if  type(catalogo_se[x]) is str else catalogo_se[x].iloc[0])
    nombres_variables = variables_usuario.apply(lambda x: x.split(">")[-1] if x.split(">")[-1] else x.split(">")[-2])
    #st.write('asefasdfdsf')
    #st.write(variables_usuario)
    rutas = variables_usuario.copy()

  elif formato == "Claves":
    # En esta parte se trata cuando se tiene la misma clave con diferentes rutas
    claves_variables =  variables_usuario
    nombres_variables = variables_usuario.apply(lambda x: catalogo_se[x] if  type(catalogo_se[x]) is str else catalogo_se[x].iloc[0])
    rutas = nombres_variables.copy()

  if len(archivo.columns) > 2:
      ## obtenemos los nombres de las columnas en caso de que existan,
      ## por defecto se estan considerando que los nombres estan en la segunda columna
      nombres_variables = archivo.iloc[:,-1].values
      nombres_variables = nombres_variables[variables_filtro]
      
  else:
      rutas = nombres_variables
      nombres_variables_ = nombres_variables.apply(lambda x: x.split(">")[-1])
      #st.write(nombres_variables)
      # Hace unico los nombres, pero no esta excento que la ruta la pongan dos veces
      nombres_variables = [str(clave) + ' '+ nombre for clave, nombre in zip(claves_variables, nombres_variables_)]
  # Convertir todo cadena
  claves_variables = claves_variables.astype(str)

  # Hace unico los nombres, pero no esta excento que la ruta la pongan dos veces
  #nombres_variables = [str(clave) + " " + nombre for clave, nombre in zip(claves_variables, nombres_variables)]
  
  # Mayor verificacion, quitar los duplicados de la lista si es que existen
  #claves_variables = list(set(claves_variables))
  #nombres_variables = list(set(nombres_variables))
  rutas_variables_usuario_2 = pd.DataFrame({"RutaCompleta": rutas, "NombreVariable": nombres_variables})
  
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

  df.reset_index(inplace=True)
  df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True).dt.date#.strftime('%Y-%m')
  df.sort_values(by='fecha' ,axis=0, inplace=True)
  #df.set_index('fecha', inplace=True)
  for col in df.columns:
     if col != 'fecha':
        df[col] = df[col].astype(float)

  return df






def get_trimestrales(df, cjt_fechas: dict = {'01','02','03','04'}, diaria:bool = False):
   '''
   Parameters: df, pandas dataframe donde el index es la fecha
   Return: Lista con los nombres de las series trimestrales

   Una serie trimestral tiene a lo mas 4 registros por año, por lo que si nosotros tenemos una serie que va desde el
   2010 hasta el 2020 entonces tenemos 10 años, por  lo que la serie trimestral debe tener mas de 3 registros al año y a lo mas 4
   lo cual nos da una cota en el ejemplo de mas 30 registros y a lo mas 40.
   
   Creamos un conjunto {01, 02, 03, 04} e iteramos sobre las fechas de cada serie donde si tenemos registros validos
   (2020/01, 2020/02, 2020/03, 2020/04) y quitamos el año.




   Nota: Esta funcion esta diseñada para identificar series trimestrales por el el conjunto cjt_fechas, pero si dicho conjunto
   se modifica a {'01','02','03'} la funcion detectaria series cuatrimestrales (pues solo hay 3 cuatrimestres por año).
   Asi que es importante llamar la funcion con un cjt_fechas adecuado segun sean las series que se quieren detectar.
   '''
   trimestrales = []

   
   for col in df.columns:
       cjt = set()
       count = 0
       filter = df[col].dropna()
       filter= filter.to_frame().reset_index()
       for fecha in filter['fecha']:
          cjt.add(str(fecha)[5:7] if not diaria else str(fecha)[-2:]) # esta condicion nos ayuda a detectar series diarias
          count += 1
        
          if count == 13:        
            if diaria and len(cjt) > 6:
              trimestrales.append(col) 

            else:
               if cjt == cjt_fechas:
                  trimestrales.append(col)
            break

   return trimestrales

mapper = {
    '01':'03',
    '02':'06',
    '03':'09',
    '04':'12',
}
def trimestres_a_anual(df,columns, mapper: dict = mapper):
    '''
    esta funcion convierte no solo fechas trimestrales del tipo 2020/01, 2020/02, 2020/03 y 2020/04 al fechas mensuales
    del tipo 2020/03, 2020/06, 2020/09 y 2020/12. Ya que depende el mapper (diccionario) que se le ingrese, por defecto
    este diseñado para convertir fechas trimestrales a mensuales.
    
    Pero esta funcion sirve para convertir bimestrales, cuatrimestrales etc. A fechas mensuales dependiendo del mapper
    '''
    trimes = df[columns]
    if not trimes.empty:
        trimes = trimes.dropna().reset_index()
        #st.write('trimes')
        #st.write(trimes)
        trimes['fecha'] = trimes['fecha'].apply(lambda x: str(x)[:5] + mapper[ str(x)[5:7]] + str(x)[7:]  ) 
        trimes.fecha = pd.to_datetime(trimes.fecha, format='%Y-%m-%d').dt.date
        return trimes
    return pd.DataFrame()









# -----------------------------
# -----------------------------
# -----------------------------                 INTERFAZ
# -----------------------------
# -----------------------------




# -----------------------------
# -----------------------------                 Titulo principal y pequeña explicación
# -----------------------------


st.title("Obtener datos :green[INEGI] 📊 y :blue[BANXICO] :chart_with_downwards_trend:")

st.write("Aqui se obtendra las series de INEGI y BANXICO a la par sin la necesidad de descargar las series en archivos separados")

# Estructura de los datos a subir
st.subheader("Estructura de los datos a subir", divider="orange")
st.write('Para un correcto funcionamiento, es importante que el archivo excel (.xlsx) tenga la siguiente estructura.')


st.markdown('- **Primer columa**: corresponde a la clave o ruta (todas deben de ser claves o rutas) de la serie a descargar')
st.markdown('- **Segunda columna**: indica si la serie es de BANXICO o INEGI. Es importante especificar de que fuente se debe extraer la serie.')
st.markdown('''- **Tercer columna**: es el nombre deseado para dicha serie, **la cual opcional pero recomendable**. Si se estan subiendo datos sin esta columna se 
                asignara por defecto la clave y nombre de la serie, lo cual por la clave se asegura que aunque dos series se llamen igual (indice general) 
                la clave hace que el nombre asignado sea unico.''')

st.markdown('''**_En el caso de realizar una busqueda por rutas y no proporcionar los nombres deseados no se asegura que el orden en el que se regresan las variables 
                sea el mismo que cuando se subieron. Esto puede afectar en la seccion de comparación, ya que al tener distintos ordenes, 
                cuando se comparen los dos archivos puede que se esten comparando dos columnas (series económicas) que no son iguales._**''')



st.write('Ejemplo de la estructura con claves')

claves_df = load_excel('./catalogo/IYB/IYB_claves.xlsx')#, engine='openpyxl')
claves_df['Clave'] = claves_df['Clave'].astype(str)
st.write(claves_df)
del claves_df

st.write('Ejemplo de la estructura con rutas')
st.write(load_excel('./catalogo/IYB/IYB_rutas.xlsx'))

# -----------------------------
# -----------------------------                 Sidebar con archivos de muestra
# -----------------------------

with st.sidebar:
    st.write('Ejemplos de rutas:')
    muestra_rutas: pd.DataFrame = load_excel('./catalogo/IYB/IYB_rutas.xlsx')
    # crear un archivo excel con BytesIO
    excel_file = BytesIO()
    muestra_rutas.to_excel(excel_file, index=False, engine='xlsxwriter')
    excel_file.seek(0)
    
    # descargar el archivo excel
    st.download_button(label='ingei-banxico-7rutas.xlsx',
                       data = excel_file,
                       file_name='ingei-banxico-7rutas.xlsx',
                       key='download_button_r')

with st.sidebar:
    st.write('Ejemplos de claves:')
    muestra_claves: pd.DataFrame = load_excel('./catalogo/IYB/IYB_claves.xlsx')
    # crear un archivo excel con BytesIO
    excel_file = BytesIO()
    muestra_claves.to_excel(excel_file, index=False, engine='xlsxwriter')
    excel_file.seek(0)
    
    # descargar el archivo excel
    st.download_button(label='ingei-banxico-7claves.xlsx',
                       data = excel_file,
                       file_name='ingei-banxico-7claves.xlsx',
                       key='download_button_c')



# -----------------------------
# -----------------------------                 Configuracion inicial
# -----------------------------

#   OBTENCION DE TOKENS
st.subheader("Configuración inicial", divider="orange")
token_INEGI = st.text_input('Escribir token de INEGI', placeholder='Ej. c64be54e-1842-acb9-0843-baad4ab4aa56')
token_INEGI = 'c64be54e-1842-acb9-0843-baad4ab4aa56' if not token_INEGI else token_INEGI
st.write("Token escrito: ", token_INEGI)
st.markdown("Si no se tiene token generarlo en: https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify")


token_BANXICO = st.text_input('Escribir token de BANXICO', placeholder='Ej. ec23db1f8fe83ebccc948d7968e962d7368bd761adb592c16ebe27a8d9e7366d')
token_BANXICO = 'ec23db1f8fe83ebccc948d7968e962d7368bd761adb592c16ebe27a8d9e7366d' if not token_BANXICO else token_BANXICO
st.write("Token escrito: ", token_BANXICO)
st.markdown("Si no se tiene token generarlo en: https://www.banxico.org.mx/SieAPIRest/service/v1/token")




col1, col2 = st.columns(2)
with col1:
    formato_excel = st.radio(
        'Seleccionar formato', ['Rutas','Claves'],
        captions=["Ej. Manufactura > extracción > ... ", "802342"])
    st.write('Tu seleccionaste:', formato_excel)
with col2:
    st.write("(Campos opcionales)")
    fecha_inicio = st.date_input('Fecha de inicio', value = None, min_value=datetime(1990,1,1), format='DD/MM/YYYY')
    st.write('Tu fecha escrita fue:', fecha_inicio)

    fecha_fin = st.date_input('Fecha final', value=datetime.now(), min_value=datetime(1990,1,1), format='DD/MM/YYYY')
    st.write('Tu fecha esscrita fue:', fecha_fin)

st.markdown('_Si no se especifica ninguna fecha por defecto se obtiene todo el historial._')

# seleccion de archivos
st.subheader('Cargar archivos', divider='orange')
uploaded_file = st.file_uploader('Escoger un archivo (Solo se admite archivos de Excel .xlsx)')
st.write('Archivo que seleccionaste: ', '' if not uploaded_file else uploaded_file.name)


# si se subio un archivo procedemos a obtener las series
if uploaded_file:
    try:
      data = pd.read_excel(uploaded_file)
    # la segunda columna (correspondiente a INEGI O BANXICO) la pasamos a mayusculas
      data[data.columns[1]] = data[data.columns[1]].apply(lambda x: x.upper())
      
      # segmentamos los datos de INEGI y BANXICO
      data_inegi = data[data[data.columns[1]] == 'INEGI']
      data_banxico = data[data[data.columns[1]] == 'BANXICO']
      


      ##############
      ############## obtencion de series de INEGI
      ##############
      df_inegi = obtener_serie_INEGI(data_inegi, formato_excel, token_INEGI) #if not data_inegi.empty() else None

      ##############
      ############## obtencion de series de BANXICO
      ##############

      df_banxico = obtener_serie_BANXICO(data_banxico, formato_excel, token_BANXICO) #if not data_banxico.empty() else None


      ## se juntan los datos de inegi y banxico
      df = pd.concat([df_inegi, df_banxico]).groupby('fecha', as_index=False).agg('first')\
          .sort_values(by='fecha',ascending=True).set_index('fecha')


      ## encontramos las series bimestrales, trimestrales, cuatrimestrales, semestrales y las ponemos en el formato adecuado
      columns = df.columns.to_list()
      dfs_temporales = []
      for (cjt, freq) in [({f'0{i}' if i < 10 else str(i) for i in range(1,31)} , True), 
                          ({'01','02','03','04','05','06'}, False),
                          ({'01','02','03','04'}, False),
                          ({'01','02','03'}, False), ({'01','02'}, False) ]:
        
        # obtenemos los nombres de las series
        temporales_nombres = get_trimestrales(df[columns], cjt, diaria= freq)
        # actualizamos los nombres de las columnas restantes
        columns = [name for name in columns if name not in temporales_nombres]

        # si es serie diaria almacenamos el nombre para darle un tratamiento especifico
        if freq: 
           diarias_names = temporales_nombres

        # en caso contrario convertimos las fechas y agregamos el df a una lista
        else:
          dfs_temporales.append( trimestres_a_anual(df, temporales_nombres) )
      
      # mostramos un df con las series diarias
      st.write('diarias')
      st.write(diarias_names)
      df_diario = df[diarias_names].dropna()
      st.write(df_diario)


      ## obtenemos el ultimo registro de cada serie diaria para agregarlos al df de series mensuales

      df_diario.reset_index(inplace=True)
      df_diario["fecha"] = pd.to_datetime(df_diario["fecha"])
      ultimo_por_mes = df_diario.groupby(df_diario["fecha"].dt.to_period("M"), as_index=False).last()
      
      ultimo_por_mes["fecha"] = pd.to_datetime(ultimo_por_mes["fecha"]).dt.date




      # agregamos el df mensualizado a la lista de todos los dfs
      dfs_temporales.append(ultimo_por_mes)
      
      
      # obtenemos un dataframe donde las series existentes son solamente mensuales
      # lo usaremos para unir los demas data frames
      df = df[columns]
      

      # unimos todos los dfs
      for df_temporal in dfs_temporales:
         df = df.merge(df_temporal, how='left',on='fecha') if not df_temporal.empty else df
      

         
#      trimestrales = get_trimestrales(df)
#      trimestrales_df = trimestres_a_anual(df, trimestrales, mapper)
      #st.write('trimestrales df')
      #st.write(trimestrales_df)
      #st.write(trimestrales_df.dtypes)

#      no_trimestrales = df[[col for col in df.columns if col not in trimestrales] ]
#      no_trimestrales.reset_index(inplace=True)
      #st.write('no trimestrales')
      #st.write(no_trimestrales)
      #st.write(no_trimestrales.dtypes)
      
      
#      df = no_trimestrales.merge(trimestrales_df, how='left',on='fecha') if not trimestrales_df.empty else no_trimestrales
      #st.write('df 2')
      #st.write(df)

      #df.reset_index(True)
      df.fecha = pd.to_datetime(df.fecha, format='%Y/%m/%d').dt.date
      df_diario['fecha'] = pd.to_datetime(df_diario['fecha']).dt.date
      #df.set_index('fecha', inplace=True)




      ## filtramos los datos por fecha de inicio y de fin
      if fecha_inicio:

        df = df[(df.fecha >= fecha_inicio) & (df.fecha <= fecha_fin)]
        df_diario = df_diario[(df_diario.fecha >= fecha_inicio) & (df_diario.fecha <= fecha_fin)]
      df.set_index('fecha', inplace=True)
      df.dropna(inplace=True, how='all')

      
      df.columns = [' '.join(col.strip().split()) for col in df.columns]
      #st.write('new cols')
      #st.write(df.columns)

      rutas_variables_usuario = pd.concat([rutas_variables_usuario_1,rutas_variables_usuario_2])
      #st.write('rutas_variables')
      #st.write(rutas_variables_usuario)
      rutas_variables_usuario["NombreVariable"] = [' '.join(col.strip().split()) for col in rutas_variables_usuario["NombreVariable"] ]
      #rutas_variables_usuario = rutas_variables_usuario.set_index('NombreVariable').T[df.columns].T.reset_index()
      #st.write('rutas_variables 2')
      #st.write(rutas_variables_usuario)

      ## selecionamos las variables en el orden que fueron proporcionadas
      if len(data.columns) > 2: # caso en el que los nombres de las variables fueron proporcionadas
         df = df[data[data.columns[-1]].values]
      
      else: # caso en el que  no fueron proporcionadas las variables
        
        ## obtenemos la primer ruto o clave del conjunto proporcionado por el usuario
        try:
          nombre = data.iloc[0,0].split('>')[-1]
        except:
          nombre = data.iloc[0,0]
        
        ## revisamos su coincidencia con los nombres generados automaticamente
        ## ya sea nombre de serie o clave

        # si coincide con la clave
        if str(nombre) == str(data_inegi.iloc[0,0]) or str(nombre) == data_banxico.columns[0].split(' ')[0]:
           df.columns = [ col.split(' ')[0].strip() for col in df.columns]
           df = df[[ str(val).strip() for val in data[data.columns[0]]] ]

           rutas_variables_usuario["NombreVariable"] = rutas_variables_usuario["NombreVariable"].apply(lambda x: x.split(' ',1)[0] )

        
        # coincide con nombre de ruta
        else:
           #print('df.columns',df.columns)
           df.columns = [ ' '.join(col.split('>')[-2:]) for col in rutas_variables_usuario['NombreVariable'].values ]
           #df.columns = [(col.split(' ',1)[1].split()) for col in df.columns]
           #print('cols 1\n', df.columns)
           #print('\n\nCols 2', [col.split('>')[-1].strip() for col in data[data.columns[0]]])
           #df = df[ [col.split('>')[-1].strip() for col in data[data.columns[0]]] ]
                   
        
         
      st.write(f"Resumen de los datos")
      st.write(df)
      mensaje_estado = "Se obtuvieron con éxito ✅"
    
    except Exception as e:
      st.write(e)
      mensaje_estado = "Hubo un error, verifique sus datos ❌"
    st.write(mensaje_estado)




# -----------------------------
# -----------------------------                 Estadisticas, minimo, maximo, promedio
# -----------------------------




# -----------------------------
# -----------------------------                 Visualizacion de las graficas
# -----------------------------







    st.subheader("Visualización", divider="orange")
    selected_variable = st.selectbox('Selecciona la variable a graficar:', df.columns)

    
    #st.write(selected_variable)
    rutas_variables_usuario = rutas_variables_usuario.set_index('NombreVariable').T[df.columns].T.reset_index()
    #st.write(rutas_variables_usuario)



    ruta_completa_variable: str = rutas_variables_usuario[rutas_variables_usuario["NombreVariable"] == selected_variable]["RutaCompleta"].iloc[0]
    tmp:list = ruta_completa_variable.split(">")[-4:-1] if len(ruta_completa_variable.split(">")[:-1]) > 3 else ruta_completa_variable.split(">")[:-1]
    ruta_completa_variable = ">".join(tmp)
    nombres_rutas = ruta_completa_variable.split(">")

    df_sin_nans = df[selected_variable].dropna()
    fig = px.line(df_sin_nans, y=selected_variable)

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
        for i, nombre in enumerate(nombres_rutas)
      ]
    )

    st.plotly_chart(fig)

    # Dash
    df_dash = pd.DataFrame(
       {
              
              "Variable": df.columns,                            
              "Historia": [(df[col].dropna()).tolist() for col in df.columns],
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
   
    st.subheader("Descargar variables", divider="green")
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

      df_diario['fecha'] = pd.to_datetime(df_diario['fecha']).dt.date
      df_diario.to_excel(writer, sheet_name='Diarias', index=False)
      # Agregamos imagenes
      for i, img_bytes1 in enumerate(imgs_bytes):    
        df_img1 = pd.DataFrame({'image': [img_bytes1.getvalue()]})
        df_img1.to_excel(writer, sheet_name='Graficas', index=False, header=False, startrow=i*15, startcol=0)
        
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
      file_name='variables_usuario.xlsx',
      key='download_button'
      )
    
# Reiniciamos ambiente
uploaded_file = None