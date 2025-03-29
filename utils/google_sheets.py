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
        
        # Download the file
        response = requests.get(export_url)
        
        if response.status_code != 200:
            st.error(f"Failed to download the spreadsheet. Status code: {response.status_code}")
            return None
        
        # Read Excel data
        excel_data = io.BytesIO(response.content)
        
        # Read the first sheet from the Excel file
        df = pd.read_excel(excel_data, engine='openpyxl')
        
        return df
    
    except Exception as e:
        st.error(f"Error fetching Google Sheet data: {str(e)}")
        return None
