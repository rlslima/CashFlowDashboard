import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils.google_sheets import fetch_google_sheet_data
from utils.data_processor import process_data
from views.monthly_view import show_monthly_view
from views.period_view import show_period_view
from views.yearly_view import show_yearly_view
from views.company_view import show_company_view

# Configuração da página
st.set_page_config(
    page_title="Painel Financeiro Grupo Combrasen",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definir estado da sessão para dados
if 'data' not in st.session_state:
    st.session_state.data = None
    st.session_state.last_refresh = None

# Título e cabeçalho do aplicativo
st.title("Painel Financeiro do Grupo Combrasen")
st.markdown("---")

# Função para carregar e processar dados
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_data():
    try:
        # URL do Google Sheet
        sheet_url = "https://docs.google.com/spreadsheets/d/1XRy39MblVtmWLpggz1cC_qIRdqE40vIx/edit?usp=sharing&ouid=110344857582375962786&rtpof=true&sd=true"
        
        # Buscar dados do Google Sheets
        raw_data = fetch_google_sheet_data(sheet_url)
        
        if raw_data is not None and not raw_data.empty:
            # Processar os dados
            processed_data = process_data(raw_data)
            
            # Para debug: mostrar os dados brutos e processados
            st.sidebar.expander("Dados Brutos (Debug)", expanded=False).write(f"""
            Dados brutos: {raw_data.shape[0]} linhas
            Colunas: {raw_data.columns.tolist()}
            Primeiros valores: {str(raw_data.head(3))}
            """)
            
            if not processed_data.empty:
                st.sidebar.expander("Dados Processados (Debug)", expanded=False).write(f"""
                Processados: {processed_data.shape[0]} linhas
                Soma de valores: R$ {processed_data['Value'].sum():.2f}
                Data mínima: {processed_data['Date'].min().strftime('%d/%m/%Y')}
                Data máxima: {processed_data['Date'].max().strftime('%d/%m/%Y')}
                """)
            
            return processed_data
        else:
            st.error("Falha ao carregar dados do Google Sheets ou a planilha está vazia.")
            return None
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

# Barra lateral - Atualização e Upload de dados
with st.sidebar:
    st.title("Controles do Painel")
    
    # Adicionar opção para carregar arquivo local
    uploaded_file = st.file_uploader("Upload planilha Excel", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            with st.spinner("Carregando arquivo..."):
                # Ler o arquivo Excel
                raw_data = pd.read_excel(uploaded_file, engine='openpyxl')
                
                # Processar os dados
                processed_data = process_data(raw_data)
                
                # Atualizar os dados na sessão
                st.session_state.data = processed_data
                st.session_state.last_refresh = datetime.now()
                
            st.success("Arquivo carregado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo: {str(e)}")
    
    # Separador
    st.markdown("---")
    
    # Botão para atualizar dados (Google Sheets)
    if st.button("Atualizar via Google Sheets", use_container_width=True):
        with st.spinner("Atualizando dados..."):
            st.session_state.data = load_data()
            st.session_state.last_refresh = datetime.now()
        st.success("Dados atualizados com sucesso!")
    
    # Mostrar última hora de atualização
    if st.session_state.last_refresh:
        st.info(f"Última atualização: {st.session_state.last_refresh.strftime('%d/%m/%Y %H:%M:%S')}")
    
    st.markdown("---")
    
    # Navegação
    st.subheader("Visualizações")
    view = st.radio(
        "Selecionar Visualização",
        options=["Fluxo de Caixa Mensal", "Análise por Período", "Resumo Anual", "Comparação de Empresas"],
        label_visibility="collapsed"
    )

# Carregar dados se ainda não estiverem carregados
if st.session_state.data is None:
    with st.spinner("Carregando dados pela primeira vez..."):
        st.session_state.data = load_data()
        st.session_state.last_refresh = datetime.now()

# Mostrar dados ou mensagem de erro
if st.session_state.data is not None:
    df = st.session_state.data
    
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
            
        # Filtro de código de trabalho
        with col3:
            all_works = ["Todos"] + sorted(df["Work"].unique().tolist())
            selected_work = st.selectbox("Código de Trabalho", all_works)
    
    # Aplicar filtros globais
    filtered_df = df.copy()
    
    if selected_company != "Todas":
        filtered_df = filtered_df[filtered_df["Company"] == selected_company]
    
    if selected_type != "Todos":
        filtered_df = filtered_df[filtered_df["Type"] == selected_type]
    
    if selected_work != "Todos":
        filtered_df = filtered_df[filtered_df["Work"] == selected_work]
    
    # Exibir visualização selecionada
    if view == "Fluxo de Caixa Mensal":
        show_monthly_view(filtered_df)
    elif view == "Análise por Período":
        show_period_view(filtered_df)
    elif view == "Resumo Anual":
        show_yearly_view(filtered_df)
    elif view == "Comparação de Empresas":
        show_company_view(filtered_df)
    
else:
    st.error("Não há dados disponíveis. Por favor, verifique a conexão com o Google Sheets ou tente atualizar.")
    
    st.info("""
        Formato de dados esperado:
        - Company: ex. "Empresa A"
        - Type: "Expense" ou "Income"
        - Work: ex. "WRK01"
        - Supplier/Client: ex. "Fornecedor 1"
        - Value: ex. "35600.00"
        - Date: ex. "24/03/2025"
    """)
    
    # Oferecer um arquivo de exemplo para download
    if os.path.exists("example_financial_data.xlsx"):
        with open("example_financial_data.xlsx", "rb") as f:
            st.download_button(
                label="Baixar arquivo de exemplo",
                data=f,
                file_name="example_financial_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        st.info("""
            1. Baixe o arquivo de exemplo acima
            2. Use-o como modelo para preparar seus dados
            3. Faça upload do arquivo usando o botão na barra lateral
        """)

# Rodapé
st.markdown("---")
st.caption("Painel Financeiro do Grupo Combrasen © 2023")
