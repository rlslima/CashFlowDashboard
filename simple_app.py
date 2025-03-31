import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Função para formatar moeda no padrão brasileiro
def format_currency_brl(value):
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# Função para processar dados
def process_data(df):
    processed_df = df.copy()
    
    # Garantir que a coluna 'Date' esteja no formato datetime
    if 'Date' in processed_df.columns:
        processed_df['Date'] = pd.to_datetime(processed_df['Date'], format='%d/%m/%Y', errors='coerce')
    
    # Garantir que Value seja numérico
    if 'Value' in processed_df.columns:
        processed_df['Value'] = pd.to_numeric(processed_df['Value'], errors='coerce')
    
    # Adicionar colunas úteis
    if 'Date' in processed_df.columns:
        processed_df['Month'] = processed_df['Date'].dt.month
        processed_df['Year'] = processed_df['Date'].dt.year
        processed_df['MonthYear'] = processed_df['Date'].dt.strftime('%m/%Y')
    
    return processed_df

# Configuração da página
st.set_page_config(
    page_title="Painel Financeiro Grupo Combrasen",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Painel Financeiro do Grupo Combrasen")
st.markdown("---")

# Barra lateral
with st.sidebar:
    st.title("Controles do Painel")
    
    # Botão para carregar dados do arquivo de exemplo
    if st.button("Carregar Dados de Exemplo", use_container_width=True):
        st.session_state.last_refresh = datetime.now()
        st.success("Dados carregados com sucesso!")
    
    # Mostrar última hora de atualização
    if 'last_refresh' in st.session_state:
        st.info(f"Última atualização: {st.session_state.last_refresh.strftime('%d/%m/%Y %H:%M:%S')}")
    
    st.markdown("---")
    
    # Navegação
    st.subheader("Visualizações")
    view = st.radio(
        "Selecionar Visualização",
        options=["Fluxo de Caixa Mensal", "Resumo Anual", "Comparação de Empresas", "Fluxo de Caixa Diário"],
        label_visibility="collapsed"
    )

# Verificar se o arquivo de exemplo existe
try:
    # Tentar carregar o arquivo de exemplo
    raw_df = pd.read_excel("example_financial_data.xlsx", engine='openpyxl')
    
    # Processar dados
    df = process_data(raw_df)
    
    # Filtros Globais
    with st.expander("Filtros Globais", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        # Filtro de empresa
        with col1:
            all_companies = ["Todas"] + sorted(df["Company"].unique().tolist())
            selected_company = st.selectbox("Empresa", all_companies)
        
        # Filtro de tipo (Despesa/Receita)
        with col2:
            all_types = ["Todos"] + sorted(df["Type"].unique().tolist())
            selected_type = st.selectbox("Tipo", all_types)
            
        # Filtro de código de trabalho
        with col3:
            all_works = ["Todos"] + sorted(df["Work"].unique().tolist())
            selected_work = st.selectbox("Obra", all_works)
    
    # Aplicar filtros globais
    filtered_df = df.copy()
    
    if selected_company != "Todas":
        filtered_df = filtered_df[filtered_df["Company"] == selected_company]
    
    if selected_type != "Todos":
        filtered_df = filtered_df[filtered_df["Type"] == selected_type]
    
    if selected_work != "Todos":
        filtered_df = filtered_df[filtered_df["Work"] == selected_work]
    
    # Exibir visualização selecionada
    if view == "Fluxo de Caixa Mensal":
        st.subheader("Fluxo de Caixa Mensal")
        
        # Agrupar por mês e tipo
        monthly_flow = filtered_df.groupby(['MonthYear', 'Type'])['Value'].sum().reset_index()
        monthly_flow_pivot = monthly_flow.pivot(index='MonthYear', columns='Type', values='Value').fillna(0)
        
        if 'Income' not in monthly_flow_pivot.columns:
            monthly_flow_pivot['Income'] = 0
        if 'Expense' not in monthly_flow_pivot.columns:
            monthly_flow_pivot['Expense'] = 0
            
        monthly_flow_pivot['Net'] = monthly_flow_pivot['Income'] - monthly_flow_pivot['Expense']
        
        # Gráfico de barras mensais com Plotly
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly_flow_pivot.index,
            y=monthly_flow_pivot['Income'],
            name='Receitas',
            marker_color='green'
        ))
        fig.add_trace(go.Bar(
            x=monthly_flow_pivot.index,
            y=monthly_flow_pivot['Expense'],
            name='Despesas',
            marker_color='red'
        ))
        fig.add_trace(go.Scatter(
            x=monthly_flow_pivot.index,
            y=monthly_flow_pivot['Net'],
            mode='lines+markers',
            name='Saldo',
            line=dict(color='blue', width=3)
        ))
        
        fig.update_layout(
            title='Fluxo de Caixa Mensal',
            xaxis_title='Mês/Ano',
            yaxis_title='Valor (R$)',
            barmode='group',
            template='plotly_white',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela resumida por mês
        st.subheader("Resumo Mensal")
        monthly_summary = pd.DataFrame({
            'Mês/Ano': monthly_flow_pivot.index,
            'Receitas': monthly_flow_pivot['Income'].apply(format_currency_brl),
            'Despesas': monthly_flow_pivot['Expense'].apply(format_currency_brl),
            'Saldo': monthly_flow_pivot['Net'].apply(format_currency_brl)
        })
        st.dataframe(monthly_summary, use_container_width=True, hide_index=True)
        
    elif view == "Resumo Anual":
        st.subheader("Resumo Anual de Fluxo de Caixa")
        
        # Agrupar por ano e tipo
        yearly_flow = filtered_df.groupby(['Year', 'Type'])['Value'].sum().reset_index()
        yearly_flow_pivot = yearly_flow.pivot(index='Year', columns='Type', values='Value').fillna(0)
        
        if 'Income' not in yearly_flow_pivot.columns:
            yearly_flow_pivot['Income'] = 0
        if 'Expense' not in yearly_flow_pivot.columns:
            yearly_flow_pivot['Expense'] = 0
            
        yearly_flow_pivot['Net'] = yearly_flow_pivot['Income'] - yearly_flow_pivot['Expense']
        
        # Gráfico de barras anuais com Plotly
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=yearly_flow_pivot.index,
            y=yearly_flow_pivot['Income'],
            name='Receitas',
            marker_color='green'
        ))
        fig.add_trace(go.Bar(
            x=yearly_flow_pivot.index,
            y=yearly_flow_pivot['Expense'],
            name='Despesas',
            marker_color='red'
        ))
        fig.add_trace(go.Bar(
            x=yearly_flow_pivot.index,
            y=yearly_flow_pivot['Net'],
            name='Saldo',
            marker_color='blue'
        ))
        
        fig.update_layout(
            title='Fluxo de Caixa Anual',
            xaxis_title='Ano',
            yaxis_title='Valor (R$)',
            barmode='group',
            template='plotly_white',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela resumida por ano
        st.subheader("Resumo Anual")
        yearly_summary = pd.DataFrame({
            'Ano': yearly_flow_pivot.index,
            'Receitas': yearly_flow_pivot['Income'].apply(format_currency_brl),
            'Despesas': yearly_flow_pivot['Expense'].apply(format_currency_brl),
            'Saldo': yearly_flow_pivot['Net'].apply(format_currency_brl)
        })
        st.dataframe(yearly_summary, use_container_width=True, hide_index=True)
        
    elif view == "Comparação de Empresas":
        st.subheader("Comparação entre Empresas")
        
        # Agrupar por empresa e tipo
        company_flow = filtered_df.groupby(['Company', 'Type'])['Value'].sum().reset_index()
        company_flow_pivot = company_flow.pivot(index='Company', columns='Type', values='Value').fillna(0)
        
        if 'Income' not in company_flow_pivot.columns:
            company_flow_pivot['Income'] = 0
        if 'Expense' not in company_flow_pivot.columns:
            company_flow_pivot['Expense'] = 0
            
        company_flow_pivot['Net'] = company_flow_pivot['Income'] - company_flow_pivot['Expense']
        
        # Gráfico de barras por empresa com Plotly
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=company_flow_pivot.index,
            y=company_flow_pivot['Income'],
            name='Receitas',
            marker_color='green'
        ))
        fig.add_trace(go.Bar(
            x=company_flow_pivot.index,
            y=company_flow_pivot['Expense'],
            name='Despesas',
            marker_color='red'
        ))
        fig.add_trace(go.Bar(
            x=company_flow_pivot.index,
            y=company_flow_pivot['Net'],
            name='Saldo',
            marker_color='blue'
        ))
        
        fig.update_layout(
            title='Fluxo de Caixa por Empresa',
            xaxis_title='Empresa',
            yaxis_title='Valor (R$)',
            barmode='group',
            template='plotly_white',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela resumida por empresa
        st.subheader("Resumo por Empresa")
        company_summary = pd.DataFrame({
            'Empresa': company_flow_pivot.index,
            'Receitas': company_flow_pivot['Income'].apply(format_currency_brl),
            'Despesas': company_flow_pivot['Expense'].apply(format_currency_brl),
            'Saldo': company_flow_pivot['Net'].apply(format_currency_brl)
        })
        st.dataframe(company_summary, use_container_width=True, hide_index=True)
        
    elif view == "Fluxo de Caixa Diário":
        st.subheader("Fluxo de Caixa Diário por Obra")
        
        # Agrupar por data, obra e tipo
        daily_flow = filtered_df.groupby(['Date', 'Work', 'Type'])['Value'].sum().reset_index()
        
        # Criar tabela dinâmica: Obras nas linhas, Datas nas colunas
        income_data = daily_flow[daily_flow['Type'] == 'Income'].pivot(index='Work', columns='Date', values='Value').fillna(0)
        expense_data = daily_flow[daily_flow['Type'] == 'Expense'].pivot(index='Work', columns='Date', values='Value').fillna(0)
        
        # Formatar datas nas colunas
        if not income_data.empty:
            income_data.columns = income_data.columns.strftime('%d/%m/%Y')
        if not expense_data.empty:
            expense_data.columns = expense_data.columns.strftime('%d/%m/%Y')
        
        # Mostrar tabelas de receitas e despesas
        st.subheader("Receitas por Obra e Data")
        if not income_data.empty:
            # Aplicar formatação de moeda em toda a tabela
            formatted_income = income_data.applymap(format_currency_brl)
            st.dataframe(formatted_income, use_container_width=True)
        else:
            st.info("Não há dados de receitas para exibir com os filtros selecionados.")
        
        st.subheader("Despesas por Obra e Data")
        if not expense_data.empty:
            # Aplicar formatação de moeda em toda a tabela
            formatted_expense = expense_data.applymap(format_currency_brl)
            st.dataframe(formatted_expense, use_container_width=True)
        else:
            st.info("Não há dados de despesas para exibir com os filtros selecionados.")
    
except Exception as e:
    st.error(f"Erro ao carregar os dados: {str(e)}")
    st.info("Verifique se o arquivo 'example_financial_data.xlsx' existe no diretório raiz.")

# Rodapé
st.markdown("---")
st.caption("Painel Financeiro do Grupo Combrasen © 2023")