import pandas as pd
import numpy as np
from datetime import datetime
import re

def process_data(df):
    """
    Processa o dataframe bruto do Google Sheets ou Excel
    
    Args:
        df (pandas.DataFrame): DataFrame bruto 
    
    Returns:
        pandas.DataFrame: DataFrame processado pronto para análise
    """
    # Criar uma cópia do dataframe para evitar modificar o original
    df_processed = df.copy()
    
    # Renomear colunas se necessário (assumindo que as colunas correspondam ao formato esperado)
    expected_columns = ["Company", "Type", "Work", "Supplier/Client", "Value", "Date"]
    
    # Verificar se as colunas precisam ser renomeadas com base em sua posição
    if list(df_processed.columns) != expected_columns and len(df_processed.columns) == len(expected_columns):
        df_processed.columns = expected_columns
    
    # Tratar valores ausentes
    df_processed = df_processed.dropna(subset=["Value", "Date"])
    
    # Processar coluna Company - garantir que não seja nula
    if "Company" in df_processed.columns:
        df_processed["Company"] = df_processed["Company"].fillna("Sem Empresa")
    else:
        df_processed["Company"] = "Sem Empresa"
    
    # Processar coluna Value - converter de string para float
    print(f"Processando {len(df_processed)} valores monetários")
    df_processed["Value"] = df_processed["Value"].astype(str)
    df_processed["Value"] = df_processed["Value"].apply(lambda x: convert_currency_to_float(x))
    
    # Imprimir valores após conversão para debug
    print("Valores após conversão:")
    print(df_processed["Value"].head(10).tolist())
    
    # Processar coluna Type - garantir que valores 'Expense' sejam negativos e traduzir tipos
    # Primeiro traduzir os tipos para português
    df_processed["Type"] = df_processed["Type"].replace({
        "Income": "Receita",
        "Expense": "Despesa"
    })
    
    # Depois aplicar os valores de sinal
    df_processed["Signed Value"] = df_processed.apply(
        lambda row: -row["Value"] if row["Type"] == "Despesa" else row["Value"], 
        axis=1
    )
    
    # Processar coluna Date - converter para datetime (formato brasileiro DD/MM/YYYY)
    try:
        # Tentar primeiro com formato padrão (vai reconhecer automaticamente)
        df_processed["Date"] = pd.to_datetime(df_processed["Date"], errors='coerce')
    except:
        # Se falhar, tentar explicitamente com formato brasileiro
        df_processed["Date"] = pd.to_datetime(df_processed["Date"], errors='coerce', 
                                              format='%d/%m/%Y', dayfirst=True)
    
    # Para debug - verificar se há datas inválidas
    invalid_dates = df_processed["Date"].isna().sum()
    if invalid_dates > 0:
        print(f"ATENÇÃO: {invalid_dates} datas não puderam ser convertidas!")
    
    # Extrair colunas adicionais relacionadas a datas para análise
    df_processed["Year"] = df_processed["Date"].dt.year
    df_processed["Month"] = df_processed["Date"].dt.month
    df_processed["Month Name"] = df_processed["Date"].dt.strftime("%b")
    df_processed["Quarter"] = df_processed["Date"].dt.quarter
    
    # Criar Período (YYYY-MM) para agrupamento mais fácil
    df_processed["Period"] = df_processed["Date"].dt.strftime("%Y-%m")
    
    # Resumo do processamento
    print(f"Processamento concluído: {len(df_processed)} linhas válidas")
    print(f"Soma total de valores: R$ {df_processed['Value'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    return df_processed

def convert_currency_to_float(value_str):
    """
    Converte valores de moeda em string para float
    Otimizado para o formato BRL (Real Brasileiro)
    
    Args:
        value_str (str): Representação em string do valor monetário
    
    Returns:
        float: Valor numérico
    """
    try:
        # Debug para verificar o valor original
        print(f"Valor original: '{value_str}' - Tipo: {type(value_str)}")
        
        # Se já for um número, apenas converter
        if isinstance(value_str, (int, float)):
            return float(value_str)
        
        # Converter para string se não for
        if not isinstance(value_str, str):
            value_str = str(value_str)
        
        # Remover símbolos de moeda (R$), espaços e caracteres não numéricos
        clean_value = re.sub(r'[^\d.,\-]', '', value_str)
        
        # Debug para verificar o valor após limpeza
        print(f"Valor após limpeza: '{clean_value}'")
        
        # Tratar valores vazios
        if not clean_value or clean_value == '.' or clean_value == ',':
            return 0.0
        
        # Formato brasileiro padrão: 1.234,56 (vírgula como separador decimal)
        # Se tiver vírgula e pontos, assumir formato brasileiro com separador de milhar
        if '.' in clean_value and ',' in clean_value:
            # Remover os pontos (separadores de milhar) e substituir vírgula por ponto
            clean_value = clean_value.replace('.', '').replace(',', '.')
        # Formato com apenas vírgula como separador decimal
        elif ',' in clean_value:
            clean_value = clean_value.replace(',', '.')
        
        # Debug para verificar o valor final antes da conversão
        print(f"Valor antes da conversão: '{clean_value}'")
        
        # Converter para float
        result = float(clean_value)
        print(f"Valor convertido: {result}")
        return result
    except Exception as e:
        # Debug mais detalhado do erro
        print(f"ERRO ao converter valor '{value_str}': {str(e)}")
        return 0.0

def format_currency_brl(value):
    """
    Formata um valor numérico para o formato de moeda brasileira
    
    Args:
        value (float): Valor numérico
    
    Returns:
        str: Valor formatado como string no formato R$ 1.234,56
    """
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calculate_cash_flow_summary(df):
    """
    Calcula estatísticas resumidas de fluxo de caixa
    
    Args:
        df (pandas.DataFrame): DataFrame processado
    
    Returns:
        dict: Dicionário com estatísticas resumidas
    """
    summary = {}
    
    # Total de receitas
    income_df = df[df["Type"] == "Receita"]
    summary["total_income"] = income_df["Value"].sum()
    
    # Total de despesas
    expense_df = df[df["Type"] == "Despesa"]
    summary["total_expenses"] = expense_df["Value"].sum()
    
    # Fluxo de caixa líquido
    summary["net_cash_flow"] = summary["total_income"] - summary["total_expenses"]
    
    # Fluxo de caixa do mês atual
    current_month = datetime.now().strftime("%Y-%m")
    current_month_df = df[df["Period"] == current_month]
    
    income_month = current_month_df[current_month_df["Type"] == "Receita"]["Value"].sum()
    expense_month = current_month_df[current_month_df["Type"] == "Despesa"]["Value"].sum()
    summary["current_month_net"] = income_month - expense_month
    
    # Adicionar quantidade de transações para o resumo
    summary["transaction_count"] = len(df)
    summary["income_transaction_count"] = len(income_df)
    summary["expense_transaction_count"] = len(expense_df)
    
    # Estatísticas adicionais
    if not df.empty:
        summary["oldest_transaction"] = df["Date"].min().strftime("%d/%m/%Y")
        summary["newest_transaction"] = df["Date"].max().strftime("%d/%m/%Y")
    else:
        summary["oldest_transaction"] = "N/A"
        summary["newest_transaction"] = "N/A"
    
    return summary
