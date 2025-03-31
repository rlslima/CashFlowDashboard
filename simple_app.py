import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Combrasen Group - Simplificado",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Dashboard Simplificado do Grupo Combrasen")
st.markdown("### Versão de Contingência")

# Verificar se o arquivo de exemplo existe
try:
    # Tentar carregar o arquivo de exemplo
    df = pd.read_excel("example_financial_data.xlsx", engine='openpyxl')
    
    st.success("Arquivo de dados de exemplo carregado com sucesso!")
    
    # Mostrar resumo dos dados
    st.write(f"Total de registros: {len(df)}")
    
    # Mostrar amostra dos dados
    st.subheader("Amostra dos Dados")
    st.dataframe(df.head(10))
    
    # Calcular alguns valores básicos
    total_receitas = df[df['Type'] == 'Income']['Value'].sum()
    total_despesas = df[df['Type'] == 'Expense']['Value'].sum()
    saldo = total_receitas - total_despesas
    
    # Mostrar resumo financeiro
    st.subheader("Resumo Financeiro")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Receitas", f"R$ {total_receitas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
    with col2:
        st.metric("Total de Despesas", f"R$ {total_despesas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
    with col3:
        st.metric("Saldo", f"R$ {saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), 
                 delta="positivo" if saldo > 0 else "negativo")
    
    # Criar um gráfico simples
    st.subheader("Receitas vs Despesas por Empresa")
    
    # Agrupar por empresa e tipo, e somar os valores
    company_summary = df.pivot_table(
        index='Company', 
        columns='Type', 
        values='Value', 
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # Mostrar o gráfico
    st.bar_chart(company_summary.set_index('Company'))
    
    st.info("Este é um painel simplificado. A versão completa incluirá todas as visualizações que estavam disponíveis anteriormente.")
    
except Exception as e:
    st.error(f"Erro ao carregar os dados: {str(e)}")
    st.info("Verifique se o arquivo 'example_financial_data.xlsx' existe no diretório raiz.")