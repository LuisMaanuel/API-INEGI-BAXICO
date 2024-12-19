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





class Indicadores:
    
    def __init__(self, token):
        self.__token = token # token proporcionado por el INEGI único para cada usuario
        self.__liga = 'https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/' 
        self.__liga_base = self.__liga + 'INDICATOR/' #base de los indicadores
        # vriables para la consulta
        self._indicadores = list() # lista con los indicadores a consultar. cada módulo la llena con sus especificaciones
        self._bancos = list() # lista con los bancos de los indicadores
        self._columnas = list() # nombres de las columnas. En los módulos de series se llena automáticamente.
        # diccionario con la clave de frecuencia del INEGI y el factor por el cual se debe multiplicar
        # el último valor para pasarlo a su mes correspondiente
        # Ejemplo: una serie semestral tiene como clave de frecuencia '4', esto indica que para cada año van
        # a haber dos periodos indicando los dos semestres: "2020/01, 2020/02"
        # El factor del diccionario indicaría que al último dígito lo multiplicamos por 6 para pasarlo a meses
        # las claves que no se encuentran en el diccionario son irregulares y no se van a operar
        self.__frecuancias_dict = {'BIE': {'1':(1,'Y'), '2':(1,'Y'), '3':(1,'Y'), '4':(6,'M'), '5':(4,'M'), '6':(3,'Q'), 
                                           '7':(2,'M'), '8':(1,'M'), '9':(14,'SM')},
                                    'BISE': {'1':(1,'Y'), '3':(1,'Y'), '4':(3,'Q'), '7':(1,'Y'), '8':(1,'M'), '9':(1,'Y'), '16':(1,'Y')}}
        self.__clave_entidad = None
        
############## Obtener Data Frame ########################

# Se definen  los métodos internos y públicos necesarios para obtener la serie y pasarla a un DataFrame
# Las dos variables esenciales para esto son self._indicadores y self._bancos. Cada módulo debe contar con métodos
# o atributos que permitan definir estas variables. También todas las variables de consulta deben ser accesibles tanto 
# dentro de las funciones obtener_df() y grafica() como parámetros así como atributos de la clase. 

    # aquí falta un control de errores cuando no se pudo obtener la info y advirtiendo que se cheque bien el token
    def __request(self, liga_api):
        #print('liga de la api', liga_api)
        req = requests.get(liga_api)
        assert req.status_code == 200, 'No se encontró información con las parámetros especificados.'
        data = json.loads(req.text)
        return data

    def __obtener_banco(self, indicador):
        if int(indicador) <= 698680: 
            return 'BIE'
        else: 
            return 'BISE'


    def __obtener_json(self, indicador, banco):
        """ 
    
        Construye la liga de consulta y obtiene la información resultante del API del
        INEGI. 
        
        Parámetros:
        ------------
        
        indicador: str.  Número del indicador a buscar.
       -------------
    
        Regresa un diccionario con la información del indicador proporcionada por el API
        del INEGI en formato JSON. 
    
        Para más información visitar https://www.inegi.org.mx/servicios/api_indicadores.html
    
        """
        if banco is None: 
            if indicador in ['539260', '539261', '539262']: 
                raise Exception("Para los indicadores '539260', '539261' y '539262' es necesario definir el banco ya que existen tanto para el BIE como para el BISE")
            else: banco = self.__obtener_banco(indicador)
        liga_api = '{}{}/es/{}/false/{}/2.0/{}?type=json'.format(self.__liga_base, indicador,  self.__clave_entidad, banco, str(self.__token))
        data = self.__request(liga_api)

        return data['Series'][0], banco
    
    def __json_a_df(self, data, banco):
        """ 
        
        Construye un DataFrame con la información resultante del API del INEGI de 
        un solo indicador a la vez.
    
        Parámetros:
        -----------
        data: Dict. JSON obtendio del API del INEGI.
        banco: str. Banco de información donde se encuentra el indocador. Puede ser 
                    'BIE' o 'BISE'.
        -----------
        
        Regresa un objeto tipo DataFrame con la información del indicador proporcionada por el API
        del INEGI en formato JSON. 
    
        Para más información visitar https://www.inegi.org.mx/servicios/api_indicadores.html
    
        """
        serie = data.pop('OBSERVATIONS') #con esto se separa la serie real de los metadatos

        # construcción de la serie
        obs_totales = len(serie)
        # dic = {'fechas':[serie[i]['TIME_PERIOD'] for i in range(obs_totales)],
        #         'valor':[float(serie[i]['OBS_VALUE']) if serie[i]['OBS_VALUE'] is not None else nan for i in range(obs_totales)]}
        
        dic = {'fechas':[serie[i]['TIME_PERIOD'] for i in range(obs_totales)],
                'valor':[float(serie[i]['OBS_VALUE']) if (serie[i]['OBS_VALUE'] is not None) and (serie[i]['OBS_VALUE'] != "") else nan for i in range(obs_totales)]}
        df = pd.DataFrame.from_dict(dic) 
        frecuencia = data['FREQ']
        # factor, period = self.__frecuancias_dict[banco].get(frecuencia) # factor que multiplica el periodo para pasar a fecha y periodo de pd
        # if factor: 
        #     try: 
        #         cambio_fechas = lambda x: '/'.join(x.split('/')[:-1] + [str(int(x.split('/')[-1])*factor)])
        #         df.fechas = df.fechas.apply(cambio_fechas)
        #         df.set_index(pd.to_datetime(df.fechas),inplace=True, drop=True)
        #         df = df.drop(['fechas'],axis=1)
        #         if period == 'SM': df.index = df.index + pd.offsets.SemiMonthBegin()
        #     except: 
        #         df.fechas = dic['fechas']
        #         df.set_index(df.fechas,inplace=True, drop=True)
        #         df = df.drop(['fechas'],axis=1)
        #         warnings.warn('No se pudo interpretar la fecha correctamente por lo que el índice no es tipo DateTime')
        # else:
        df.set_index(df.fechas,inplace=True, drop=True)
        df = df.drop(['fechas'],axis=1)
            #warnings.warn('No se pudo interpretar la fecha correctamente por lo que el índice no es tipo DateTime')

        # construcción de metadatos
        data['BANCO'] = banco
        meta = pd.DataFrame.from_dict(data, orient='index', columns=['valor'])
            
        return df, meta

    def __definir_cve_ent(self, entidad):
        cve_base = '0700'
        if entidad == '00': 
            self.__clave_entidad = cve_base
            return
        if len(entidad[2:5]) == 0: self.__clave_entidad = '{}00{}'.format(cve_base, entidad[:2])
        else: self.__clave_entidad = '{}00{}0{}'.format(cve_base, entidad[:2], entidad[2:5])

    def _consulta(self, inicio, fin, banco, metadatos):
        
        if isinstance(self._indicadores, str): self._indicadores = [self._indicadores]
        if isinstance(self._bancos, str): self._bancos = [self._bancos]
        if isinstance(self._columnas, str): self._columnas = [self._columnas]
        
        lista_df = list()
        meta_dfs = list()
        for i in range(len(self._indicadores)):
            indicador = self._indicadores[i]
            data, banco = self.__obtener_json(indicador, banco)
            df, meta = self.__json_a_df(data, banco)
            if banco == 'BIE': df = df[::-1]
            lista_df.append(df)
            meta_dfs.append(meta)

        df = pd.concat(lista_df,axis=1)
        meta = pd.concat(meta_dfs, axis=1)
        try: 
            df.columns = self._columnas
            meta.columns = self._columnas
        except: 
            warnings.warn('Los nombres no coinciden con el número de indicadores')
            df.columns = self._indicadores
            meta.columns = self._indicadores

        if metadatos is False: return df[inicio:fin] 
        else: return df[inicio:fin], meta
        
    def obtener_df(self, 
                   indicadores: 'str|list', 
                   nombres: 'str|list' = None, 
                   clave_area: str = '00',
                   inicio: str = None, 
                   fin: str = None, 
                   banco: str = None, 
                   metadatos: bool = False):
        """
        Regresa un DataFrame con la información de los indicadores proporcionada por el API del INEGI. Si metadatos = True regresa un segundo DataFrame con las claves de los metadatos del indicador. 

        Parametros
        -----------
        indicadores: str/list. Clave(s) de los indicadores a consultar.
        nombres: list/str, opcional. Nombre(s) de las columas del DataFrame. De no proporcionarse, se usarán los indicadores.
        clave_area: str. Clave de dos a cinco caracteres que indentifica el área geográfica de acuerdo con el Marco Geoestadístico. Para definir el total nacional se especifica '00'. Este campo solo aplica para los indicadores del Bando de Indicadores (BISE), no aplica para los del Banco de Información Económica (BIE).
                                    Dos dígitos para incluir nivel estatal (ej.01 a 32).
                                    Cinco dígitos dígitos para incluir nivel municipal (ej. 01001).
        inicio: str, opcional. Fecha donde iniciar la serie en formato YYYY(-MM-DD). De no proporcionarse será desde el primer valor disponible. 
        fin: str, opcional. Fecha donde terminar la serie en formato YYYY(-MM-DD). De no proporcionarse será hasta el último valor disponible.
        banco: str, opcional. ['BIE' | 'BISE'] Define el banco al cual pertenecen los indicadores. Puede ser el Banco de Indicadores Económicos (BISE) o el Banco de Información Económica (BIE). Ya que solamente tres claves de indicadores se encuentran en ambos bancos y el resto son diferentes, no es necesario definir este parámetro a menos que los indicadores a consultar sea alguno de los siguientes: ['539260', '539261', '539262'].
        metadatos: bool. En caso se ser verdadero regresa un DataFrame con los metadatos de los indicadores.
        ----------
        
        El DataFrame resultante tiene una columna por cada indicador y un DateTimeIndex con la fecha de los valores. 
        
        Para más información visitar https://www.inegi.org.mx/servicios/api_indicadores.html

        """     
        self._indicadores = indicadores
        self._columnas = indicadores
        if nombres is not None: 
            self._columnas = nombres
        self.__definir_cve_ent(clave_area)
        return self._consulta(inicio, fin, banco, metadatos)



## Catalogo de Metadatos

    def _consultar_catalogo(self, clave, id, banco):
        liga = '{}{}/{}/es/{}/2.0/{}/?type=json'.format(self.__liga, clave, id, banco, self.__token)
        req = requests.get(liga)
        data = json.loads(req.text)
        return pd.DataFrame(data['CODE'])

    def catalogo_indicadores(self, 
                             banco: str, 
                             indicador: str = None):
        '''
        Regresa un DataFrame con la descripción de algunos o todos los indicadores de un banco. 

        Parametros
        -----------
        banco: str. ['BIE' | 'BISE'] Define el banco al cual pertenecen los indicadores. Puede ser el Banco de Indicadores Económicos (BISE) o el Banco de Información Económica (BIE).
        indicador: str, opcional. Clave del indicador a consultar. En caso de no definirse se regresan todos los indicadores del banco.
        ----------
        
        Para más información visitar https://www.inegi.org.mx/servicios/api_indicadores.html

        '''
        if indicador is None: indicador = 'null'
        return self._consultar_catalogo('CL_INDICATOR', indicador, banco)

    def consulta_metadatos(self, 
                           metadatos: 'DataFrame|dict'):
        '''
        Regresa un DataFrame con la descripción de los metadatos de una o más series. 

        Parametros
        -----------
        metadatos: DataFrame con los metadatos a consultar obtenido por la función obtener_df cuando metadatos = True. También acepta un diccionario equivalente.
        ----------
        
        Para más información visitar https://www.inegi.org.mx/servicios/api_indicadores.html

        '''
        if isinstance(metadatos, dict): metadatos = pd.DataFrame.from_dict(dict)
        n_df = metadatos.copy(deep=True)
        for col in metadatos.columns:
            banco = metadatos.loc['BANCO',col]
            for idx in metadatos.index: 
                if idx in ['LASTUPDATE','BANCO']: continue
                id = metadatos.loc[idx,col]
                if id is None or len(id) == 0: continue
                if idx == 'INDICADOR': clave = 'CL_INDICATOR'
                else: clave = 'CL_{}'.format(idx)
                try:
                    desc = self._consultar_catalogo(clave, id, banco)
                    n_df.loc[idx,col] = desc.iloc[0,1]
                except: n_df.loc[idx,col] = 'No hay información'

        return n_df
    

# 1) La primera vez tardara, las siguientes seran muy veloces
#catalogo_path: str = r"./catalogo/catalogoCompletoINEGI.xlsx"
#catalogo: pd.DataFrame = load_excel(catalogo_path)

# 2) La primera vez siempre correra rapido, las siguientes seran muy veloces
catalogo: pd.DataFrame = load_data_objeto('./catalogo/catalogoINEGI.pkl')
rutas_variables_usuario = None

def construir_catalogo(formato: str):
  if formato.strip() == "Rutas":
    columna_formato = "Variables"
  elif formato.strip() == "Claves":
    columna_formato = "Claves"
  tmp = catalogo[["Variables", "Claves"]].set_index(columna_formato).squeeze()
  return tmp 


def obtener_serie(ruta_archivo: str, formato:str, token:str = "f6a7b69c-5c48-bf0c-b191-5ca98c6a6cc0"):
  global rutas_variables_usuario 
  
  archivo = pd.read_excel(ruta_archivo)
  # Tomamos siempre la primera columna
  variables_usuario: pd.Series = archivo.iloc[:,0]

  #st.write(variables_usuario.iloc[0])
  catalogo_se: pd.Series = construir_catalogo(formato)
  #st.write(catalogo_se[variables_usuario.iloc[3]])

  # Se instancia la interfaz que se counicara con INEGI
  inegi = Indicadores(token)  
  variables_df = pd.DataFrame({"Mensaje": ["No entro en ninguno de los condicionales programadas (if) reportar"]})
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

    # ISSUE: Verficar si el usuario no puso rutas repetidas
    # Mayor verificacion, quitar los duplicados de la lista si es que existen
    #claves_variables = list(set(claves_variables))
    #nombres_variables = list(set(nombres_variables))
    
    # Se obtiene la serie a partir de la API
    variables_df = inegi.obtener_df(indicadores=claves_variables.tolist(), nombres=nombres_variables, banco="BIE")
    
    rutas_variables_usuario = pd.DataFrame({"RutaCompleta": variables_usuario_, "NombreVariable": nombres_variables})
  
  elif formato == "Claves":
    claves_variables =  variables_usuario
    # st.write(claves_variables.isin(catalogo_se.index))
    
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
    if len(archivo.columns) > 1:
        ## obtenemos los nombres de las columnas en caso de que existan,
        ## por defecto se estan considerando que los nombres estan en la segunda columna
        nombres_variables = archivo.iloc[:,1].values
        nombres_variables = nombres_variables[claves_filtro]

        
    else:
        nombres_variables = claves_variables.apply(lambda x: catalogo_se[x].split(">")[-1])
        nombres_variables = [str(clave) + nombre for clave, nombre in zip(claves_variables, nombres_variables)]

    rutas_variables_usuario = pd.DataFrame({"RutaCompleta": claves_variables.apply(lambda x: catalogo_se[x]), "NombreVariable": nombres_variables})

    # Convertir todo cadena
    claves_variables = claves_variables.astype(str)
    claves_variables = claves_variables.tolist()
    # Quitamos duplicados
    # claves_variables = list(set(claves_variables))
    # nombres_variables = list(set(nombres_variables))
    
    # for clave_, nombre_ in claves_variables, nombres_variables:
    #    print(clave_, nombre_)
    variables_df = inegi.obtener_df(indicadores=claves_variables, nombres=nombres_variables, banco="BIE")
      #  st.write(variables_df)
    # variables_df = inegi.obtener_df(indicadores=claves_variables, nombres=nombres_variables, banco="BIE")
    
    

  return variables_df



# ----------------------------------- Interfaz ---------------------------------------
  
with st.sidebar:
    st.write("Ejemplos de rutas: ")
    muestra_rutas: pd.DataFrame = load_excel("./pruebas/inegi-muestra-5rutas.xlsx")   
    # Crear un archivo Excel en BytesIO
    excel_file = BytesIO()
    muestra_rutas.to_excel(excel_file, index=False, engine='xlsxwriter')
    excel_file.seek(0)
    # Descargar el archivo Excel
    st.download_button(
        label="inegi-muestra-5rutas.xlsx",
        data=excel_file,
        file_name='inegi-muestra-5rutas.xlsx',
        key='download_button_r'
    )

with st.sidebar:
    st.write("Ejemplos de claves: ")
    muestra_claves: pd.DataFrame = load_excel("./pruebas/inegi-muestra-5claves.xlsx")   
    # Crear un archivo Excel en BytesIO
    excel_file = BytesIO()
    muestra_claves.to_excel(excel_file, index=False, engine='xlsxwriter')
    excel_file.seek(0)
    # Descargar el archivo Excel
    st.download_button(
        label="inegi-muestra-5claves.xlsx",
        data=excel_file,
        file_name='inegi-muestra-5claves.xlsx',
        key='download_button_c'
    )

# Titulo principal y pequeña explicación
st.title("Obtener datos :green[INEGI] 📊")
st.write("Aqui se obtendra las series de Inegi")


# Estructura de los datos a subir
st.subheader("Estructura de los datos a subir", divider="green")

st.write('Para un correcto funcionamiento, es importante que el archivo excel (.xlsx) tenga la siguiente estructura.')

st.markdown('- Primer columa: corresponde a la clave o ruta de la serie a descargar.') 
st.markdown('- Segunda columna (opcional): es el nombre deseado para dicha serie.')

st.write('''En caso de no proporcionar la columna opcional del nombre, se le asignara la clave de la serie seguido del nombre que tiene dicha serie en la plataforma.
         Si se tiene una tercer columna es importante que la segunda corresponda a los nombres deseados.''')


st.write('Ejemplo de la estructura con claves')
st.write(pd.read_excel('./catalogo/INEGI/estructura_claves.xlsx'))

st.write('Ejemplo de la estructura con rutas')
st.write(pd.read_excel('./catalogo/INEGI/estructura_rutas.xlsx'))


# Configuración inicial
st.subheader("Configuración inicial", divider="green")
token = st.text_input('Escribir token', placeholder='Ej. c64be54e-1842-acb9-0843-baad4ab4aa56')
token = 'c64be54e-1842-acb9-0843-baad4ab4aa56' if not token else token
st.write("Token escrito: ", token)

st.markdown("Si no se tiene token generarlo en: https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify")

col1, col2 = st.columns(2)
with col1:
    formato_excel = st.radio(
        "Seleccionar formato",
        ["Rutas", "Claves"],
        captions = ["Ej. Manufactura > extracción > ... ", "802342"])
    st.write("Tu seleccionaste:", formato_excel)
with col2:
    st.write("(Campos opcionales)")
    fecha_inicio = st.date_input("Fecha de inicio", value=None, min_value=datetime(1990, 1, 1), format="DD/MM/YYYY")
    st.write('Tu fecha escrita fue:', fecha_inicio)
    
    fecha_fin = st.date_input("Fecha final", value=datetime.now(), min_value=datetime(1990, 1, 1), format="DD/MM/YYYY")
    st.write('Tu fecha escrita fue:', fecha_fin)

st.markdown('_Si no se especifica ninguna fecha por defecto se obtiene todo el historial._')
# Seleecion de archivos
st.subheader("Cargar archivos", divider="green")
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
      
      ## Para las series anuales, aqui es donde se modifica la fecha para tener el anio 
      ## y el primer mes del anio como fecha, por ejemplo, pasar de 2003 a 2003/01
      ## y de 2004 a 2004/01

      df.reset_index(inplace=True)

      df['fechas'] = df['fechas'].apply(lambda x : x + '/01' if len(x)== 4 else x)

      df = df.groupby('fechas', as_index=False).agg('first').sort_values(by='fechas', ascending = True)

      ## en la siguiente linea de codigo usamos dt.strftime('%Y-%m')
      ## para tener fechas del tipo 2010-02, 2010-03, etc.
      ## si queremos fechas con dia basta con usar dt.date
      df.fechas = pd.to_datetime(df.fechas, format='%Y/%m').dt.strftime('%Y-%m')
      df.set_index('fechas', inplace=True)

      # Aqui es donde haremos el corte
      if fecha_inicio is not None:
        # Convertir la serie de índices a tipo fecha


        # Convertir el objeto de tipo date a datetime
        fecha_inicio = datetime.combine(fecha_inicio, datetime.min.time())
        fecha_fin = datetime.combine(fecha_fin, datetime.min.time())

        # Filtrar el DataFrame para obtener solo las filas dentro del intervalo de fechas
        df = df.loc[(pd.to_datetime(df.index) >= fecha_inicio) & (pd.to_datetime(df.index) <= fecha_fin)]
      st.write(f"Resumen de los datos")
      st.write(df)
      mensaje_estado = "Se obtuvieron con éxito ✅"
   except Exception as e:
      st.write(e)
      mensaje_estado = "Hubo un error, verifique sus datos ❌"
   st.write(mensaje_estado)
   
   st.subheader("Visualización", divider="green")

   #st.write(rutas_variables_usuario)
   # Selección de la variable
   selected_variable = st.selectbox('Selecciona la variable a graficar:', df.columns)
   
   ruta_completa_variable: str = rutas_variables_usuario[rutas_variables_usuario["NombreVariable"] == selected_variable]["RutaCompleta"].iloc[0]
   
   tmp:list = ruta_completa_variable.split(">")[-4:-1] if len(ruta_completa_variable.split(">")[:-1]) > 3 else ruta_completa_variable.split(">")[:-1]

   ruta_completa_variable = ">".join(tmp)
   
   #st.write(ruta_completa_variable)
   # Crear y mostrar la gráfica de líneas
   df_sin_nans = df[selected_variable].dropna()
   #st.line_chart(data=df_sin_nans, y=selected_variable, height=450)
   fig = px.line(df_sin_nans, y=selected_variable) #title=" ".join(selected_variable.split(" ")[1:]))
   # Configurar el diseño (layout)
   nombres_rutas = ruta_completa_variable.split(">")
   
#    fig.update_layout(
#     title="hola\n memo",  # Título principal
#     xaxis_title='Eje X',  # Título del eje X
#     yaxis_title='Eje Y',  # Título del eje Y
#     title_font=dict(size=14),  # Tamaño de fuente del título principal
#     title_x=0.06,  # Posición del título principal en el eje X (0.5 = centrado)
#     title_y=0.95,  # Posición del título principal en el eje Y  
# )
   
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
        for i, nombre in enumerate(nombres_rutas)
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

  #     pio.write_excel(fig, excel_file, sheet_name='graficas')
   
   #df.to_excel(excel_file, index=True, engine='xlsxwriter')
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
   



