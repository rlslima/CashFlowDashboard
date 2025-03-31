import pandas as pd
import io
import requests
import re
import os
import streamlit as st

def fetch_google_sheet_data(sheet_url, sheet_name=None):
    """
    Busca dados de uma planilha do Google Sheets usando a URL de exportação
    
    Args:
        sheet_url (str): URL para a planilha do Google
        sheet_name (str, optional): Nome da aba específica para carregar
    
    Returns:
        pandas.DataFrame: DataFrame contendo os dados da planilha
    """
    try:
        # Extrair o ID do arquivo da URL do Google Sheets
        file_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', sheet_url)
        if not file_id_match:
            st.error("URL do Google Sheets inválida. Não foi possível extrair o ID do arquivo.")
            return None
        
        file_id = file_id_match.group(1)
        
        # Criar a URL de exportação para o formato XLSX
        export_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        
        # Registrar a URL sendo acessada
        st.sidebar.expander("URL de Debug", expanded=False).write(f"Acessando URL: {export_url}")
        
        # Baixar o arquivo
        response = requests.get(export_url)
        
        # Registrar o status da resposta
        st.sidebar.expander("Resposta de Debug", expanded=False).write(f"Status da resposta: {response.status_code}")
        
        if response.status_code != 200:
            st.error(f"Falha ao baixar a planilha. Código de status: {response.status_code}")
            return None
        
        # Ler dados do Excel
        excel_data = io.BytesIO(response.content)
        
        # Se uma aba específica foi solicitada, tentar carregar apenas ela
        if sheet_name:
            try:
                df = pd.read_excel(excel_data, sheet_name=sheet_name, engine='openpyxl')
                return df
            except ValueError:
                st.warning(f"A aba '{sheet_name}' não foi encontrada. Carregando a primeira aba.")
        
        # Se não foi especificada uma aba ou ela não foi encontrada, carregar a primeira
        df = pd.read_excel(excel_data, engine='openpyxl')
        
        # Verificar se os dados foram carregados corretamente
        if df is not None and not df.empty:
            st.sidebar.expander("Dados Carregados", expanded=False).write(f"""
            Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas
            Colunas encontradas: {', '.join(df.columns.tolist())}
            """)
            
            # Imprimir informações sobre a coluna Value para debug
            if "Value" in df.columns:
                value_types = df["Value"].apply(type).value_counts().to_dict()
                sample_values = df["Value"].head(5).tolist()
                
                st.sidebar.expander("Coluna de Valor", expanded=False).write(f"""
                Tipos de dados encontrados: {value_types}
                Exemplos de valores: {sample_values}
                """)
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar dados do Google Sheets: {str(e)}")
        st.sidebar.expander("Erro Detalhado", expanded=False).write(str(e))
        return None
