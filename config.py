import os

# Configuração do ambiente de execução
os.environ["PYTHONPATH"] = "/home/runner/workspace/.pythonlibs/lib/python3.11/site-packages"

# Configurações do aplicativo
APP_TITLE = "Painel Financeiro do Grupo Combrasen"
APP_ICON = "💰"
DEFAULT_DATA_FILE = "example_financial_data.xlsx"

# Configurações de cores
COLORS = {
    "receita": "#0068c9",
    "despesa": "#ff2b2b",
    "saldo_positivo": "#09ab3b",
    "saldo_negativo": "#ff2b2b",
    "background": "#f5f5f5",
    "text": "#262730"
}