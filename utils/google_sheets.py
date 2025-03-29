import pandas as pd
import io
import requests
import re
import os
import streamlit as st

def fetch_google_sheet_data(sheet_url):
    """
    Fetch data from a Google Sheet using the export URL
    
    Args:
        sheet_url (str): URL to the Google Sheet
    
    Returns:
        pandas.DataFrame: DataFrame containing the sheet data
    """
    try:
        # Extract file ID from the Google Sheets URL
        file_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', sheet_url)
        if not file_id_match:
            st.error("Invalid Google Sheets URL. Could not extract file ID.")
            return None
        
        file_id = file_id_match.group(1)
        
        # Create the export URL for XLSX format
        export_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        
        # Log the URL being accessed
        st.sidebar.expander("Debug URL", expanded=False).write(f"Accessing URL: {export_url}")
        
        # Download the file
        response = requests.get(export_url)
        
        # Log the response status
        st.sidebar.expander("Debug Response", expanded=False).write(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            st.error(f"Failed to download the spreadsheet. Status code: {response.status_code}")
            return None
        
        # Read Excel data
        excel_data = io.BytesIO(response.content)
        
        # Read the first sheet from the Excel file
        df = pd.read_excel(excel_data, engine='openpyxl')
        
        # Verificar se os dados foram carregados corretamente
        if df is not None and not df.empty:
            st.sidebar.expander("Data Loaded", expanded=False).write(f"Shape: {df.shape}")
            
            # Tentativa de criar dados de exemplo se as planilhas não tiverem dados reais
            if "Value" in df.columns and df["Value"].dtype == object:
                # Tentar converter as strings para valores numéricos
                st.sidebar.expander("Value Column", expanded=False).write(f"Valores detectados como strings, tentando converter")
        
        return df
    
    except Exception as e:
        st.error(f"Error fetching Google Sheet data: {str(e)}")
        st.sidebar.expander("Detailed Error", expanded=False).write(str(e))
        return None
