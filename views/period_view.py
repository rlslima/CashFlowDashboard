import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar

def show_period_view(df):
    """
    Mostra a análise de fluxo de caixa baseada em períodos
    
    Args:
        df (pandas.DataFrame): DataFrame processado e filtrado
    """
    st.header("Análise de Fluxo de Caixa por Período")
    
    if df.empty:
        st.warning("Não há dados disponíveis com os filtros atuais.")
        return
    
    # Opções de seleção de período
    col1, col2 = st.columns(2)
    
    with col1:
        period_type = st.selectbox(
            "Tipo de Período",
            options=["Intervalo de Datas", "Trimestre", "Semestre", "Meses Personalizados"]
        )
    
    # Intervalo de datas para todo o conjunto de dados
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()
    
    # Filtragem com base no tipo de período
    if period_type == "Intervalo de Datas":
        with col2:
            date_range = st.date_input(
                "Selecione o Intervalo de Datas",
                value=(
                    min_date,
                    max_date
                ),
                min_value=min_date,
                max_value=max_date
            )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = df[(df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)]
            # Formato brasileiro de data
            period_title = f"{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"
        else:
            st.warning("Por favor, selecione as datas de início e fim.")
            return
    
    elif period_type == "Trimestre":
        with col2:
            years = sorted(df["Year"].unique().tolist())
            selected_year = st.selectbox("Selecione o Ano", years, index=len(years)-1 if years else 0)
            
            quarter = st.selectbox(
                "Selecione o Trimestre",
                options=["T1 (Jan-Mar)", "T2 (Abr-Jun)", "T3 (Jul-Set)", "T4 (Out-Dez)"]
            )
        
        if quarter == "T1 (Jan-Mar)":
            start_date = f"{selected_year}-01-01"
            end_date = f"{selected_year}-03-31"
        elif quarter == "T2 (Abr-Jun)":
            start_date = f"{selected_year}-04-01"
            end_date = f"{selected_year}-06-30"
        elif quarter == "T3 (Jul-Set)":
            start_date = f"{selected_year}-07-01"
            end_date = f"{selected_year}-09-30"
        else:  # T4
            start_date = f"{selected_year}-10-01"
            end_date = f"{selected_year}-12-31"
            
        start_date_dt = pd.to_datetime(start_date)
        end_date_dt = pd.to_datetime(end_date)
        filtered_df = df[(df["Date"] >= start_date_dt) & (df["Date"] <= end_date_dt)]
        period_title = f"{quarter} {selected_year}"
    
    elif period_type == "Semestre":
        with col2:
            years = sorted(df["Year"].unique().tolist())
            selected_year = st.selectbox("Selecione o Ano", years, index=len(years)-1 if years else 0)
            
            half = st.selectbox(
                "Selecione o Semestre",
                options=["S1 (Jan-Jun)", "S2 (Jul-Dez)"]
            )
        
        if half == "S1 (Jan-Jun)":
            start_date = f"{selected_year}-01-01"
            end_date = f"{selected_year}-06-30"
        else:  # S2
            start_date = f"{selected_year}-07-01"
            end_date = f"{selected_year}-12-31"
            
        start_date_dt = pd.to_datetime(start_date)
        end_date_dt = pd.to_datetime(end_date)
        filtered_df = df[(df["Date"] >= start_date_dt) & (df["Date"] <= end_date_dt)]
        period_title = f"{half} {selected_year}"
    
    else:  # Meses Personalizados
        with col2:
            # Usando nomes de meses em português
            meses_ptbr = [
                "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
            ]
            months = [(i+1, meses_ptbr[i]) for i in range(12)]
            
            selected_months = st.multiselect(
                "Selecione os Meses",
                options=months,
                format_func=lambda x: x[1],
                default=[months[datetime.now().month-1]] if months else None
            )
            
            years = sorted(df["Year"].unique().tolist())
            selected_year = st.selectbox("Selecione o Ano", years, index=len(years)-1 if years else 0)
        
        if not selected_months:
            st.warning("Por favor, selecione pelo menos um mês.")
            return
        
        # Obter números dos meses
        month_nums = [month[0] for month in selected_months]
        filtered_df = df[(df["Year"] == selected_year) & (df["Month"].isin(month_nums))]
        
        # Criar título do período com nomes dos meses
        month_names = [month[1] for month in selected_months]
        period_title = f"{', '.join(month_names)} de {selected_year}"
    
    # Verificar se temos dados para o período selecionado
    if filtered_df.empty:
        st.warning(f"Não há dados disponíveis para o período selecionado: {period_title}")
        return
    
    # Exibir título do período
    st.subheader(f"Análise para: {period_title}")
    
    # Criar contêineres para diferentes visualizações
    summary_container = st.container()
    trends_container = st.container()
    breakdown_container = st.container()
    
    # Métricas de resumo
    with summary_container:
        st.subheader("Resumo do Período")
        
        col1, col2, col3, col4 = st.columns(4)
        
        income_df = filtered_df[filtered_df["Type"] == "Income"]
        expense_df = filtered_df[filtered_df["Type"] == "Expense"]
        
        total_income = income_df["Value"].sum()
        total_expense = expense_df["Value"].sum()
        net_cashflow = total_income - total_expense
        
        with col1:
            st.metric("Receitas Totais", f"R$ {total_income:,.2f}")
        
        with col2:
            st.metric("Despesas Totais", f"R$ {total_expense:,.2f}")
        
        with col3:
            st.metric(
                "Fluxo de Caixa Líquido", 
                f"R$ {net_cashflow:,.2f}",
                delta=f"{(net_cashflow/total_income*100 if total_income else 0):.1f}%" if total_income else None
            )
        
        with col4:
            # Calcular transações únicas e empresas
            st.metric("Total de Transações", filtered_df.shape[0])
    
    # Tendências ao longo do tempo (se aplicável)
    with trends_container:
        st.subheader("Tendências de Fluxo de Caixa")
        
        # Agrupar por data para análise de tendência
        daily_data = filtered_df.groupby(["Date", "Type"])["Value"].sum().unstack(fill_value=0).reset_index()
        
        if "Income" not in daily_data.columns:
            daily_data["Income"] = 0
        
        if "Expense" not in daily_data.columns:
            daily_data["Expense"] = 0
        
        daily_data["Net"] = daily_data["Income"] - daily_data["Expense"]
        daily_data["Cumulative Net"] = daily_data["Net"].cumsum()
        
        # Gráfico de linha para fluxo de caixa acumulado
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_data["Date"],
            y=daily_data["Cumulative Net"],
            mode="lines",
            name="Fluxo de Caixa Acumulado",
            line=dict(width=3, color="blue")
        ))
        
        # Adicionar receitas e despesas como gráfico de barras
        fig.add_trace(go.Bar(
            x=daily_data["Date"],
            y=daily_data["Income"],
            name="Receitas",
            marker_color="green",
            opacity=0.7
        ))
        
        fig.add_trace(go.Bar(
            x=daily_data["Date"],
            y=daily_data["Expense"] * -1,  # Negativo para mostrar abaixo do eixo
            name="Despesas",
            marker_color="red",
            opacity=0.7
        ))
        
        fig.update_layout(
            title="Tendências Diárias de Fluxo de Caixa",
            barmode="relative",
            xaxis_title="Data",
            yaxis_title="Valor (R$)",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Análise por categorias
    with breakdown_container:
        st.subheader("Análise de Despesas e Receitas")
        
        tab1, tab2 = st.tabs(["Por Código de Trabalho", "Por Fornecedor/Cliente"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            # Análise de despesas por código de trabalho
            with col1:
                expense_by_work = expense_df.groupby("Work")["Value"].sum().reset_index()
                if not expense_by_work.empty:
                    expense_by_work = expense_by_work.sort_values("Value", ascending=False)
                    
                    fig = px.pie(
                        expense_by_work,
                        values="Value",
                        names="Work",
                        title="Despesas por Código de Trabalho",
                        hole=0.4
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Não há dados de despesas para análise por código de trabalho.")
            
            # Análise de receitas por código de trabalho
            with col2:
                income_by_work = income_df.groupby("Work")["Value"].sum().reset_index()
                if not income_by_work.empty:
                    income_by_work = income_by_work.sort_values("Value", ascending=False)
                    
                    fig = px.pie(
                        income_by_work,
                        values="Value",
                        names="Work",
                        title="Receitas por Código de Trabalho",
                        hole=0.4
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Não há dados de receitas para análise por código de trabalho.")
        
        with tab2:
            # Mostrar principais fornecedores/clientes
            col1, col2 = st.columns(2)
            
            # Principais fornecedores de despesas
            with col1:
                top_suppliers = expense_df.groupby("Supplier/Client")["Value"].sum().reset_index()
                top_suppliers = top_suppliers.sort_values("Value", ascending=False).head(10)
                
                if not top_suppliers.empty:
                    fig = px.bar(
                        top_suppliers,
                        x="Value",
                        y="Supplier/Client",
                        orientation="h",
                        title="Top 10 Fornecedores (Despesas)",
                        labels={"Value": "Valor (R$)", "Supplier/Client": "Fornecedor"}
                    )
                    
                    fig.update_layout(yaxis={"categoryorder": "total ascending"})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Não há dados de fornecedores disponíveis.")
            
            # Principais clientes de receitas
            with col2:
                top_clients = income_df.groupby("Supplier/Client")["Value"].sum().reset_index()
                top_clients = top_clients.sort_values("Value", ascending=False).head(10)
                
                if not top_clients.empty:
                    fig = px.bar(
                        top_clients,
                        x="Value",
                        y="Supplier/Client",
                        orientation="h",
                        title="Top 10 Clientes (Receitas)",
                        labels={"Value": "Valor (R$)", "Supplier/Client": "Cliente"}
                    )
                    
                    fig.update_layout(yaxis={"categoryorder": "total ascending"})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Não há dados de clientes disponíveis.")
    
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
    display_df["Value"] = display_df["Value"].apply(lambda x: f"R$ {x:,.2f}")
    
    # Mostrar tabela com colunas selecionadas
    columns_to_show = ["Date", "Company", "Type", "Work", "Supplier/Client", "Value"]
    column_names = {
        "Date": "Data", 
        "Company": "Empresa", 
        "Type": "Tipo", 
        "Work": "Cód. Trabalho", 
        "Supplier/Client": "Fornecedor/Cliente", 
        "Value": "Valor"
    }
    
    display_df = display_df[columns_to_show].rename(columns=column_names)
    st.dataframe(display_df, use_container_width=True)
