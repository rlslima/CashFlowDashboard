import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import io
from utils.google_sheets import fetch_google_sheet_data
import requests
import re

def show_settings_view():
    """
    Mostra a página de configurações do sistema
    """
    st.header("Configurações do Sistema")
    
    # Configurações do Google Sheets
    st.subheader("Configurações do Google Sheets")
    
    # URL do Google Sheet
    if 'sheet_url' not in st.session_state:
        st.session_state.sheet_url = None
    
    new_url = st.text_input(
        "URL do Google Sheet",
        value=st.session_state.sheet_url if st.session_state.sheet_url else "",
        help="Cole aqui a URL da planilha do Google Sheets. A URL deve ser do tipo: https://docs.google.com/spreadsheets/d/SEU_ID_AQUI/edit"
    )
    
    # Inicializar a aba selecionada do Google Sheets na sessão se ainda não existir
    if 'gs_selected_sheet' not in st.session_state:
        st.session_state.gs_selected_sheet = None
    
    # Se a URL mudou, resetar a aba selecionada e limpar os dados antigos
    if new_url != st.session_state.sheet_url:
        st.session_state.sheet_url = new_url
        st.session_state.gs_selected_sheet = None
        st.session_state.data = None
        st.session_state.last_refresh = None
        st.session_state.current_data_source = None
        st.session_state.current_sheet = None
    
    try:
        # Obter todas as abas disponíveis
        excel_file = pd.ExcelFile(io.BytesIO(requests.get(f"https://docs.google.com/spreadsheets/d/{re.search(r'/d/([a-zA-Z0-9-_]+)', new_url).group(1)}/export?format=xlsx").content))
        available_sheets = excel_file.sheet_names
        
        # Se não houver aba selecionada, usar a primeira
        if st.session_state.gs_selected_sheet is None:
            st.session_state.gs_selected_sheet = available_sheets[0]
        
        # Mostrar seleção de aba
        selected_sheet = st.selectbox(
            "Selecione a aba com os dados financeiros",
            options=available_sheets,
            index=available_sheets.index(st.session_state.gs_selected_sheet),
            key="gs_sheet_selector",
            help="Escolha a aba que contém os dados financeiros"
        )
        
        # Atualizar a aba selecionada na sessão
        if selected_sheet != st.session_state.gs_selected_sheet:
            st.session_state.gs_selected_sheet = selected_sheet
            st.session_state.data = None  # Limpar dados antigos ao mudar de aba
            st.session_state.last_refresh = None
            st.session_state.current_data_source = None
            st.session_state.current_sheet = None
            st.success(f"Aba '{selected_sheet}' selecionada!")
        
        # Mostrar prévia dos dados da aba selecionada
        with st.expander("Prévia dos dados da aba selecionada"):
            preview_df = pd.read_excel(io.BytesIO(requests.get(f"https://docs.google.com/spreadsheets/d/{re.search(r'/d/([a-zA-Z0-9-_]+)', new_url).group(1)}/export?format=xlsx").content), sheet_name=selected_sheet, nrows=5)
            st.dataframe(preview_df)
        
        # Carregar e processar os dados usando a função fetch_google_sheet_data
        processed_preview = fetch_google_sheet_data(new_url, sheet_name=selected_sheet)
        
        if processed_preview is not None and not processed_preview.empty:
            # Mostrar informações de debug
            with st.expander("Informações de Debug", expanded=False):
                st.write("**Colunas disponíveis:**")
                st.write(processed_preview.columns.tolist())
                st.write("**Tipos de dados:**")
                st.write(processed_preview.dtypes)
                st.write("**Primeiras linhas dos dados brutos:**")
                st.dataframe(processed_preview.head())
            
            # Mostrar prévia dos dados processados
            with st.expander("Prévia dos dados processados"):
                try:
                    st.write("**Informações gerais:**")
                    st.write(f"- Total de registros: {len(processed_preview)}")
                    
                    # Verificar se as colunas necessárias existem
                    if 'Date' in processed_preview.columns:
                        st.write(f"- Período: {processed_preview['Date'].min().strftime('%d/%m/%Y')} a {processed_preview['Date'].max().strftime('%d/%m/%Y')}")
                    else:
                        st.error("Coluna 'Date' não encontrada nos dados processados")
                    
                    if 'Type' in processed_preview.columns and 'Value' in processed_preview.columns:
                        receitas = processed_preview[processed_preview['Type'] == 'Entrada']['Value'].sum()
                        despesas = processed_preview[processed_preview['Type'] == 'Saída']['Value'].sum()
                        st.write(f"- Total de receitas: R$ {receitas:,.2f}")
                        st.write(f"- Total de despesas: R$ {despesas:,.2f}")
                        st.write(f"- Saldo: R$ {(receitas + despesas):,.2f}")  # Despesas já são negativas
                    else:
                        st.error("Colunas 'Type' ou 'Value' não encontradas nos dados processados")
                    
                    st.write("**Amostra dos dados processados:**")
                    st.dataframe(processed_preview.head())
                except Exception as e:
                    st.error(f"Erro ao mostrar informações dos dados: {str(e)}")
                    st.write("**Amostra dos dados processados:**")
                    st.dataframe(processed_preview.head())
            
            # Botão para carregar os dados
            if st.button("Carregar dados do Google Sheets"):
                with st.spinner("Carregando dados..."):
                    # Atualizar os dados na sessão
                    st.session_state.data = processed_preview
                    st.session_state.last_refresh = datetime.now(pytz.timezone('America/Sao_Paulo'))
                    st.session_state.current_data_source = "google_sheets"
                    st.session_state.current_sheet = selected_sheet
                    
                st.success("Dados carregados com sucesso!")
        else:
            st.error("Não foi possível processar os dados. Verifique se a aba selecionada contém os dados financeiros corretos.")
    except Exception as e:
        st.error(f"Erro ao carregar as abas: {str(e)}")
    
    # Separador
    st.markdown("---")
    
    # Upload de arquivo local
    st.subheader("Upload de Arquivo Local")
    
    uploaded_file = st.file_uploader(
        "Upload planilha Excel",
        type=['xlsx', 'xls'],
        help="Faça upload de um arquivo Excel local para substituir os dados do Google Sheets"
    )
    
    # Se um arquivo foi carregado, mostrar seleção de aba
    if uploaded_file is not None:
        try:
            # Limpar dados antigos ao carregar novo arquivo
            st.session_state.data = None
            st.session_state.last_refresh = None
            st.session_state.current_data_source = None
            st.session_state.current_sheet = None
            st.session_state.uploaded_file = uploaded_file
            
            # Ler todas as abas disponíveis
            excel_file = pd.ExcelFile(uploaded_file)
            available_sheets = excel_file.sheet_names
            
            # Inicializar a aba selecionada na sessão se ainda não existir
            if 'local_selected_sheet' not in st.session_state:
                st.session_state.local_selected_sheet = available_sheets[0]
            
            # Selecionar a aba
            selected_sheet = st.selectbox(
                "Selecione a aba com os dados financeiros",
                options=available_sheets,
                index=available_sheets.index(st.session_state.local_selected_sheet),
                key="local_sheet_selector",
                help="Escolha a aba que contém os dados financeiros"
            )
            
            # Atualizar a aba selecionada na sessão
            if selected_sheet != st.session_state.local_selected_sheet:
                st.session_state.local_selected_sheet = selected_sheet
                st.session_state.data = None  # Limpar dados antigos ao mudar de aba
                st.session_state.last_refresh = None
                st.session_state.current_data_source = None
                st.session_state.current_sheet = None
                st.success(f"Aba '{selected_sheet}' selecionada!")
            
            # Mostrar prévia dos dados da aba selecionada
            with st.expander("Prévia dos dados da aba selecionada"):
                preview_df = pd.read_excel(uploaded_file, sheet_name=selected_sheet, nrows=5)
                st.dataframe(preview_df)
            
            # Ler e processar os dados
            raw_data = pd.read_excel(uploaded_file, sheet_name=selected_sheet, engine='openpyxl')
            from utils.data_processor import process_data
            processed_preview = process_data(raw_data)
            
            if processed_preview is not None and not processed_preview.empty:
                # Mostrar informações de debug
                with st.expander("Informações de Debug", expanded=False):
                    st.write("**Colunas disponíveis:**")
                    st.write(processed_preview.columns.tolist())
                    st.write("**Tipos de dados:**")
                    st.write(processed_preview.dtypes)
                    st.write("**Primeiras linhas dos dados brutos:**")
                    st.dataframe(processed_preview.head())
                
                # Mostrar prévia dos dados processados
                with st.expander("Prévia dos dados processados"):
                    try:
                        st.write("**Informações gerais:**")
                        st.write(f"- Total de registros: {len(processed_preview)}")
                        
                        # Verificar se as colunas necessárias existem
                        if 'Date' in processed_preview.columns:
                            st.write(f"- Período: {processed_preview['Date'].min().strftime('%d/%m/%Y')} a {processed_preview['Date'].max().strftime('%d/%m/%Y')}")
                        else:
                            st.error("Coluna 'Date' não encontrada nos dados processados")
                        
                        if 'Type' in processed_preview.columns and 'Value' in processed_preview.columns:
                            receitas = processed_preview[processed_preview['Type'] == 'Entrada']['Value'].sum()
                            despesas = processed_preview[processed_preview['Type'] == 'Saída']['Value'].sum()
                            st.write(f"- Total de receitas: R$ {receitas:,.2f}")
                            st.write(f"- Total de despesas: R$ {despesas:,.2f}")
                            st.write(f"- Saldo: R$ {(receitas + despesas):,.2f}")  # Despesas já são negativas
                        else:
                            st.error("Colunas 'Type' ou 'Value' não encontradas nos dados processados")
                        
                        st.write("**Amostra dos dados processados:**")
                        st.dataframe(processed_preview.head())
                    except Exception as e:
                        st.error(f"Erro ao mostrar informações dos dados: {str(e)}")
                        st.write("**Amostra dos dados processados:**")
                        st.dataframe(processed_preview.head())
                
                # Botão para carregar os dados
                if st.button("Carregar dados da aba selecionada"):
                    with st.spinner("Carregando arquivo..."):
                        # Atualizar os dados na sessão
                        st.session_state.data = processed_preview
                        st.session_state.last_refresh = datetime.now(pytz.timezone('America/Sao_Paulo'))
                        st.session_state.current_data_source = "local_file"
                        st.session_state.current_sheet = selected_sheet
                        
                    st.success("Arquivo carregado com sucesso!")
            else:
                st.error("Não foi possível processar os dados. Verifique se a aba selecionada contém os dados financeiros corretos.")
                
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {str(e)}")
    
    # Separador
    st.markdown("---")
    
    # Informações do sistema
    st.subheader("Informações do Sistema")
    
    if 'last_refresh' in st.session_state and st.session_state.last_refresh:
        # Converter para o fuso horário do Brasil
        br_timezone = pytz.timezone('America/Sao_Paulo')
        last_refresh_br = st.session_state.last_refresh.astimezone(br_timezone)
        st.info(f"Última atualização: {last_refresh_br.strftime('%d/%m/%Y %H:%M:%S')} (Brasil)")
    
    # Versão do sistema
    st.caption("Versão 1.0.0") 