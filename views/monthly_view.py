import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import calendar

def show_monthly_view(df):
    """
    Display monthly cash flow visualization
    
    Args:
        df (pandas.DataFrame): Processed and filtered DataFrame
    """
    st.header("Análise de Fluxo de Caixa Mensal")
    
    if df.empty:
        st.warning("Nenhum dado disponível com os filtros atuais.")
        return
    
    # Get current year and available years for selection
    current_year = datetime.now().year
    available_years = sorted(df["Year"].unique().tolist())
    
    if not available_years:
        st.warning("Nenhum dado de ano disponível.")
        return
    
    default_year = current_year if current_year in available_years else available_years[-1]
    
    # Year selection
    selected_year = st.selectbox("Selecione o Ano", available_years, index=available_years.index(default_year) if default_year in available_years else 0)
    
    # Filter data for selected year
    year_df = df[df["Year"] == selected_year].copy()
    
    if year_df.empty:
        st.warning(f"Nenhum dado disponível para {selected_year}.")
        return
    
    # Prepare monthly aggregation
    monthly_data = []
    
    for month in range(1, 13):
        month_name = calendar.month_name[month]
        month_df = year_df[year_df["Month"] == month]
        
        income = month_df[month_df["Type"] == "Receita"]["Value"].sum()
        expense = month_df[month_df["Type"] == "Despesa"]["Value"].sum()
        net = income - expense
        
        monthly_data.append({
            "Month": month,
            "Month Name": month_name,
            "Income": income,
            "Expense": expense,
            "Net": net
        })
    
    monthly_df = pd.DataFrame(monthly_data)
    
    # Create visualizations
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Monthly cash flow chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=monthly_df["Month Name"],
            y=monthly_df["Income"],
            name="Receitas",
            marker_color="green"
        ))
        
        fig.add_trace(go.Bar(
            x=monthly_df["Month Name"],
            y=monthly_df["Expense"],
            name="Despesas",
            marker_color="red"
        ))
        
        fig.add_trace(go.Scatter(
            x=monthly_df["Month Name"],
            y=monthly_df["Net"],
            name="Fluxo de Caixa Líquido",
            mode="lines+markers",
            line=dict(color="blue", width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title=f"Fluxo de Caixa Mensal de {selected_year}",
            xaxis_title="Mês",
            yaxis_title="Valor (R$)",
            legend_title="Categoria",
            barmode="group",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Summary metrics
        st.subheader("Resumo Anual")
        
        total_income = monthly_df["Income"].sum()
        total_expense = monthly_df["Expense"].sum()
        total_net = total_income - total_expense
        
        st.metric("Receita Total", f"R$ {total_income:,.2f}")
        st.metric("Despesas Totais", f"R$ {total_expense:,.2f}")
        st.metric("Fluxo de Caixa Líquido", f"R$ {total_net:,.2f}", delta=f"{(total_net/total_income*100 if total_income else 0):.1f}%" if total_income else None)
        
        # Monthly average metrics
        st.subheader("Médias Mensais")
        avg_income = total_income / 12
        avg_expense = total_expense / 12
        avg_net = total_net / 12
        
        st.metric("Receita Média", f"R$ {avg_income:,.2f}")
        st.metric("Despesa Média", f"R$ {avg_expense:,.2f}")
        st.metric("Fluxo Líquido Médio", f"R$ {avg_net:,.2f}")
    
    # Monthly breakdown table
    st.subheader("Detalhamento Mensal")
    
    # Format the dataframe for display
    display_df = monthly_df.copy()
    display_df["Income"] = display_df["Income"].apply(lambda x: f"R$ {x:,.2f}")
    display_df["Expense"] = display_df["Expense"].apply(lambda x: f"R$ {x:,.2f}")
    display_df["Net"] = display_df["Net"].apply(lambda x: f"R$ {x:,.2f}")
    
    # Rename display columns
    display_df = display_df[["Month Name", "Income", "Expense", "Net"]].rename(columns={
        "Month Name": "Mês",
        "Income": "Receitas",
        "Expense": "Despesas",
        "Net": "Líquido"
    })
    
    # Only show Month Name and financial columns
    st.dataframe(display_df, use_container_width=True)
    
    # Top transactions for the year
    st.subheader("Principais Transações")
    
    tab1, tab2 = st.tabs(["Maiores Despesas", "Maiores Receitas"])
    
    with tab1:
        top_expenses = year_df[year_df["Type"] == "Despesa"].sort_values("Value", ascending=False).head(10)
        if not top_expenses.empty:
            expense_fig = px.bar(
                top_expenses,
                x="Value",
                y="Supplier/Client",
                color="Month Name",
                orientation="h",
                title="Top 10 Despesas",
                labels={"Value": "Valor (R$)", "Supplier/Client": "Fornecedor", "Month Name": "Mês"}
            )
            st.plotly_chart(expense_fig, use_container_width=True)
        else:
            st.info("Não há dados de despesas disponíveis.")
    
    with tab2:
        top_income = year_df[year_df["Type"] == "Receita"].sort_values("Value", ascending=False).head(10)
        if not top_income.empty:
            income_fig = px.bar(
                top_income,
                x="Value",
                y="Supplier/Client",
                color="Month Name",
                orientation="h",
                title="Top 10 Fontes de Receita",
                labels={"Value": "Valor (R$)", "Supplier/Client": "Cliente", "Month Name": "Mês"}
            )
            st.plotly_chart(income_fig, use_container_width=True)
        else:
            st.info("Não há dados de receitas disponíveis.")
