import pandas as pd
import numpy as np
from datetime import datetime
import re

def process_data(df):
    """
    Process the raw dataframe from Google Sheets
    
    Args:
        df (pandas.DataFrame): Raw DataFrame from Google Sheets
    
    Returns:
        pandas.DataFrame: Processed DataFrame ready for analysis
    """
    # Create a copy of the dataframe to avoid modifying the original
    df_processed = df.copy()
    
    # Rename columns if needed (assuming the columns match our expected format)
    expected_columns = ["Company", "Type", "Work", "Supplier/Client", "Value", "Date"]
    
    # Check if columns need renaming based on their position
    if list(df_processed.columns) != expected_columns and len(df_processed.columns) == len(expected_columns):
        df_processed.columns = expected_columns
    
    # Handle missing values
    df_processed = df_processed.dropna(subset=["Value", "Date"])
    
    # Process Value column - convert from string to float
    df_processed["Value"] = df_processed["Value"].astype(str)
    df_processed["Value"] = df_processed["Value"].apply(lambda x: convert_currency_to_float(x))
    
    # Process Type column - ensure 'Expense' values are negative
    df_processed["Signed Value"] = df_processed.apply(
        lambda row: -row["Value"] if row["Type"] == "Expense" else row["Value"], 
        axis=1
    )
    
    # Process Date column - convert to datetime
    df_processed["Date"] = pd.to_datetime(df_processed["Date"], errors='coerce')
    
    # Extract additional date-related columns for analysis
    df_processed["Year"] = df_processed["Date"].dt.year
    df_processed["Month"] = df_processed["Date"].dt.month
    df_processed["Month Name"] = df_processed["Date"].dt.strftime("%b")
    df_processed["Quarter"] = df_processed["Date"].dt.quarter
    
    # Create Period (YYYY-MM) for easier grouping
    df_processed["Period"] = df_processed["Date"].dt.strftime("%Y-%m")
    
    return df_processed

def convert_currency_to_float(value_str):
    """
    Convert string currency values to float
    
    Args:
        value_str (str): String representation of currency value
    
    Returns:
        float: Numerical value
    """
    try:
        # Remove any currency symbols, commas, and spaces
        clean_value = re.sub(r'[^\d.,\-]', '', str(value_str))
        
        # Replace comma with dot if needed
        if ',' in clean_value and '.' not in clean_value:
            clean_value = clean_value.replace(',', '.')
        elif ',' in clean_value and '.' in clean_value:
            # Handle cases where thousands are separated by comma
            clean_value = clean_value.replace(',', '')
        
        # Convert to float
        return float(clean_value)
    except:
        # Return 0 if conversion fails
        return 0.0

def calculate_cash_flow_summary(df):
    """
    Calculate cash flow summary statistics
    
    Args:
        df (pandas.DataFrame): Processed DataFrame
    
    Returns:
        dict: Dictionary with summary statistics
    """
    summary = {}
    
    # Total income
    income_df = df[df["Type"] == "Income"]
    summary["total_income"] = income_df["Value"].sum()
    
    # Total expenses
    expense_df = df[df["Type"] == "Expense"]
    summary["total_expenses"] = expense_df["Value"].sum()
    
    # Net cash flow
    summary["net_cash_flow"] = summary["total_income"] - summary["total_expenses"]
    
    # Current month cash flow
    current_month = datetime.now().strftime("%Y-%m")
    current_month_df = df[df["Period"] == current_month]
    
    income_month = current_month_df[current_month_df["Type"] == "Income"]["Value"].sum()
    expense_month = current_month_df[current_month_df["Type"] == "Expense"]["Value"].sum()
    summary["current_month_net"] = income_month - expense_month
    
    return summary
