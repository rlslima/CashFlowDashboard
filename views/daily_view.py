import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
from utils.data_processor import format_currency_brl

def show_daily_view(df):
    """
    Mostra a análise de fluxo de caixa diário por Obra
    
    Args:
        df (pandas.DataFrame): DataFrame processado e filtrado
    """
    st.header("Fluxo de Caixa Diário por Obra")
    
    if df.empty:
        st.warning("Não há dados disponíveis com os filtros atuais.")
        return
    
    # Determinar o intervalo de datas
    min_date = df["Date"].min()
    max_date = df["Date"].max()
    
    # Opções de seleção de período
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Data Inicial",
            value=max_date - timedelta(days=30),
            min_value=min_date,
            max_value=max_date
        )
    
    with col2:
        end_date = st.date_input(
            "Data Final",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    
    # Filtrar dados pelo intervalo de datas selecionado
    filtered_df = df[(df["Date"] >= pd.Timestamp(start_date)) & 
                      (df["Date"] <= pd.Timestamp(end_date))]
    
    if filtered_df.empty:
        st.warning("Não há dados disponíveis para o período selecionado.")
        return
    
    # Criar visualização de fluxo de caixa diário por Obra
    st.subheader("Movimentações Diárias por Obra")
    
    # Separar receitas e despesas
    income_df = filtered_df[filtered_df["Type"] == "Receita"]
    expense_df = filtered_df[filtered_df["Type"] == "Despesa"]
    
    # Formatação visual com cores
    receita_color = "#00CC96"  # Verde
    despesa_color = "#EF553B"  # Vermelho
    
    # Obter todas as Obras únicas
    obras = filtered_df["Work"].unique()
    
    # Interface para seleção de como agrupar os dados
    group_by = st.radio(
        "Agrupar por:",
        options=["Dia", "Obra"],
        horizontal=True
    )
    
    # Criar tabelas e gráficos com base na seleção
    if group_by == "Dia":
        # Agrupar por dia
        daily_income = income_df.groupby(["Date", "Work"])["Value"].sum().reset_index()
        daily_expense = expense_df.groupby(["Date", "Work"])["Value"].sum().reset_index()
        
        # Formatar datas para exibição
        daily_income["Date_Str"] = daily_income["Date"].dt.strftime("%d/%m/%Y")
        daily_expense["Date_Str"] = daily_expense["Date"].dt.strftime("%d/%m/%Y")
        
        # Criar gráfico de barras empilhadas para receitas
        if not daily_income.empty:
            fig_income = px.bar(
                daily_income,
                x="Date",
                y="Value",
                color="Work",
                title="Receitas Diárias por Obra",
                labels={"Value": "Valor (R$)", "Date": "Data", "Work": "Obra"}
            )
            
            fig_income.update_layout(
                barmode="stack",
                xaxis_tickformat="%d/%m/%Y",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig_income, use_container_width=True)
        else:
            st.info("Não há dados de receitas para o período selecionado.")
        
        # Criar gráfico de barras empilhadas para despesas
        if not daily_expense.empty:
            fig_expense = px.bar(
                daily_expense,
                x="Date",
                y="Value",
                color="Work",
                title="Despesas Diárias por Obra",
                labels={"Value": "Valor (R$)", "Date": "Data", "Work": "Obra"}
            )
            
            fig_expense.update_layout(
                barmode="stack",
                xaxis_tickformat="%d/%m/%Y",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig_expense, use_container_width=True)
        else:
            st.info("Não há dados de despesas para o período selecionado.")
            
        # Fluxo de caixa líquido diário
        daily_net = filtered_df.groupby("Date").apply(
            lambda x: x[x["Type"] == "Receita"]["Value"].sum() - 
                     x[x["Type"] == "Despesa"]["Value"].sum()
        ).reset_index(name="Net Value")
        
        if not daily_net.empty and len(daily_net) > 1:
            fig_net = go.Figure()
            
            fig_net.add_trace(go.Scatter(
                x=daily_net["Date"],
                y=daily_net["Net Value"],
                mode="lines+markers",
                name="Fluxo de Caixa Líquido",
                line=dict(color="blue", width=2),
                marker=dict(size=6)
            ))
            
            fig_net.update_layout(
                title="Fluxo de Caixa Líquido Diário",
                xaxis_title="Data",
                yaxis_title="Valor (R$)",
                xaxis_tickformat="%d/%m/%Y",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig_net, use_container_width=True)
        
    else:  # Agrupar por Obra
        # Agrupar por Obra e calcular totais
        obra_income = income_df.groupby("Work")["Value"].sum().reset_index()
        obra_expense = expense_df.groupby("Work")["Value"].sum().reset_index()
        
        # Formatar para exibição
        obra_income["Type"] = "Receita"
        obra_expense["Type"] = "Despesa"
        
        # Tabelas de valores por Obra
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Receitas por Obra")
            if not obra_income.empty:
                obra_income = obra_income.sort_values("Value", ascending=False)
                display_income = obra_income.copy()
                display_income["Value"] = display_income["Value"].apply(format_currency_brl)
                
                st.dataframe(
                    display_income.rename(columns={"Work": "Obra", "Value": "Valor"}),
                    use_container_width=True
                )
                
                # Gráfico de barras para receitas
                fig_income = px.bar(
                    obra_income,
                    y="Work",
                    x="Value",
                    orientation="h",
                    title="Total de Receitas por Obra",
                    labels={"Value": "Valor (R$)", "Work": "Obra"},
                    color_discrete_sequence=[receita_color]
                )
                
                fig_income.update_layout(yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig_income, use_container_width=True)
            else:
                st.info("Não há dados de receitas para o período selecionado.")
        
        with col2:
            st.subheader("Despesas por Obra")
            if not obra_expense.empty:
                obra_expense = obra_expense.sort_values("Value", ascending=False)
                display_expense = obra_expense.copy()
                display_expense["Value"] = display_expense["Value"].apply(format_currency_brl)
                
                st.dataframe(
                    display_expense.rename(columns={"Work": "Obra", "Value": "Valor"}),
                    use_container_width=True
                )
                
                # Gráfico de barras para despesas
                fig_expense = px.bar(
                    obra_expense,
                    y="Work",
                    x="Value",
                    orientation="h",
                    title="Total de Despesas por Obra",
                    labels={"Value": "Valor (R$)", "Work": "Obra"},
                    color_discrete_sequence=[despesa_color]
                )
                
                fig_expense.update_layout(yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig_expense, use_container_width=True)
            else:
                st.info("Não há dados de despesas para o período selecionado.")
        
        # Saldo por Obra
        st.subheader("Saldo por Obra")
        
        # Criar dataframe com o saldo para cada Obra
        obra_balance = pd.DataFrame(columns=["Work", "Receita", "Despesa", "Saldo"])
        
        for obra in obras:
            receita = obra_income[obra_income["Work"] == obra]["Value"].sum() if not obra_income.empty else 0
            despesa = obra_expense[obra_expense["Work"] == obra]["Value"].sum() if not obra_expense.empty else 0
            saldo = receita - despesa
            
            obra_balance = pd.concat([
                obra_balance, 
                pd.DataFrame([{"Work": obra, "Receita": receita, "Despesa": despesa, "Saldo": saldo}])
            ])
        
        if not obra_balance.empty:
            # Ordenar por saldo
            obra_balance = obra_balance.sort_values("Saldo", ascending=False)
            
            # Formatar valores para exibição
            display_balance = obra_balance.copy()
            display_balance["Receita"] = display_balance["Receita"].apply(format_currency_brl)
            display_balance["Despesa"] = display_balance["Despesa"].apply(format_currency_brl)
            display_balance["Saldo"] = display_balance["Saldo"].apply(format_currency_brl)
            
            # Exibir tabela
            st.dataframe(
                display_balance.rename(columns={"Work": "Obra"}),
                use_container_width=True
            )
            
            # Gráfico de barras para o saldo
            fig_balance = go.Figure()
            
            # Adicionar barras para cada obra
            for i, row in obra_balance.iterrows():
                color = receita_color if row["Saldo"] >= 0 else despesa_color
                
                fig_balance.add_trace(go.Bar(
                    x=[row["Work"]],
                    y=[row["Saldo"]],
                    name=row["Work"],
                    marker_color=color
                ))
            
            fig_balance.update_layout(
                title="Saldo por Obra",
                xaxis_title="Obra",
                yaxis_title="Valor (R$)",
                showlegend=False,
                hovermode="closest"
            )
            
            st.plotly_chart(fig_balance, use_container_width=True)
        else:
            st.info("Não há dados suficientes para calcular o saldo por Obra.")
    
    # Tabela detalhada de transações
    st.subheader("Transações Detalhadas")
    
    # Permitir ao usuário ordenar e filtrar a tabela de transações
    sort_by = st.selectbox(
        "Ordenar por",
        options=["Data (mais recente primeiro)", "Data (mais antiga primeiro)", "Valor (maior primeiro)", "Valor (menor primeiro)"]
    )
    
    if sort_by == "Data (mais recente primeiro)":
        filtered_df = filtered_df.sort_values("Date", ascending=False)
    elif sort_by == "Data (mais antiga primeiro)":
        filtered_df = filtered_df.sort_values("Date", ascending=True)
    elif sort_by == "Valor (maior primeiro)":
        filtered_df = filtered_df.sort_values("Value", ascending=False)
    else:  # Valor (menor primeiro)
        filtered_df = filtered_df.sort_values("Value", ascending=True)
    
    # Formatar o dataframe para exibição
    display_df = filtered_df.copy()
    display_df["Date"] = display_df["Date"].dt.strftime("%d/%m/%Y")
    display_df["Value"] = display_df["Value"].apply(format_currency_brl)
    
    # Mostrar tabela com colunas selecionadas
    columns_to_show = ["Date", "Company", "Type", "Work", "Supplier/Client", "Value"]
    column_names = {
        "Date": "Data", 
        "Company": "Empresa", 
        "Type": "Tipo", 
        "Work": "Obra", 
        "Supplier/Client": "Fornecedor/Cliente", 
        "Value": "Valor"
    }
    
    display_df = display_df[columns_to_show].rename(columns=column_names)
    st.dataframe(display_df, use_container_width=True)