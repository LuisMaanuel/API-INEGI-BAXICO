import pandas as pd
import streamlit as st
from st_pages import  get_nav_from_toml



@st.cache_data
def load_data(url):
    df = pd.read_excel(url)
    return df

# Specify what pages should be shown in the sidebar, and what their titles and icons
# should be

#show_pages(
#    [
#        Page("app.py", "Introducción", "🏠"),
#        Page("vista/02_obtener_series_inegi.py", "Obtener datos INEGI", "📗"),
#        Page("vista/03_obtener_series_banxico.py", "Obtener datos BANXICO", "📘"),
#        Page("vista/04_buscar.py", "Buscar rutas", "🔎")
#    ]
#)

nav = get_nav_from_toml(
    "pages_sections.toml" #if sections else ".streamlit/pages.toml"
)

pg = st.navigation(nav)
pg.run()


muestra_rutas: pd.DataFrame = load_data("./pruebas/inegi-muestra-5rutas.xlsx")
muestra_claves: pd.DataFrame = load_data("./pruebas/inegi-muestra-5claves.xlsx")

# Opciones para leer el catalogo
# 1) Leyendo el excel por primera vez y despues serializarlo
#catalogo_inegi: pd.DataFrame = load_data(r"./catalogo/catalogoCompletoINEGI.xlsx")


# 2) Abrir el archivo en modo lectura binaria y guardarlo en cache por si lo vuelve abrir el enlace

