import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def show_yearly_view(df):
    """
    Display yearly cash flow summary
    
    Args:
        df (pandas.DataFrame): Processed and filtered DataFrame
    """
    st.header("Yearly Cash Flow Summary")
    
    if df.empty:
        st.warning("No data available with the current filters.")
        return
    
    # Get all available years
    available_years = sorted(df["Year"].unique().tolist())
    
    if not available_years:
        st.warning("No year data available.")
        return
    
    # Year selection
    col1, col2 = st.columns([1, 3])
    
    with col1:
        current_year = datetime.now().year
        default_year_index = available_years.index(current_year) if current_year in available_years else len(available_years) - 1
        selected_year = st.selectbox("Select Year", available_years, index=default_year_index if available_years else 0)
    
    # Filter data for selected year
    year_df = df[df["Year"] == selected_year].copy()
    
    if year_df.empty:
        st.warning(f"No data available for {selected_year}.")
        return
    
    # Create year summary
    with col2:
        # Calculate metrics
        income_df = year_df[year_df["Type"] == "Income"]
        expense_df = year_df[year_df["Type"] == "Expense"]
        
        total_income = income_df["Value"].sum()
        total_expense = expense_df["Value"].sum()
        net_cashflow = total_income - total_expense
        
        # Show year summary metrics
        metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
        
        with metrics_col1:
            st.metric("Total Income", f"${total_income:,.2f}")
        
        with metrics_col2:
            st.metric("Total Expenses", f"${total_expense:,.2f}")
        
        with metrics_col3:
            st.metric(
                "Net Cash Flow", 
                f"${net_cashflow:,.2f}",
                delta=f"{(net_cashflow/total_income*100 if total_income else 0):.1f}%" if total_income else None
            )
        
        with metrics_col4:
            # Count unique work codes
            unique_works = year_df["Work"].nunique()
            st.metric("Work Codes", unique_works)
    
    # Yearly Overview Section
    st.subheader("Yearly Overview")
    
    # Create containers for different visualizations
    trends_container = st.container()
    quarterly_container = st.container()
    category_container = st.container()
    
    # Quarterly breakdown
    with quarterly_container:
        # Prepare quarterly data
        quarterly_data = year_df.groupby(["Quarter", "Type"])["Value"].sum().unstack(fill_value=0).reset_index()
        
        if "Income" not in quarterly_data.columns:
            quarterly_data["Income"] = 0
        
        if "Expense" not in quarterly_data.columns:
            quarterly_data["Expense"] = 0
        
        quarterly_data["Net"] = quarterly_data["Income"] - quarterly_data["Expense"]
        quarterly_data["Quarter"] = quarterly_data["Quarter"].apply(lambda q: f"Q{q}")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Create quarterly comparison chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=quarterly_data["Quarter"],
                y=quarterly_data["Income"],
                name="Income",
                marker_color="green"
            ))
            
            fig.add_trace(go.Bar(
                x=quarterly_data["Quarter"],
                y=quarterly_data["Expense"],
                name="Expense",
                marker_color="red"
            ))
            
            fig.add_trace(go.Scatter(
                x=quarterly_data["Quarter"],
                y=quarterly_data["Net"],
                name="Net Cash Flow",
                mode="lines+markers",
                line=dict(color="blue", width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title=f"Quarterly Breakdown for {selected_year}",
                xaxis_title="Quarter",
                yaxis_title="Amount",
                legend_title="Category",
                barmode="group",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Create quarterly metrics table
            st.subheader("Quarterly Metrics")
            
            # Format the dataframe for display
            display_df = quarterly_data.copy()
            display_df["Income"] = display_df["Income"].apply(lambda x: f"${x:,.2f}")
            display_df["Expense"] = display_df["Expense"].apply(lambda x: f"${x:,.2f}")
            display_df["Net"] = display_df["Net"].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(display_df[["Quarter", "Income", "Expense", "Net"]], use_container_width=True)
    
    # Monthly trends
    with trends_container:
        # Prepare monthly data
        monthly_data = year_df.groupby(["Month", "Month Name", "Type"])["Value"].sum().unstack(fill_value=0).reset_index()
        
        if "Income" not in monthly_data.columns:
            monthly_data["Income"] = 0
        
        if "Expense" not in monthly_data.columns:
            monthly_data["Expense"] = 0
        
        monthly_data["Net"] = monthly_data["Income"] - monthly_data["Expense"]
        monthly_data = monthly_data.sort_values("Month")
        
        # Create monthly trend chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=monthly_data["Month Name"],
            y=monthly_data["Income"],
            name="Income",
            mode="lines+markers",
            line=dict(color="green", width=2),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=monthly_data["Month Name"],
            y=monthly_data["Expense"],
            name="Expense",
            mode="lines+markers",
            line=dict(color="red", width=2),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=monthly_data["Month Name"],
            y=monthly_data["Net"],
            name="Net Cash Flow",
            mode="lines+markers",
            line=dict(color="blue", width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title=f"Monthly Trends for {selected_year}",
            xaxis_title="Month",
            yaxis_title="Amount",
            legend_title="Category",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Category breakdown
    with category_container:
        st.subheader("Category Analysis")
        
        tab1, tab2 = st.tabs(["By Work Code", "By Company"])
        
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
                        title="Income by Work Code",
                        hole=0.4
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No income data for breakdown by work code.")
            
            # Expense by work code
            with col2:
                expense_by_work = expense_df.groupby("Work")["Value"].sum().reset_index()
                if not expense_by_work.empty:
                    expense_by_work = expense_by_work.sort_values("Value", ascending=False)
                    
                    fig = px.pie(
                        expense_by_work,
                        values="Value",
                        names="Work",
                        title="Expense by Work Code",
                        hole=0.4
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No expense data for breakdown by work code.")
        
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
                            title="Income by Company",
                            hole=0.4
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No income data for breakdown by company.")
                
                # Expense by company
                with col2:
                    expense_by_company = expense_df.groupby("Company")["Value"].sum().reset_index()
                    if not expense_by_company.empty:
                        expense_by_company = expense_by_company.sort_values("Value", ascending=False)
                        
                        fig = px.pie(
                            expense_by_company,
                            values="Value",
                            names="Company",
                            title="Expense by Company",
                            hole=0.4
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No expense data for breakdown by company.")
            else:
                st.info("Only one company found in the filtered data.")
    
    # Year-over-Year Comparison (if we have more than one year of data)
    if len(available_years) > 1:
        st.subheader("Year-over-Year Comparison")
        
        # Prepare yearly comparison data
        yearly_data = df.groupby(["Year", "Type"])["Value"].sum().unstack(fill_value=0).reset_index()
        
        if "Income" not in yearly_data.columns:
            yearly_data["Income"] = 0
        
        if "Expense" not in yearly_data.columns:
            yearly_data["Expense"] = 0
        
        yearly_data["Net"] = yearly_data["Income"] - yearly_data["Expense"]
        
        # Create year-over-year comparison chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=yearly_data["Year"],
            y=yearly_data["Income"],
            name="Income",
            marker_color="green"
        ))
        
        fig.add_trace(go.Bar(
            x=yearly_data["Year"],
            y=yearly_data["Expense"],
            name="Expense",
            marker_color="red"
        ))
        
        fig.add_trace(go.Scatter(
            x=yearly_data["Year"],
            y=yearly_data["Net"],
            name="Net Cash Flow",
            mode="lines+markers",
            line=dict(color="blue", width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Year-over-Year Comparison",
            xaxis_title="Year",
            yaxis_title="Amount",
            legend_title="Category",
            barmode="group",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Create yearly metrics table
        yearly_data["Year"] = yearly_data["Year"].astype(str)
        yearly_data["Income"] = yearly_data["Income"].apply(lambda x: f"${x:,.2f}")
        yearly_data["Expense"] = yearly_data["Expense"].apply(lambda x: f"${x:,.2f}")
        yearly_data["Net"] = yearly_data["Net"].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(yearly_data[["Year", "Income", "Expense", "Net"]], use_container_width=True)
