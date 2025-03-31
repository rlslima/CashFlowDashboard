import streamlit as st
import pandas as pd
from datetime import datetime

# Função para formatar moeda no padrão brasileiro
def format_currency_brl(value):
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

# Barra lateral
with st.sidebar:
    st.title("Controles do Painel")
    
    # Botão para carregar dados do arquivo de exemplo
    if st.button("Carregar Dados de Exemplo", use_container_width=True):
        st.session_state.last_refresh = datetime.now()
        st.success("Dados carregados com sucesso!")
    
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

# Verificar se o arquivo de exemplo existe
try:
    # Tentar carregar o arquivo de exemplo
    df = pd.read_excel("example_financial_data.xlsx", engine='openpyxl')
    
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
        saldo = total_receitas - total_despesas
        
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
            pivot_table['Saldo'] = pivot_table['Income'] - pivot_table['Expense']
        elif 'Income' in pivot_table.columns:
            pivot_table['Saldo'] = pivot_table['Income']
        elif 'Expense' in pivot_table.columns:
            pivot_table['Saldo'] = -pivot_table['Expense']
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
            pivot_table['Saldo'] = pivot_table['Income'] - pivot_table['Expense']
        elif 'Income' in pivot_table.columns:
            pivot_table['Saldo'] = pivot_table['Income']
        elif 'Expense' in pivot_table.columns:
            pivot_table['Saldo'] = -pivot_table['Expense']
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
            formatted_income = income_data.applymap(format_currency_brl)
            st.dataframe(formatted_income, use_container_width=True)
        else:
            st.info("Não há dados de receitas para exibir com os filtros selecionados.")
        
        st.subheader("Despesas por Obra e Data")
        if not expense_data.empty:
            # Remover linhas com valores zerados (opcional)
            expense_data = expense_data.loc[(expense_data != 0).any(axis=1)]
            
            # Aplicar formatação de moeda em toda a tabela
            formatted_expense = expense_data.applymap(format_currency_brl)
            st.dataframe(formatted_expense, use_container_width=True)
        else:
            st.info("Não há dados de despesas para exibir com os filtros selecionados.")
    
except Exception as e:
    st.error(f"Erro ao carregar os dados: {str(e)}")
    st.info("Verifique se o arquivo 'example_financial_data.xlsx' existe no diretório raiz.")

# Rodapé
st.markdown("---")
st.caption("Painel Financeiro do Grupo Combrasen © 2023")