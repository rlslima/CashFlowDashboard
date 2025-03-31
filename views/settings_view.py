import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import io

def show_settings_view():
    """
    Mostra a página de configurações do sistema
    """
    st.header("Configurações do Sistema")
    
    # Configurações do Google Sheets
    st.subheader("Configurações do Google Sheets")
    
    # URL do Google Sheet
    if 'sheet_url' not in st.session_state:
        st.session_state.sheet_url = "https://docs.google.com/spreadsheets/d/1XRy39MblVtmWLpggz1cC_qIRdqE40vIx/edit?usp=sharing&ouid=110344857582375962786&rtpof=true&sd=true"
    
    new_url = st.text_input(
        "URL do Google Sheet",
        value=st.session_state.sheet_url,
        help="Cole aqui a URL da planilha do Google Sheets"
    )
    
    if new_url != st.session_state.sheet_url:
        st.session_state.sheet_url = new_url
        st.success("URL do Google Sheets atualizada!")
    
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
            # Ler todas as abas disponíveis
            excel_file = pd.ExcelFile(uploaded_file)
            available_sheets = excel_file.sheet_names
            
            # Inicializar a aba selecionada na sessão se ainda não existir
            if 'selected_sheet' not in st.session_state:
                st.session_state.selected_sheet = available_sheets[0]
            
            # Selecionar a aba
            selected_sheet = st.selectbox(
                "Selecione a aba com os dados financeiros",
                options=available_sheets,
                index=available_sheets.index(st.session_state.selected_sheet),
                help="Escolha a aba que contém os dados financeiros"
            )
            
            # Atualizar a aba selecionada na sessão
            if selected_sheet != st.session_state.selected_sheet:
                st.session_state.selected_sheet = selected_sheet
                st.success(f"Aba '{selected_sheet}' selecionada!")
            
            # Mostrar prévia dos dados da aba selecionada
            with st.expander("Prévia dos dados da aba selecionada"):
                preview_df = pd.read_excel(uploaded_file, sheet_name=selected_sheet, nrows=5)
                st.dataframe(preview_df)
            
            # Botão para carregar os dados
            if st.button("Carregar dados da aba selecionada"):
                with st.spinner("Carregando arquivo..."):
                    # Ler o arquivo Excel da aba selecionada
                    raw_data = pd.read_excel(uploaded_file, sheet_name=selected_sheet, engine='openpyxl')
                    
                    # Processar os dados
                    from utils.data_processor import process_data
                    processed_data = process_data(raw_data)
                    
                    # Atualizar os dados na sessão
                    st.session_state.data = processed_data
                    st.session_state.last_refresh = datetime.now(pytz.timezone('America/Sao_Paulo'))
                    
                st.success("Arquivo carregado com sucesso!")
                
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