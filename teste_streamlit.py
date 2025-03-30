import streamlit as st
import pandas as pd
import numpy as np

st.title('Teste de Funcionamento do Streamlit')
st.write('Este é um teste simples para verificar se o Streamlit está funcionando.')

# Cria um DataFrame de exemplo
data = pd.DataFrame({
    'Categoria': ['A', 'B', 'C', 'D'],
    'Valores': [10, 20, 30, 40]
})

st.write(data)

# Cria um gráfico simples
st.bar_chart(data.set_index('Categoria'))

st.success('Tudo funcionando corretamente!')
