import streamlit as st

# Configuração mínima
st.set_page_config(
    page_title="Teste Mínimo",
    page_icon=":rocket:",
    layout="wide"
)

# Conteúdo simples
st.title("Teste de Dashboard Mínimo")
st.write("Este é um teste simples para verificar se o Streamlit está funcionando.")

# Elementos básicos
st.header("Elementos Básicos")
st.button("Clique Aqui")
st.slider("Selecione um valor", 0, 100, 50)

# Mensagem de sucesso
st.success("Aplicação de teste carregada com sucesso!")