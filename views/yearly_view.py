import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.data_processor import format_currency_brl

def show_yearly_view(df):
    """
    Display yearly cash flow summary
    
    Args:
        df (pandas.DataFrame): Processed and filtered DataFrame
    """
    st.header("Resumo Anual de Fluxo de Caixa")
    
    if df.empty:
        st.warning("Nenhum dado disponível com os filtros atuais.")
        return
    
    # Get all available years
    available_years = sorted(df["Year"].unique().tolist())
    
    if not available_years:
        st.warning("Nenhum dado de ano disponível.")
        return
    
    # Year selection
    col1, col2 = st.columns([1, 3])
    
    with col1:
        current_year = datetime.now().year
        default_year_index = available_years.index(current_year) if current_year in available_years else len(available_years) - 1
        selected_year = st.selectbox("Selecione o Ano", available_years, index=default_year_index if available_years else 0)
    
    # Filter data for selected year
    year_df = df[df["Year"] == selected_year].copy()
    
    if year_df.empty:
        st.warning(f"Nenhum dado disponível para {selected_year}.")
        return
    
    # Create year summary
    with col2:
        # Calculate metrics
        income_df = year_df[year_df["Type"] == "Receita"]
        expense_df = year_df[year_df["Type"] == "Despesa"]
        
        total_income = income_df["Value"].sum()
        total_expense = expense_df["Value"].sum()
        net_cashflow = total_income - total_expense
        
        # Show year summary metrics
        metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
        
        with metrics_col1:
            st.metric("Receita Total", format_currency_brl(total_income))
        
        with metrics_col2:
            st.metric("Despesas Totais", format_currency_brl(total_expense))
        
        with metrics_col3:
            st.metric(
                "Fluxo de Caixa Líquido", 
                format_currency_brl(net_cashflow),
                delta=f"{(net_cashflow/total_income*100 if total_income else 0):.1f}%" if total_income else None
            )
        
        with metrics_col4:
            # Count unique work codes
            unique_works = year_df["Work"].nunique()
            st.metric("Códigos de Trabalho", unique_works)
    
    # Yearly Overview Section
    st.subheader("Visão Geral Anual")
    
    # Create containers for different visualizations
    trends_container = st.container()
    quarterly_container = st.container()
    category_container = st.container()
    
    # Quarterly breakdown
    with quarterly_container:
        # Prepare quarterly data
        quarterly_data = year_df.groupby(["Quarter", "Type"])["Value"].sum().unstack(fill_value=0).reset_index()
        
        if "Receita" not in quarterly_data.columns:
            quarterly_data["Receita"] = 0
        
        if "Despesa" not in quarterly_data.columns:
            quarterly_data["Despesa"] = 0
        
        quarterly_data["Net"] = quarterly_data["Receita"] - quarterly_data["Despesa"]
        quarterly_data["Quarter"] = quarterly_data["Quarter"].apply(lambda q: f"T{q}")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Create quarterly comparison chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=quarterly_data["Quarter"],
                y=quarterly_data["Receita"],
                name="Receitas",
                marker_color="green"
            ))
            
            fig.add_trace(go.Bar(
                x=quarterly_data["Quarter"],
                y=quarterly_data["Despesa"],
                name="Despesas",
                marker_color="red"
            ))
            
            fig.add_trace(go.Scatter(
                x=quarterly_data["Quarter"],
                y=quarterly_data["Net"],
                name="Fluxo de Caixa Líquido",
                mode="lines+markers",
                line=dict(color="blue", width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title=f"Análise Trimestral de {selected_year}",
                xaxis_title="Trimestre",
                yaxis_title="Valor (R$)",
                legend_title="Categoria",
                barmode="group",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Create quarterly metrics table
            st.subheader("Métricas Trimestrais")
            
            # Format the dataframe for display
            display_df = quarterly_data.copy()
            display_df["Receita"] = display_df["Receita"].apply(format_currency_brl)
            display_df["Despesa"] = display_df["Despesa"].apply(format_currency_brl)
            display_df["Net"] = display_df["Net"].apply(format_currency_brl)
            
            # Renomear colunas para exibição
            display_df = display_df[["Quarter", "Receita", "Despesa", "Net"]].rename(columns={
                "Quarter": "Trimestre",
                "Net": "Líquido"
            })
            
            st.dataframe(display_df, use_container_width=True)
    
    # Monthly trends
    with trends_container:
        # Prepare monthly data
        monthly_data = year_df.groupby(["Month", "Month Name", "Type"])["Value"].sum().unstack(fill_value=0).reset_index()
        
        if "Receita" not in monthly_data.columns:
            monthly_data["Receita"] = 0
        
        if "Despesa" not in monthly_data.columns:
            monthly_data["Despesa"] = 0
        
        monthly_data["Net"] = monthly_data["Receita"] - monthly_data["Despesa"]
        monthly_data = monthly_data.sort_values("Month")
        
        # Create monthly trend chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=monthly_data["Month Name"],
            y=monthly_data["Receita"],
            name="Receitas",
            mode="lines+markers",
            line=dict(color="green", width=2),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=monthly_data["Month Name"],
            y=monthly_data["Despesa"],
            name="Despesas",
            mode="lines+markers",
            line=dict(color="red", width=2),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=monthly_data["Month Name"],
            y=monthly_data["Net"],
            name="Fluxo de Caixa Líquido",
            mode="lines+markers",
            line=dict(color="blue", width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title=f"Tendências Mensais de {selected_year}",
            xaxis_title="Mês",
            yaxis_title="Valor (R$)",
            legend_title="Categoria",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Category breakdown
    with category_container:
        st.subheader("Análise por Categorias")
        
        tab1, tab2 = st.tabs(["Por Código de Trabalho", "Por Empresa"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            # Income by work code
            with col1:
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
                    st.info("Sem dados de receita para análise por código de trabalho.")
            
            # Expense by work code
            with col2:
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
                    st.info("Sem dados de despesa para análise por código de trabalho.")
        
        with tab2:
            # Only show if we have multiple companies
            companies = year_df["Company"].unique()
            
            if len(companies) > 1:
                col1, col2 = st.columns(2)
                
                # Income by company
                with col1:
                    income_by_company = income_df.groupby("Company")["Value"].sum().reset_index()
                    if not income_by_company.empty:
                        income_by_company = income_by_company.sort_values("Value", ascending=False)
                        
                        fig = px.pie(
                            income_by_company,
                            values="Value",
                            names="Company",
                            title="Receitas por Empresa",
                            hole=0.4
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Sem dados de receita para análise por empresa.")
                
                # Expense by company
                with col2:
                    expense_by_company = expense_df.groupby("Company")["Value"].sum().reset_index()
                    if not expense_by_company.empty:
                        expense_by_company = expense_by_company.sort_values("Value", ascending=False)
                        
                        fig = px.pie(
                            expense_by_company,
                            values="Value",
                            names="Company",
                            title="Despesas por Empresa",
                            hole=0.4
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Sem dados de despesa para análise por empresa.")
            else:
                st.info("Apenas uma empresa encontrada nos dados filtrados.")
    
    # Year-over-Year Comparison (if we have more than one year of data)
    if len(available_years) > 1:
        st.subheader("Comparação Ano a Ano")
        
        # Prepare yearly comparison data
        yearly_data = df.groupby(["Year", "Type"])["Value"].sum().unstack(fill_value=0).reset_index()
        
        if "Receita" not in yearly_data.columns:
            yearly_data["Receita"] = 0
        
        if "Despesa" not in yearly_data.columns:
            yearly_data["Despesa"] = 0
        
        yearly_data["Net"] = yearly_data["Receita"] - yearly_data["Despesa"]
        
        # Create year-over-year comparison chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=yearly_data["Year"],
            y=yearly_data["Receita"],
            name="Receitas",
            marker_color="green"
        ))
        
        fig.add_trace(go.Bar(
            x=yearly_data["Year"],
            y=yearly_data["Despesa"],
            name="Despesas",
            marker_color="red"
        ))
        
        fig.add_trace(go.Scatter(
            x=yearly_data["Year"],
            y=yearly_data["Net"],
            name="Fluxo de Caixa Líquido",
            mode="lines+markers",
            line=dict(color="blue", width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Comparação Ano a Ano",
            xaxis_title="Ano",
            yaxis_title="Valor (R$)",
            legend_title="Categoria",
            barmode="group",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Create yearly metrics table
        yearly_data["Year"] = yearly_data["Year"].astype(str)
        yearly_data["Receita"] = yearly_data["Receita"].apply(format_currency_brl)
        yearly_data["Despesa"] = yearly_data["Despesa"].apply(format_currency_brl)
        yearly_data["Net"] = yearly_data["Net"].apply(format_currency_brl)
        
        # Renomear colunas para exibição
        yearly_data = yearly_data[["Year", "Receita", "Despesa", "Net"]].rename(columns={
            "Year": "Ano",
            "Net": "Líquido"
        })
        
        st.dataframe(yearly_data, use_container_width=True)
