import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests
from io import BytesIO

# Configurar o ambiente
os.environ["PYTHONPATH"] = "/home/runner/workspace/.pythonlibs/lib/python3.11/site-packages"

# Função para formatar moeda no padrão brasileiro
def format_currency_brl(value):
    if pd.isna(value):
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# Configuração da página
st.set_page_config(
    page_title="Painel Financeiro Grupo Combrasen",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Painel Financeiro do Grupo Combrasen")
st.markdown("---")

# Criar dados de exemplo diretamente
def create_sample_data():
    data = {
        "Company": ["Combrasen Matriz", "Combrasen Matriz", "Combrasen Filial SP", "Combrasen Filial RJ", 
                  "Combrasen Filial SP", "Combrasen Matriz", "Combrasen Filial MG", "Combrasen Filial RJ"],
        "Type": ["Income", "Expense", "Income", "Expense", "Expense", "Income", "Expense", "Income"],
        "Work": ["Obra Residencial Alfa", "Obra Comercial Beta", "Obra Industrial Gama", 
               "Obra Residencial Alfa", "Obra Comercial Beta", "Obra Industrial Gama", 
               "Obra Residencial Delta", "Obra Comercial Ômega"],
        "Entity": ["Cliente A", "Fornecedor X", "Cliente B", "Fornecedor Z", 
                 "Fornecedor Y", "Cliente C", "Fornecedor X", "Cliente A"],
        "Value": [15000.0, -8500.0, 12000.0, -7500.0, -9200.0, 18500.0, -6800.0, 10500.0],
        "Date": ["01/03/2023", "05/03/2023", "10/03/2023", "15/03/2023", 
                "20/03/2023", "25/03/2023", "01/04/2023", "05/04/2023"],
        "Description": ["Venda residencial", "Materiais de construção", "Serviços prestados", 
                       "Pagamento fornecedores", "Materiais elétricos", "Consultoria", 
                       "Equipamentos", "Projeto arquitetônico"]
    }
    df = pd.DataFrame(data)
    return df

# Função para carregar dados do Google Sheets via URL de exportação
def load_from_google_sheets(sheet_url):
    try:
        # Acessar a URL e baixar os dados
        response = requests.get(sheet_url)
        response.raise_for_status()  # Verificar se houve erro na requisição
        
        # Carregar os dados em um DataFrame
        excel_data = BytesIO(response.content)
        df = pd.read_excel(excel_data, engine='openpyxl')
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados da planilha: {str(e)}")
        return None

# Barra lateral
with st.sidebar:
    st.title("Controles do Painel")
    
    # Campo para URL da planilha do Google Sheets
    sheet_url = st.text_input("URL da Planilha", 
                            value="", 
                            help="Cole a URL da planilha exportada do Google Sheets")
    
    # Botão para carregar dados da planilha
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Carregar da URL", use_container_width=True):
            if sheet_url:
                # Salvar URL na sessão
                st.session_state.sheet_url = sheet_url
                st.session_state.last_refresh = datetime.now()
                st.success("URL salva! Carregando dados...")
                st.rerun()
    
    # Botão para carregar dados de exemplo
    with col2:
        if st.button("Dados de Exemplo", use_container_width=True):
            # Limpar URL da sessão
            if 'sheet_url' in st.session_state:
                del st.session_state.sheet_url
            st.session_state.last_refresh = datetime.now()
            st.success("Usando dados de exemplo!")
            st.rerun()
    
    # Mostrar última hora de atualização
    if 'last_refresh' in st.session_state:
        st.info(f"Última atualização: {st.session_state.last_refresh.strftime('%d/%m/%Y %H:%M:%S')}")
    
    st.markdown("---")
    
    # Navegação
    st.subheader("Visualizações")
    view = st.radio(
        "Selecionar Visualização",
        options=["Resumo Geral", "Fluxo de Caixa Mensal", "Comparação de Empresas", "Fluxo de Caixa Diário"],
        label_visibility="collapsed"
    )

# Tentar carregar ou criar dados de exemplo
try:
    # Verificar se há URL na sessão
    if 'sheet_url' in st.session_state and st.session_state.sheet_url:
        # Tentar carregar dados da URL
        df = load_from_google_sheets(st.session_state.sheet_url)
        if df is None:
            # Se falhar, usar dados de exemplo
            df = create_sample_data()
            st.warning("Não foi possível carregar dados da URL. Usando dados de exemplo.")
    else:
        try:
            # Tentar carregar do arquivo local
            df = pd.read_excel("example_financial_data.xlsx", engine='openpyxl')
        except:
            # Se não encontrar, criar dados de exemplo
            df = create_sample_data()
    
    # Processar dados básicos
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    df['Month'] = df['Date'].dt.month
    df['Year'] = df['Date'].dt.year
    df['MonthYear'] = df['Date'].dt.strftime('%m/%Y')
    
    # Filtros Globais
    with st.expander("Filtros Globais", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        # Filtro de empresa
        with col1:
            all_companies = ["Todas"] + sorted(df["Company"].unique().tolist())
            selected_company = st.selectbox("Empresa", all_companies)
        
        # Filtro de tipo (Despesa/Receita)
        with col2:
            all_types = ["Todos"] + sorted(df["Type"].unique().tolist())
            selected_type = st.selectbox("Tipo", all_types)
            
        # Filtro de obra
        with col3:
            all_works = ["Todas"] + sorted(df["Work"].unique().tolist())
            selected_work = st.selectbox("Obra", all_works)
    
    # Aplicar filtros globais
    filtered_df = df.copy()
    
    if selected_company != "Todas":
        filtered_df = filtered_df[filtered_df["Company"] == selected_company]
    
    if selected_type != "Todos":
        filtered_df = filtered_df[filtered_df["Type"] == selected_type]
        
    if selected_work != "Todas":
        filtered_df = filtered_df[filtered_df["Work"] == selected_work]
    
    # Exibir visualização selecionada
    if view == "Resumo Geral":
        st.subheader("Resumo Financeiro Geral")
        
        # Calcular valores básicos
        total_receitas = filtered_df[filtered_df['Type'] == 'Income']['Value'].sum()
        total_despesas = filtered_df[filtered_df['Type'] == 'Expense']['Value'].sum()
        saldo = total_receitas + total_despesas  # Despesas já são negativas
        
        # Mostrar métricas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Receitas", format_currency_brl(total_receitas))
            
        with col2:
            st.metric("Total de Despesas", format_currency_brl(total_despesas))
            
        with col3:
            st.metric("Saldo", format_currency_brl(saldo), 
                    delta="positivo" if saldo > 0 else "negativo")
        
        # Mostrar dados detalhados
        st.subheader("Amostra dos Dados")
        st.dataframe(filtered_df.head(10), use_container_width=True)
        
    elif view == "Fluxo de Caixa Mensal":
        st.subheader("Fluxo de Caixa Mensal")
        
        # Agrupar por mês e tipo
        monthly_flow = filtered_df.groupby(['MonthYear', 'Type'])['Value'].sum().reset_index()
        
        # Criar tabela dinâmica: Mês/Ano nas linhas, Tipo nas colunas
        pivot_table = monthly_flow.pivot(index='MonthYear', columns='Type', values='Value').fillna(0)
        
        # Calcular saldo
        if 'Income' in pivot_table.columns and 'Expense' in pivot_table.columns:
            pivot_table['Saldo'] = pivot_table['Income'] + pivot_table['Expense']  # Despesas já são negativas
        elif 'Income' in pivot_table.columns:
            pivot_table['Saldo'] = pivot_table['Income']
        elif 'Expense' in pivot_table.columns:
            pivot_table['Saldo'] = pivot_table['Expense']
        else:
            pivot_table['Saldo'] = 0
        
        # Renomear colunas
        pivot_table.columns = ['Receitas' if x == 'Income' else 'Despesas' if x == 'Expense' else x for x in pivot_table.columns]
        
        # Mostrar gráfico de barras
        st.bar_chart(pivot_table)
        
        # Mostrar tabela com formatação em BRL
        formatted_table = pivot_table.copy()
        for col in formatted_table.columns:
            formatted_table[col] = formatted_table[col].apply(format_currency_brl)
        
        st.dataframe(formatted_table, use_container_width=True)
        
    elif view == "Comparação de Empresas":
        st.subheader("Comparação entre Empresas")
        
        # Agrupar por empresa e tipo
        company_flow = filtered_df.groupby(['Company', 'Type'])['Value'].sum().reset_index()
        
        # Criar tabela dinâmica: Empresa nas linhas, Tipo nas colunas
        pivot_table = company_flow.pivot(index='Company', columns='Type', values='Value').fillna(0)
        
        # Calcular saldo
        if 'Income' in pivot_table.columns and 'Expense' in pivot_table.columns:
            pivot_table['Saldo'] = pivot_table['Income'] + pivot_table['Expense']  # Despesas já são negativas
        elif 'Income' in pivot_table.columns:
            pivot_table['Saldo'] = pivot_table['Income']
        elif 'Expense' in pivot_table.columns:
            pivot_table['Saldo'] = pivot_table['Expense']
        else:
            pivot_table['Saldo'] = 0
        
        # Renomear colunas
        pivot_table.columns = ['Receitas' if x == 'Income' else 'Despesas' if x == 'Expense' else x for x in pivot_table.columns]
        
        # Mostrar gráfico de barras
        st.bar_chart(pivot_table)
        
        # Mostrar tabela com formatação em BRL
        formatted_table = pivot_table.copy()
        for col in formatted_table.columns:
            formatted_table[col] = formatted_table[col].apply(format_currency_brl)
        
        st.dataframe(formatted_table, use_container_width=True)
        
    elif view == "Fluxo de Caixa Diário":
        st.subheader("Fluxo de Caixa Diário por Obra")
        
        # Agrupar por data, obra e tipo
        daily_flow = filtered_df.groupby(['Date', 'Work', 'Type'])['Value'].sum().reset_index()
        
        # Criar tabelas dinâmicas: Obras nas linhas, Datas nas colunas
        income_data = daily_flow[daily_flow['Type'] == 'Income'].pivot(index='Work', columns='Date', values='Value').fillna(0)
        expense_data = daily_flow[daily_flow['Type'] == 'Expense'].pivot(index='Work', columns='Date', values='Value').fillna(0)
        
        # Formatar datas nas colunas
        if not income_data.empty:
            income_data.columns = income_data.columns.strftime('%d/%m/%Y')
        if not expense_data.empty:
            expense_data.columns = expense_data.columns.strftime('%d/%m/%Y')
        
        # Mostrar tabelas de receitas e despesas
        st.subheader("Receitas por Obra e Data")
        if not income_data.empty:
            # Remover linhas com valores zerados (opcional)
            income_data = income_data.loc[(income_data != 0).any(axis=1)]
            
            # Aplicar formatação de moeda em toda a tabela
            formatted_income = income_data.copy()
            for col in formatted_income.columns:
                formatted_income[col] = formatted_income[col].apply(format_currency_brl)
            st.dataframe(formatted_income, use_container_width=True)
        else:
            st.info("Não há dados de receitas para exibir com os filtros selecionados.")
        
        st.subheader("Despesas por Obra e Data")
        if not expense_data.empty:
            # Remover linhas com valores zerados (opcional)
            expense_data = expense_data.loc[(expense_data != 0).any(axis=1)]
            
            # Aplicar formatação de moeda em toda a tabela
            formatted_expense = expense_data.copy()
            for col in formatted_expense.columns:
                formatted_expense[col] = formatted_expense[col].apply(format_currency_brl)
            st.dataframe(formatted_expense, use_container_width=True)
        else:
            st.info("Não há dados de despesas para exibir com os filtros selecionados.")
    
except Exception as e:
    st.error(f"Erro ao processar os dados: {str(e)}")
    st.info("Tentando usar dados de exemplo embutidos.")
    
    try:
        # Tentar usar dados de exemplo embutidos
        df = create_sample_data()
        st.success("Dados de exemplo carregados com sucesso!")
        st.rerun()
    except Exception as inner_e:
        st.error(f"Erro ao criar dados de exemplo: {str(inner_e)}")

# Rodapé
st.markdown("---")
st.caption("Painel Financeiro do Grupo Combrasen © 2023")