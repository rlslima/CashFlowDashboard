import streamlit as st
import pandas as pd
from datetime import datetime
import os
import pytz
from utils.google_sheets import fetch_google_sheet_data
from utils.data_processor import process_data, format_currency_brl
from views.monthly_view import show_monthly_view
from views.period_view import show_period_view
from views.yearly_view import show_yearly_view
from views.company_view import show_company_view
from views.daily_view import show_daily_view
from views.settings_view import show_settings_view

# Configuração da página
st.set_page_config(
    page_title="Painel Financeiro Grupo Combrasen",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definir estado da sessão para dados
if 'data' not in st.session_state:
    st.session_state.data = None
    st.session_state.last_refresh = None
if 'sheet_url' not in st.session_state:
    st.session_state.sheet_url = "https://docs.google.com/spreadsheets/d/1XRy39MblVtmWLpggz1cC_qIRdqE40vIx/edit?usp=sharing&ouid=110344857582375962786&rtpof=true&sd=true"

# Título e cabeçalho do aplicativo
st.title("Painel Financeiro do Grupo Combrasen")
st.markdown("---")

# Função para carregar e processar dados
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_data():
    try:
        # Buscar dados do Google Sheets
        raw_data = fetch_google_sheet_data(
            st.session_state.sheet_url,
            sheet_name=st.session_state.get('selected_sheet')
        )
        
        if raw_data is not None and not raw_data.empty:
            # Processar os dados
            processed_data = process_data(raw_data)
            
            if not processed_data.empty:
                st.sidebar.expander("Dados Processados (Debug)", expanded=False).write(f"""
                Processados: {processed_data.shape[0]} linhas
                Soma de valores: {format_currency_brl(processed_data['Value'].sum())}
                Data mínima: {processed_data['Date'].min().strftime('%d/%m/%Y')}
                Data máxima: {processed_data['Date'].max().strftime('%d/%m/%Y')}
                """)
            
            return processed_data
        else:
            st.error("Falha ao carregar dados do Google Sheets ou a planilha está vazia.")
            return None
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

# Barra lateral - Navegação
with st.sidebar:
    st.title("Menu de Navegação")
    
    # Navegação
    view = st.radio(
        "Selecionar Visualização",
        options=["Fluxo de Caixa Diário", "Fluxo de Caixa Mensal", "Análise por Período", "Resumo Anual", "Comparação de Empresas", "Configurações"],
        label_visibility="collapsed"
    )
    
    # Mostrar última hora de atualização
    if st.session_state.last_refresh:
        # Converter para o fuso horário do Brasil
        br_timezone = pytz.timezone('America/Sao_Paulo')
        last_refresh_br = st.session_state.last_refresh.astimezone(br_timezone)
        st.info(f"Última atualização: {last_refresh_br.strftime('%d/%m/%Y %H:%M:%S')} (Brasil)")

# Carregar dados se ainda não estiverem carregados
if st.session_state.data is None:
    with st.spinner("Carregando dados pela primeira vez..."):
        st.session_state.data = load_data()
        st.session_state.last_refresh = datetime.now(pytz.timezone('America/Sao_Paulo'))

# Mostrar dados ou mensagem de erro
if st.session_state.data is not None:
    df = st.session_state.data
    
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
    if view == "Fluxo de Caixa Diário":
        show_daily_view(filtered_df)
    elif view == "Fluxo de Caixa Mensal":
        show_monthly_view(filtered_df)
    elif view == "Análise por Período":
        show_period_view(filtered_df)
    elif view == "Resumo Anual":
        show_yearly_view(filtered_df)
    elif view == "Comparação de Empresas":
        show_company_view(filtered_df)
    elif view == "Configurações":
        show_settings_view()
    
else:
    st.error("Não há dados disponíveis. Por favor, verifique a conexão com o Google Sheets ou tente atualizar.")
    
    st.info("""
        Formato de dados esperado:
        - Company: ex. "Empresa A"
        - Type: "Expense" ou "Income"
        - Work: ex. "WRK01"
        - Supplier/Client: ex. "Fornecedor 1"
        - Value: ex. "35600.00"
        - Date: ex. "24/03/2025"
    """)
    
    # Oferecer um arquivo de exemplo para download
    if os.path.exists("example_financial_data.xlsx"):
        with open("example_financial_data.xlsx", "rb") as f:
            st.download_button(
                label="Baixar arquivo de exemplo",
                data=f,
                file_name="example_financial_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        st.info("""
            1. Baixe o arquivo de exemplo acima
            2. Use-o como modelo para preparar seus dados
            3. Faça upload do arquivo usando o botão na barra lateral
        """)

# Rodapé
st.markdown("---")
st.caption("Painel Financeiro do Grupo Combrasen © 2023")
