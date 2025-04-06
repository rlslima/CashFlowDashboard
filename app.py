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
from views.initial_balances_view import show_initial_balances_view
from config import load_config, save_config, APP_TITLE, APP_ICON
import json

# Configuração da página
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide"
)

# Carregar configurações salvas
try:
    config = load_config()
except json.JSONDecodeError:
    st.warning("Arquivo de configuração corrompido. Resetando para padrão.")
    config = {"sheet_url": "", "gs_selected_sheet": "", "initial_balances": []}
    save_config(config)
except FileNotFoundError:
    st.info("Arquivo de configuração não encontrado. Criando um novo.")
    config = {"sheet_url": "", "gs_selected_sheet": "", "initial_balances": []}
    save_config(config)

# Inicialização das variáveis de sessão
if 'data' not in st.session_state:
    st.session_state.data = None
if 'sheet_url' not in st.session_state:
    st.session_state.sheet_url = config.get('sheet_url', '')
if 'gs_selected_sheet' not in st.session_state:
    st.session_state.gs_selected_sheet = config.get('gs_selected_sheet', '')
if 'initial_balances' not in st.session_state:
    # Carrega saldos iniciais da configuração
    if 'initial_balances' in config and config['initial_balances']:
        try:
            balances_data = config['initial_balances']
            if isinstance(balances_data, list) and all(isinstance(item, dict) for item in balances_data):
                initial_balances_df = pd.DataFrame(balances_data)
                if not initial_balances_df.empty:
                    if 'Date' in initial_balances_df.columns:
                         # Converter a coluna Date para datetime
                         initial_balances_df['Date'] = pd.to_datetime(initial_balances_df['Date'])
                         st.session_state.initial_balances = initial_balances_df
                    else:
                        st.warning("Coluna 'Date' não encontrada nos saldos iniciais. Inicializando vazio.")
                        st.session_state.initial_balances = pd.DataFrame(columns=['Company', 'Balance', 'Date'])
                else:
                    st.session_state.initial_balances = pd.DataFrame(columns=['Company', 'Balance', 'Date'])
            else:
                 st.warning("Formato inválido dos saldos iniciais na configuração. Inicializando vazio.")
                 st.session_state.initial_balances = pd.DataFrame(columns=['Company', 'Balance', 'Date'])
        except (ValueError, KeyError) as e:
            st.error(f"Erro ao processar saldos iniciais da configuração: {e}. Inicializando vazio.")
            st.session_state.initial_balances = pd.DataFrame(columns=['Company', 'Balance', 'Date'])
    else:
        st.session_state.initial_balances = pd.DataFrame(columns=['Company', 'Balance', 'Date']) # Inicializa como DataFrame vazio

# Garantir que initial_balances seja sempre um DataFrame
if not isinstance(st.session_state.initial_balances, pd.DataFrame):
    st.session_state.initial_balances = pd.DataFrame(columns=['Company', 'Balance', 'Date'])

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None
if 'current_data_source' not in st.session_state:
    st.session_state.current_data_source = "google_sheets"  # Definir fonte padrão
if 'current_sheet' not in st.session_state:
    st.session_state.current_sheet = None
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None

# Se temos uma URL e uma aba selecionada, tentar carregar os dados automaticamente
if st.session_state.sheet_url and st.session_state.gs_selected_sheet and st.session_state.data is None:
    try:
        data = fetch_google_sheet_data(st.session_state.sheet_url, st.session_state.gs_selected_sheet)
        st.session_state.data = process_data(data)
        st.success("Dados carregados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao carregar dados automaticamente: {e}")
        st.session_state.data = None # Limpar dados em caso de erro

def load_data():
    """
    Carrega os dados do Google Sheets ou arquivo local, dependendo da configuração.
    """
    try:
        if st.session_state.current_data_source == "google_sheets":
            if not st.session_state.sheet_url:
                st.warning("URL do Google Sheets não configurada. Por favor, configure na aba Configurações.")
                return None
                
            if not st.session_state.gs_selected_sheet:
                st.warning("Planilha não selecionada. Por favor, selecione uma planilha na aba Configurações.")
                return None
                
            # Carregar dados principais
            df = fetch_google_sheet_data(st.session_state.sheet_url, st.session_state.gs_selected_sheet)
            
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
st.title(APP_TITLE)

# Sidebar para navegação
with st.sidebar:
    st.header("Navegação")
    view = st.radio(
        "Selecione a visualização",
        ["Visão por Empresa", "Visão Diária", "Visão Mensal", "Saldos Iniciais", "Configurações"]
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
elif view == "Saldos Iniciais":
    show_initial_balances_view()
else:
    show_settings_view()

# Rodapé
st.markdown("---")
st.caption("Painel Financeiro do Grupo Combrasen © 2023")
