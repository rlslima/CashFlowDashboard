import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def create_sample_data(num_rows=100, output_file="example_financial_data.xlsx"):
    """
    Cria um conjunto de dados financeiros de exemplo e salva em um arquivo Excel
    
    Args:
        num_rows (int): Número de transações a serem geradas
        output_file (str): Nome do arquivo de saída
    """
    # Lista de possíveis empresas
    companies = ["Combrasen Matriz", "Combrasen Filial SP", "Combrasen Filial RJ", "Combrasen Filial MG"]
    
    # Lista de possíveis tipos de transação
    transaction_types = ["Income", "Expense"]
    
    # Lista de possíveis obras/projetos
    works = ["Obra Residencial Alfa", "Obra Comercial Beta", "Obra Industrial Gama", 
             "Obra Residencial Delta", "Obra Comercial Ômega"]
    
    # Lista de possíveis fornecedores/clientes
    entities = ["Cliente A", "Cliente B", "Cliente C", "Fornecedor X", "Fornecedor Y", 
                "Fornecedor Z", "Banco ABC", "Investidor 123"]
    
    # Gerar dados aleatórios
    # Data atual menos até 365 dias
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Gerar datas aleatórias
    dates = [start_date + timedelta(days=np.random.randint(0, 365)) for _ in range(num_rows)]
    dates = [date.strftime("%d/%m/%Y") for date in dates]
    
    # Outros dados aleatórios
    data = {
        "Company": np.random.choice(companies, num_rows),
        "Type": np.random.choice(transaction_types, num_rows, p=[0.4, 0.6]),  # Mais despesas que receitas
        "Work": np.random.choice(works, num_rows),
        "Entity": np.random.choice(entities, num_rows),
        "Value": np.random.normal(10000, 5000, num_rows).round(2),  # Valores em torno de 10.000
        "Date": dates,
        "Description": ["Transação " + str(i+1) for i in range(num_rows)]
    }
    
    # Ajustar valores de acordo com o tipo de transação
    for i in range(num_rows):
        if data["Type"][i] == "Expense":
            data["Value"][i] = abs(data["Value"][i]) * -1  # Despesas são negativas
        else:
            data["Value"][i] = abs(data["Value"][i])  # Receitas são positivas
    
    # Converter para DataFrame do pandas
    df = pd.DataFrame(data)
    
    # Salvar em arquivo Excel
    df.to_excel(output_file, index=False)
    
    print(f"Dados de exemplo criados com sucesso e salvos em '{output_file}'")
    return df

if __name__ == "__main__":
    create_sample_data(150)