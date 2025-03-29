import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Criar dados de exemplo
def create_sample_data(rows=100):
    # Lista de empresas
    companies = ["Empresa A", "Empresa B", "Empresa C", "Empresa D"]
    
    # Tipos de transação
    transaction_types = ["Income", "Expense"]
    
    # Códigos de trabalho
    work_codes = ["WRK01", "WRK02", "WRK03", "PRJ01", "PRJ02", "SRV01"]
    
    # Fornecedores/clientes
    suppliers_clients = [
        "Fornecedor 1",
        "Fornecedor 2",
        "Cliente A",
        "Cliente B",
        "Cliente C",
        "Parceiro X",
        "Parceiro Y",
        "Contratante Z"
    ]
    
    # Data inicial (3 meses atrás)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    # Gerar dados aleatórios
    data = []
    for _ in range(rows):
        company = random.choice(companies)
        transaction_type = random.choice(transaction_types)
        work_code = random.choice(work_codes)
        
        # Escolher fornecedor/cliente com base no tipo de transação
        if transaction_type == "Income":
            supplier_client = random.choice([s for s in suppliers_clients if "Cliente" in s or "Contratante" in s])
        else:
            supplier_client = random.choice([s for s in suppliers_clients if "Fornecedor" in s or "Parceiro" in s])
        
        # Gerar valor
        if transaction_type == "Income":
            value = round(random.uniform(1000, 50000), 2)
        else:
            value = round(random.uniform(500, 30000), 2)
        
        # Gerar data aleatória no intervalo
        random_days = random.randint(0, (end_date - start_date).days)
        date = start_date + timedelta(days=random_days)
        
        data.append({
            "Company": company,
            "Type": transaction_type,
            "Work": work_code,
            "Supplier/Client": supplier_client,
            "Value": value,
            "Date": date
        })
    
    # Criar DataFrame
    df = pd.DataFrame(data)
    
    return df

if __name__ == "__main__":
    # Criar dados de exemplo
    sample_data = create_sample_data(rows=100)
    
    # Salvar como arquivo Excel
    sample_data.to_excel("example_financial_data.xlsx", index=False)
    
    print("Arquivo de exemplo criado: example_financial_data.xlsx")