import streamlit as st
import pandas as pd
from datetime import datetime, date as date_class
import os
import pytz
from utils.google_sheets import fetch_google_sheet_data, fetch_initial_balances
from utils.data_processor import process_data, format_currency_brl
from views.monthly_view import show_monthly_view
from views.period_view import show_period_view
from views.yearly_view import show_yearly_view
from views.company_view import show_company_view
from views.daily_view import show_daily_view
from views.settings_view import show_settings_view

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Fluxo de Caixa",
    page_icon="💰",
    layout="wide"
)

# Inicialização das variáveis de sessão
if 'data' not in st.session_state:
    st.session_state.data = None
if 'initial_balances' not in st.session_state:
    st.session_state.initial_balances = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None
if 'sheet_url' not in st.session_state:
    st.session_state.sheet_url = None
if 'current_data_source' not in st.session_state:
    st.session_state.current_data_source = None
if 'current_sheet' not in st.session_state:
    st.session_state.current_sheet = None
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None

def load_data():
    """
    Carrega os dados do Google Sheets ou arquivo local, dependendo da configuração.
    """
    if "data_source" not in st.session_state:
        st.session_state.data_source = "google_sheets"
        
    if "sheet_url" not in st.session_state:
        st.session_state.sheet_url = None
        
    if "selected_sheet" not in st.session_state:
        st.session_state.selected_sheet = None
        
    if "data" not in st.session_state:
        st.session_state.data = None
        
    if "initial_balances" not in st.session_state:
        st.session_state.initial_balances = None
        
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = None
        
    try:
        if st.session_state.data_source == "google_sheets":
            if not st.session_state.sheet_url:
                st.warning("URL do Google Sheets não configurada. Por favor, configure na aba Configurações.")
                return None
                
            if not st.session_state.selected_sheet:
                st.warning("Planilha não selecionada. Por favor, selecione uma planilha na aba Configurações.")
                return None
                
            # Carregar dados principais
            df = fetch_google_sheet_data(st.session_state.sheet_url, st.session_state.selected_sheet)
            
            # Carregar saldos iniciais
            try:
                initial_balances = fetch_initial_balances(st.session_state.sheet_url)
                st.session_state.initial_balances = initial_balances
            except Exception as e:
                st.warning(f"Não foi possível carregar os saldos iniciais: {str(e)}")
                st.session_state.initial_balances = None
                
        else:  # Local file
            if "uploaded_file" not in st.session_state or st.session_state.uploaded_file is None:
                st.warning("Arquivo local não carregado. Por favor, faça o upload do arquivo na aba Configurações.")
                return None
                
            df = pd.read_excel(st.session_state.uploaded_file)
            st.session_state.initial_balances = None  # Reset initial balances for local file
            
        if df is not None and not df.empty:
            df = process_data(df)
            st.session_state.data = df
            st.session_state.last_refresh = datetime.now()
            return df
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None
        
    return None

# Título principal
st.title("Dashboard de Fluxo de Caixa")

# Sidebar para navegação
with st.sidebar:
    st.header("Navegação")
    view = st.radio(
        "Selecione a visualização",
        ["Visão por Empresa", "Visão Diária", "Visão Mensal", "Configurações"]
    )
    
    # Mostrar última atualização se houver dados
    if st.session_state.last_refresh:
        st.info(f"Última atualização: {st.session_state.last_refresh.strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Botão para forçar atualização dos dados
    if st.button("Atualizar Dados"):
        st.session_state.data = None
        st.session_state.last_refresh = None
        if load_data():
            st.success("Dados atualizados com sucesso!")
        else:
            st.error("Erro ao atualizar os dados.")

# Carregar dados se necessário
if st.session_state.data is None:
    if not load_data():
        st.warning("Por favor, configure a fonte de dados nas Configurações antes de visualizar.")

# Mostrar a visualização selecionada
if view == "Visão por Empresa":
    if st.session_state.data is not None:
        show_company_view(st.session_state.data)
    else:
        st.warning("Por favor, carregue os dados nas Configurações antes de visualizar.")
elif view == "Visão Diária":
    if st.session_state.data is not None:
        show_daily_view(st.session_state.data, st.session_state.initial_balances)
    else:
        st.warning("Por favor, carregue os dados nas Configurações antes de visualizar.")
elif view == "Visão Mensal":
    if st.session_state.data is not None:
        show_monthly_view(st.session_state.data)
    else:
        st.warning("Por favor, carregue os dados nas Configurações antes de visualizar.")
else:
    show_settings_view()

# Rodapé
st.markdown("---")
st.caption("Painel Financeiro do Grupo Combrasen © 2023")
