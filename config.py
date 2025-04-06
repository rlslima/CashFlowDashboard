import os
import json

# Configuração do ambiente de execução
os.environ["PYTHONPATH"] = "/home/runner/workspace/.pythonlibs/lib/python3.11/site-packages"

# Configurações do aplicativo
APP_TITLE = "Painel Financeiro do Grupo Combrasen"
APP_ICON = "💰"
DEFAULT_DATA_FILE = "example_financial_data.xlsx"
CONFIG_FILE = ".streamlit/config.json"

# Configurações de cores
COLORS = {
    "receita": "#0068c9",
    "despesa": "#ff2b2b",
    "saldo_positivo": "#09ab3b",
    "saldo_negativo": "#ff2b2b",
    "background": "#f5f5f5",
    "text": "#262730"
}

def save_config(config_data):
    """
    Salva as configurações em um arquivo JSON
    """
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f)

def load_config():
    """
    Carrega as configurações do arquivo JSON
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}