import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_processor import format_currency_brl
from config import save_config, load_config
import json  # Importar json

def show_initial_balances_view():
    """
    Mostra a tela para gerenciar saldos bancários iniciais por empresa
    """
    st.header("Saldos Bancários Iniciais")
    
    # Carregar configurações salvas
    config = load_config()
    
    # Inicializar o estado da sessão para saldos iniciais se não existir
    if 'initial_balances' not in st.session_state:
        if 'initial_balances' in config and config['initial_balances']:
            try:
                balances_data = config['initial_balances']
                # Verificar se os dados são uma lista de dicionários
                if isinstance(balances_data, list) and all(isinstance(item, dict) for item in balances_data):
                    st.session_state.initial_balances = pd.DataFrame(balances_data)
                    # Garantir que a coluna Date existe antes de converter
                    if 'Date' in st.session_state.initial_balances.columns:
                        st.session_state.initial_balances['Date'] = pd.to_datetime(st.session_state.initial_balances['Date'])
                    else:
                         # Se a coluna 'Date' não existir, inicializar DataFrame vazio com as colunas corretas
                         st.session_state.initial_balances = pd.DataFrame(columns=['Company', 'Balance', 'Date'])
                else:
                    st.warning("Formato inválido dos saldos iniciais na configuração. Resetando...")
                    st.session_state.initial_balances = pd.DataFrame(columns=['Company', 'Balance', 'Date'])
                    config['initial_balances'] = []
                    save_config(config)
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                st.error(f"Erro ao carregar saldos iniciais da configuração: {e}. Resetando...")
                st.session_state.initial_balances = pd.DataFrame(columns=['Company', 'Balance', 'Date'])
                config['initial_balances'] = []
                save_config(config)
        else:
            st.session_state.initial_balances = pd.DataFrame(columns=['Company', 'Balance', 'Date'])

    # Garantir que initial_balances seja sempre um DataFrame
    if not isinstance(st.session_state.initial_balances, pd.DataFrame):
         st.session_state.initial_balances = pd.DataFrame(columns=['Company', 'Balance', 'Date'])

    # Formulário para adicionar novo saldo
    with st.form("new_balance_form"):
        st.subheader("Adicionar Novo Saldo")
        
        # Obter lista de empresas únicas dos dados
        if st.session_state.data is not None and 'Company' in st.session_state.data.columns:
            companies = sorted(st.session_state.data['Company'].unique())
        else:
            companies = []
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            company = st.selectbox("Empresa", options=companies)
        
        with col2:
            balance = st.number_input("Saldo Inicial (R$)", 
                                    min_value=-1.0e15, # Usar um número negativo grande em vez de -inf
                                    step=0.01,
                                    format="%.2f")
        
        with col3:
            date = st.date_input("Data do Saldo",
                               value=datetime.now(),
                               format="DD/MM/YYYY")
        
        # Botão de envio deve ser o último elemento dentro do form
        submitted = st.form_submit_button("Adicionar Saldo") 
        
        # Lógica de processamento após o botão
        if submitted:
            if company and balance is not None and date:
                try:
                    # Criar novo registro com data como string ISO
                    new_balance_data = {
                        'Company': company,
                        'Balance': float(balance),
                        'Date': pd.Timestamp(date).strftime('%Y-%m-%d')
                    }
                    new_balance_df = pd.DataFrame([new_balance_data])
                    new_balance_df['Date'] = pd.to_datetime(new_balance_df['Date']) # Converter para datetime para o DataFrame

                    # Concatenar com o DataFrame existente
                    st.session_state.initial_balances = pd.concat(
                        [st.session_state.initial_balances, new_balance_df],
                        ignore_index=True
                    )

                    # Preparar dados para salvar (converter Date de volta para string ISO)
                    balances_to_save = st.session_state.initial_balances.copy()
                    if 'Date' in balances_to_save.columns:
                         balances_to_save['Date'] = balances_to_save['Date'].dt.strftime('%Y-%m-%d')

                    # Salvar no arquivo de configuração
                    config['initial_balances'] = balances_to_save.to_dict('records')
                    save_config(config)

                    st.success("Saldo adicionado com sucesso!")
                    st.rerun() # Rerun para atualizar a lista exibida

                except Exception as e:
                    st.error(f"Erro ao adicionar saldo: {str(e)}")
            else:
                st.warning("Por favor, preencha todos os campos para adicionar o saldo.")
    
    # Mostrar saldos existentes
    st.subheader("Saldos Registrados")
    
    if not st.session_state.initial_balances.empty:
        # Formatar a tabela para exibição
        display_df = st.session_state.initial_balances.copy()
        display_df['Balance'] = display_df['Balance'].apply(format_currency_brl)
        
        # Verificar se a coluna Date existe e é do tipo datetime antes de formatar
        if 'Date' in display_df.columns and pd.api.types.is_datetime64_any_dtype(display_df['Date']):
            display_df['Date'] = display_df['Date'].dt.strftime('%d/%m/%Y')
        elif 'Date' in display_df.columns:
             # Tentar converter se não for datetime
             try:
                  display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%d/%m/%Y')
             except ValueError:
                  display_df['Date'] = 'Data Inválida'
        else:
             display_df['Date'] = 'N/A'
        
        # Adicionar botão de exclusão para cada linha
        indices_to_drop = []
        for idx in display_df.index: # Usar display_df.index
            row = display_df.loc[idx]
            col1, col2, col3, col4 = st.columns([3, 3, 3, 1])
            
            with col1:
                st.write(row['Company'])
            
            with col2:
                st.write(row['Balance'])
            
            with col3:
                st.write(row['Date'])
            
            with col4:
                if st.button("🗑️", key=f"delete_{idx}"):
                    indices_to_drop.append(idx)

        if indices_to_drop:
            try:
                 # Remover os saldos do DataFrame principal (usando os índices originais)
                 st.session_state.initial_balances = st.session_state.initial_balances.drop(indices_to_drop)

                 # Preparar dados para salvar (converter Date de volta para string ISO)
                 balances_to_save = st.session_state.initial_balances.copy()
                 if 'Date' in balances_to_save.columns:
                      balances_to_save['Date'] = balances_to_save['Date'].dt.strftime('%Y-%m-%d')

                 # Atualizar o arquivo de configuração
                 config['initial_balances'] = balances_to_save.to_dict('records')
                 save_config(config)
                 st.rerun()
            except Exception as e:
                 st.error(f"Erro ao excluir saldo: {str(e)}")
    else:
        st.info("Nenhum saldo inicial registrado.") 