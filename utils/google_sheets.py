import pandas as pd
import io
import requests
import re
import os
import streamlit as st
from datetime import datetime
import pytz
from utils.data_processor import process_data, convert_currency_to_float

def fetch_google_sheet_data(url, sheet_name=None):
    """
    Busca dados de uma planilha do Google Sheets
    
    Args:
        url (str): URL da planilha do Google Sheets
        sheet_name (str, optional): Nome da aba específica para carregar
    
    Returns:
        pandas.DataFrame: DataFrame com os dados processados
    """
    try:
        # Verificar se a URL foi fornecida
        if not url:
            raise ValueError("URL do Google Sheets não fornecida")
            
        # Extrair o ID do arquivo da URL
        file_id = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
        if not file_id:
            raise ValueError("URL do Google Sheets inválida")
        
        file_id = file_id.group(1)
        
        # Criar URL de exportação
        export_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        
        # Debug - mostrar URL sendo acessada
        print(f"Acessando URL: {export_url}")
        
        # Fazer o download do arquivo
        response = requests.get(export_url)
        response.raise_for_status()  # Levantar exceção se houver erro
        
        # Debug - mostrar status da resposta
        print(f"Status da resposta: {response.status_code}")
        
        # Ler o arquivo Excel
        excel_file = pd.ExcelFile(io.BytesIO(response.content))
        
        # Listar abas disponíveis
        available_sheets = excel_file.sheet_names
        print(f"Abas disponíveis: {available_sheets}")
        
        # Se não foi especificada uma aba, usar a primeira
        if sheet_name is None:
            sheet_name = available_sheets[0]
            print(f"Nenhuma aba especificada, usando a primeira: {sheet_name}")
        
        # Verificar se a aba solicitada existe
        if sheet_name not in available_sheets:
            raise ValueError(f"A aba '{sheet_name}' não foi encontrada. Abas disponíveis: {available_sheets}")
        
        print(f"Carregando aba: {sheet_name}")
        
        # Ler os dados da aba
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        # Debug - mostrar informações sobre os dados carregados
        print(f"Dados carregados: {df.shape[0]} linhas x {df.shape[1]} colunas")
        print(f"Colunas: {df.columns.tolist()}")
        print(f"Tipos de dados: {df.dtypes}")
        
        # Processar os dados
        processed_df = process_data(df)
        
        # Debug - mostrar informações sobre os dados processados
        if processed_df is not None and not processed_df.empty:
            print(f"Dados processados: {processed_df.shape[0]} linhas x {processed_df.shape[1]} colunas")
            print(f"Colunas processadas: {processed_df.columns.tolist()}")
            print(f"Tipos de dados processados: {processed_df.dtypes}")
        else:
            print("ATENÇÃO: Dados processados estão vazios!")
        
        return processed_df
        
    except Exception as e:
        print(f"Erro ao carregar dados do Google Sheets: {str(e)}")
        raise

def fetch_initial_balances(url):
    """
    Busca os saldos iniciais da aba SaldoContas
    
    Args:
        url (str): URL da planilha do Google Sheets
    
    Returns:
        pandas.DataFrame: DataFrame com os saldos iniciais
    """
    try:
        # Verificar se a URL foi fornecida
        if not url:
            raise ValueError("URL do Google Sheets não fornecida")
            
        # Extrair o ID do arquivo da URL
        file_id = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
        if not file_id:
            raise ValueError("URL do Google Sheets inválida")
        
        file_id = file_id.group(1)
        
        # Criar URL de exportação
        export_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        
        # Fazer o download do arquivo
        response = requests.get(export_url)
        response.raise_for_status()
        
        # Ler a aba SaldoContas
        excel_file = pd.ExcelFile(io.BytesIO(response.content))
        
        if "SaldoContas" not in excel_file.sheet_names:
            print("Aba SaldoContas não encontrada")
            return None
            
        df = pd.read_excel(excel_file, sheet_name="SaldoContas")
        
        # Verificar se as colunas necessárias existem
        required_columns = ["Company", "Balance", "Date"]
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            print(f"Colunas ausentes na aba SaldoContas: {missing_cols}")
            return None
            
        # Processar os dados
        df["Date"] = pd.to_datetime(df["Date"])
        df["Balance"] = df["Balance"].astype(str).apply(convert_currency_to_float)
        
        print(f"Saldos iniciais carregados: {len(df)} empresas")
        print(f"Data dos saldos: {df['Date'].min().strftime('%d/%m/%Y')}")
        print("Saldos por empresa:")
        for _, row in df.iterrows():
            print(f"- {row['Company']}: {row['Balance']:,.2f}")
        
        return df
            
    except Exception as e:
        print(f"Erro ao carregar saldos iniciais: {str(e)}")
        return None
