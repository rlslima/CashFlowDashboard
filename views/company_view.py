import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.data_processor import format_currency_brl

def show_company_view(df):
    """
    Display company comparison view
    
    Args:
        df (pandas.DataFrame): Processed and filtered DataFrame
    """
    st.header("Comparação entre Empresas")
    
    if df.empty:
        st.warning("No data available with the current filters.")
        return
    
    # Get unique companies
    companies = df["Company"].unique().tolist()
    
    if len(companies) <= 1:
        st.info("This view requires multiple companies for comparison. Only one company found in the filtered data.")
        
        # If only one company, display its summary
        if len(companies) == 1:
            company_name = companies[0]
            st.subheader(f"{company_name} Summary")
            
            company_df = df[df["Company"] == company_name]
            income_df = company_df[company_df["Type"] == "Entrada"]
            expense_df = company_df[company_df["Type"] == "Saída"]
            
            total_income = income_df["Value"].sum()
            total_expense = expense_df["Value"].sum()
            net_cashflow = total_income - total_expense
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Receita Total", format_currency_brl(total_income))
            
            with col2:
                st.metric("Despesas Totais", format_currency_brl(total_expense))
            
            with col3:
                st.metric(
                    "Fluxo de Caixa Líquido", 
                    format_currency_brl(net_cashflow),
                    delta=f"{(net_cashflow/total_income*100 if total_income else 0):.1f}%" if total_income else None
                )
        
        return
    
    # Time period selection
    st.subheader("Time Period Selection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Get available years
        available_years = sorted(df["Year"].unique().tolist())
        
        if datetime.now().year in available_years:
            default_year_index = available_years.index(datetime.now().year)
        else:
            default_year_index = len(available_years) - 1 if available_years else 0
        
        selected_year = st.selectbox(
            "Select Year", 
            available_years,
            index=default_year_index if available_years else 0
        )
    
    with col2:
        period_type = st.selectbox(
            "Period Type",
            options=["Full Year", "Quarter", "Month"]
        )
        
        if period_type == "Quarter":
            selected_quarter = st.selectbox(
                "Select Quarter",
                options=["Q1 (Jan-Mar)", "Q2 (Apr-Jun)", "Q3 (Jul-Sep)", "Q4 (Oct-Dec)"]
            )
            
            # Map selected quarter to numeric value
            if selected_quarter == "Q1 (Jan-Mar)":
                quarter_num = 1
            elif selected_quarter == "Q2 (Apr-Jun)":
                quarter_num = 2
            elif selected_quarter == "Q3 (Jul-Sep)":
                quarter_num = 3
            else:  # Q4
                quarter_num = 4
                
        elif period_type == "Month":
            # Get months with data for the selected year
            months_with_data = df[df["Year"] == selected_year]["Month"].unique().tolist()
            month_options = [(i, datetime(2000, i, 1).strftime("%B")) for i in range(1, 13) if i in months_with_data]
            
            if not month_options:
                st.warning(f"No monthly data available for {selected_year}.")
                return
                
            selected_month = st.selectbox(
                "Select Month",
                options=month_options,
                format_func=lambda x: x[1],
                index=0
            )
            
            # Get the month number
            month_num = selected_month[0]
    
    # Filter data based on selected time period
    if period_type == "Full Year":
        filtered_df = df[df["Year"] == selected_year]
        period_title = f"Full Year {selected_year}"
    elif period_type == "Quarter":
        filtered_df = df[(df["Year"] == selected_year) & (df["Quarter"] == quarter_num)]
        period_title = f"{selected_quarter} {selected_year}"
    else:  # Month
        filtered_df = df[(df["Year"] == selected_year) & (df["Month"] == month_num)]
        period_title = f"{datetime(2000, month_num, 1).strftime('%B')} {selected_year}"
    
    # Check if we have data for the selected period
    if filtered_df.empty:
        st.warning(f"No data available for the selected period: {period_title}")
        return
    
    # Display period title
    st.subheader(f"Comparison for: {period_title}")
    
    # Create company comparison visualizations
    st.subheader("Company Financial Comparison")
    
    # Prepare company data
    company_data = filtered_df.groupby(["Company", "Type"])["Value"].sum().unstack(fill_value=0).reset_index()
    
    if "Entrada" not in company_data.columns:
        company_data["Entrada"] = 0
    
    if "Saída" not in company_data.columns:
        company_data["Saída"] = 0
    
    company_data["Net"] = company_data["Entrada"] - company_data["Saída"]
    company_data["Profit Margin"] = company_data.apply(
        lambda row: (row["Net"] / row["Entrada"] * 100) if row["Entrada"] > 0 else 0, 
        axis=1
    )
    
    # Sort companies by net cash flow
    company_data = company_data.sort_values("Net", ascending=False)
    
    # Create visualizations
    tabs = st.tabs(["Overview", "Entrada", "Saída", "Net Cash Flow", "Profit Margin"])
    
    with tabs[0]:
        # Overview chart with income and expenses for each company
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=company_data["Company"],
            y=company_data["Entrada"],
            name="Entrada",
            marker_color="green"
        ))
        
        fig.add_trace(go.Bar(
            x=company_data["Company"],
            y=company_data["Saída"],
            name="Saída",
            marker_color="red"
        ))
        
        fig.add_trace(go.Scatter(
            x=company_data["Company"],
            y=company_data["Net"],
            name="Net Cash Flow",
            mode="lines+markers",
            line=dict(color="blue", width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title=f"Company Financial Overview for {period_title}",
            xaxis_title="Company",
            yaxis_title="Amount",
            legend_title="Category",
            barmode="group",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary table
        display_df = company_data.copy()
        display_df["Entrada"] = display_df["Entrada"].apply(format_currency_brl)
        display_df["Saída"] = display_df["Saída"].apply(format_currency_brl)
        display_df["Net"] = display_df["Net"].apply(format_currency_brl)
        display_df["Profit Margin"] = display_df["Profit Margin"].apply(lambda x: f"{x:.2f}%")
        
        # Rename columns
        display_df = display_df[["Company", "Entrada", "Saída", "Net", "Profit Margin"]].rename(columns={
            "Company": "Empresa", 
            "Entrada": "Receitas", 
            "Saída": "Despesas", 
            "Net": "Líquido", 
            "Profit Margin": "Margem de Lucro"
        })
        
        st.dataframe(display_df, use_container_width=True)
    
    with tabs[1]:
        # Entrada comparison
        fig = px.bar(
            company_data,
            x="Company",
            y="Entrada",
            title=f"Entrada Comparison for {period_title}",
            labels={"Entrada": "Entrada Amount", "Company": "Company Name"},
            color="Entrada",
            color_continuous_scale="Greens"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Entrada by work code for each company
        st.subheader("Entrada by Work Code")
        
        income_df = filtered_df[filtered_df["Type"] == "Entrada"]
        
        if not income_df.empty:
            income_by_company_work = income_df.groupby(["Company", "Work"])["Value"].sum().reset_index()
            
            fig = px.bar(
                income_by_company_work,
                x="Company",
                y="Value",
                color="Work",
                title="Entrada by Work Code for Each Company",
                labels={"Value": "Entrada Amount", "Company": "Company Name"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No entrada data available for the selected period.")
    
    with tabs[2]:
        # Saída comparison
        fig = px.bar(
            company_data,
            x="Company",
            y="Saída",
            title=f"Saída Comparison for {period_title}",
            labels={"Saída": "Saída Amount", "Company": "Company Name"},
            color="Saída",
            color_continuous_scale="Reds"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Saída by work code for each company
        st.subheader("Saídas by Work Code")
        
        expense_df = filtered_df[filtered_df["Type"] == "Saída"]
        
        if not expense_df.empty:
            expense_by_company_work = expense_df.groupby(["Company", "Work"])["Value"].sum().reset_index()
            
            fig = px.bar(
                expense_by_company_work,
                x="Company",
                y="Value",
                color="Work",
                title="Saídas by Work Code for Each Company",
                labels={"Value": "Saída Amount", "Company": "Company Name"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No saída data available for the selected period.")
    
    with tabs[3]:
        # Net cash flow comparison
        fig = px.bar(
            company_data,
            x="Company",
            y="Net",
            title=f"Net Cash Flow Comparison for {period_title}",
            labels={"Net": "Net Cash Flow", "Company": "Company Name"},
            color="Net",
            color_continuous_scale="RdBu"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Net cash flow by work code for each company
        st.subheader("Net Cash Flow by Work Code")
        
        if not filtered_df.empty:
            # Group data by company and work code, and calculate net for each
            net_by_company_work = filtered_df.groupby(["Company", "Work", "Type"])["Value"].sum().unstack(fill_value=0).reset_index()
            
            if "Entrada" not in net_by_company_work.columns:
                net_by_company_work["Entrada"] = 0
            
            if "Saída" not in net_by_company_work.columns:
                net_by_company_work["Saída"] = 0
            
            net_by_company_work["Net"] = net_by_company_work["Entrada"] - net_by_company_work["Saída"]
            
            fig = px.bar(
                net_by_company_work,
                x="Company",
                y="Net",
                color="Work",
                title="Net Cash Flow by Work Code for Each Company",
                labels={"Net": "Net Amount", "Company": "Company Name"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tabs[4]:
        # Profit margin comparison
        fig = px.bar(
            company_data,
            x="Company",
            y="Profit Margin",
            title=f"Profit Margin Comparison for {period_title}",
            labels={"Profit Margin": "Profit Margin (%)", "Company": "Company Name"},
            color="Profit Margin",
            color_continuous_scale="RdYlGn"
        )
        
        fig.update_layout(yaxis_title="Profit Margin (%)")
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Company performance metrics
    st.subheader("Key Performance Metrics")
    
    # Prepare metrics data
    company_metrics = company_data.copy()
    
    # Add expense-to-income ratio
    company_metrics["Expense Ratio"] = company_metrics.apply(
        lambda row: (row["Saída"] / row["Entrada"] * 100) if row["Entrada"] > 0 else 0, 
        axis=1
    )
    
    # Sort by net value
    company_metrics = company_metrics.sort_values("Net", ascending=False)
    
    # Create metrics visualization
    col1, col2 = st.columns(2)
    
    with col1:
        # Profit margin chart
        fig = px.scatter(
            company_metrics,
            x="Entrada",
            y="Profit Margin",
            size="Net",
            color="Company",
            hover_name="Company",
            size_max=50,
            title="Profit Margin vs Entrada"
        )
        
        fig.update_layout(
            xaxis_title="Entrada",
            yaxis_title="Profit Margin (%)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Expense ratio chart
        fig = px.scatter(
            company_metrics,
            x="Entrada",
            y="Expense Ratio",
            size="Saída",
            color="Company",
            hover_name="Company",
            size_max=50,
            title="Expense Ratio vs Entrada"
        )
        
        fig.update_layout(
            xaxis_title="Entrada",
            yaxis_title="Expense Ratio (%)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Company ranking
    st.subheader("Company Rankings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Entrada ranking
        income_rank = company_metrics.sort_values("Entrada", ascending=False).reset_index(drop=True)
        income_rank.index = income_rank.index + 1
        income_rank = income_rank.reset_index().rename(columns={"index": "Rank"})
        
        income_display = income_rank[["Rank", "Company", "Entrada"]].copy()
        income_display["Entrada"] = income_display["Entrada"].apply(format_currency_brl)
        income_display = income_display.rename(columns={
            "Rank": "Posição",
            "Company": "Empresa",
            "Entrada": "Receita"
        })
        
        st.markdown("#### Ranking de Receitas")
        st.dataframe(income_display, use_container_width=True)
    
    with col2:
        # Net cash flow ranking
        net_rank = company_metrics.sort_values("Net", ascending=False).reset_index(drop=True)
        net_rank.index = net_rank.index + 1
        net_rank = net_rank.reset_index().rename(columns={"index": "Rank"})
        
        net_display = net_rank[["Rank", "Company", "Net"]].copy()
        net_display["Net"] = net_display["Net"].apply(format_currency_brl)
        net_display = net_display.rename(columns={
            "Rank": "Posição",
            "Company": "Empresa",
            "Net": "Fluxo Líquido"
        })
        
        st.markdown("#### Ranking de Fluxo de Caixa Líquido")
        st.dataframe(net_display, use_container_width=True)
    
    with col3:
        # Profit margin ranking
        margin_rank = company_metrics.sort_values("Profit Margin", ascending=False).reset_index(drop=True)
        margin_rank.index = margin_rank.index + 1
        margin_rank = margin_rank.reset_index().rename(columns={"index": "Rank"})
        
        margin_display = margin_rank[["Rank", "Company", "Profit Margin"]].copy()
        margin_display["Profit Margin"] = margin_display["Profit Margin"].apply(lambda x: f"{x:.2f}%")
        margin_display = margin_display.rename(columns={
            "Rank": "Posição",
            "Company": "Empresa",
            "Profit Margin": "Margem de Lucro"
        })
        
        st.markdown("#### Ranking de Margem de Lucro")
        st.dataframe(margin_display, use_container_width=True)
