import streamlit as st
import pandas as pd

df = pd.read_excel("misVariablesMacrosEjemplo.xlsx")
text = df.iloc[0]["Variables"].split(">")[0]

x = st.slider("Select a value")
st.write(x, f"{text} squared is", x * x)