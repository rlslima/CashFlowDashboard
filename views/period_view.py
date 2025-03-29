import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar

def show_period_view(df):
    """
    Display period-based cash flow analysis
    
    Args:
        df (pandas.DataFrame): Processed and filtered DataFrame
    """
    st.header("Period-Based Cash Flow Analysis")
    
    if df.empty:
        st.warning("No data available with the current filters.")
        return
    
    # Period selection options
    col1, col2 = st.columns(2)
    
    with col1:
        period_type = st.selectbox(
            "Period Type",
            options=["Custom Date Range", "Quarter", "Half-Year", "Custom Months"]
        )
    
    # Date range for the whole dataset
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()
    
    # Filter based on period type
    if period_type == "Custom Date Range":
        with col2:
            date_range = st.date_input(
                "Select Date Range",
                value=(
                    (datetime.now() - timedelta(days=90)).date(),
                    datetime.now().date()
                ),
                min_value=min_date,
                max_value=max_date
            )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = df[(df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)]
            period_title = f"{start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}"
        else:
            st.warning("Please select both start and end dates.")
            return
    
    elif period_type == "Quarter":
        with col2:
            years = sorted(df["Year"].unique().tolist())
            selected_year = st.selectbox("Select Year", years, index=len(years)-1 if years else 0)
            
            quarter = st.selectbox(
                "Select Quarter",
                options=["Q1 (Jan-Mar)", "Q2 (Apr-Jun)", "Q3 (Jul-Sep)", "Q4 (Oct-Dec)"]
            )
        
        if quarter == "Q1 (Jan-Mar)":
            start_date = f"{selected_year}-01-01"
            end_date = f"{selected_year}-03-31"
        elif quarter == "Q2 (Apr-Jun)":
            start_date = f"{selected_year}-04-01"
            end_date = f"{selected_year}-06-30"
        elif quarter == "Q3 (Jul-Sep)":
            start_date = f"{selected_year}-07-01"
            end_date = f"{selected_year}-09-30"
        else:  # Q4
            start_date = f"{selected_year}-10-01"
            end_date = f"{selected_year}-12-31"
            
        filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
        period_title = f"{quarter} {selected_year}"
    
    elif period_type == "Half-Year":
        with col2:
            years = sorted(df["Year"].unique().tolist())
            selected_year = st.selectbox("Select Year", years, index=len(years)-1 if years else 0)
            
            half = st.selectbox(
                "Select Half",
                options=["H1 (Jan-Jun)", "H2 (Jul-Dec)"]
            )
        
        if half == "H1 (Jan-Jun)":
            start_date = f"{selected_year}-01-01"
            end_date = f"{selected_year}-06-30"
        else:  # H2
            start_date = f"{selected_year}-07-01"
            end_date = f"{selected_year}-12-31"
            
        filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
        period_title = f"{half} {selected_year}"
    
    else:  # Custom Months
        with col2:
            months = []
            for i in range(1, 13):
                months.append((i, calendar.month_name[i]))
            
            selected_months = st.multiselect(
                "Select Months",
                options=months,
                format_func=lambda x: x[1],
                default=[months[datetime.now().month-1]] if months else None
            )
            
            years = sorted(df["Year"].unique().tolist())
            selected_year = st.selectbox("Select Year", years, index=len(years)-1 if years else 0)
        
        if not selected_months:
            st.warning("Please select at least one month.")
            return
        
        # Get month numbers
        month_nums = [month[0] for month in selected_months]
        filtered_df = df[(df["Year"] == selected_year) & (df["Month"].isin(month_nums))]
        
        # Create period title with month names
        month_names = [month[1] for month in selected_months]
        period_title = f"{', '.join(month_names)} {selected_year}"
    
    # Check if we have data for the selected period
    if filtered_df.empty:
        st.warning(f"No data available for the selected period: {period_title}")
        return
    
    # Display period title
    st.subheader(f"Analysis for: {period_title}")
    
    # Create containers for different visualizations
    summary_container = st.container()
    trends_container = st.container()
    breakdown_container = st.container()
    
    # Summary metrics
    with summary_container:
        st.subheader("Period Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        income_df = filtered_df[filtered_df["Type"] == "Income"]
        expense_df = filtered_df[filtered_df["Type"] == "Expense"]
        
        total_income = income_df["Value"].sum()
        total_expense = expense_df["Value"].sum()
        net_cashflow = total_income - total_expense
        
        with col1:
            st.metric("Total Income", f"${total_income:,.2f}")
        
        with col2:
            st.metric("Total Expenses", f"${total_expense:,.2f}")
        
        with col3:
            st.metric(
                "Net Cash Flow", 
                f"${net_cashflow:,.2f}",
                delta=f"{(net_cashflow/total_income*100 if total_income else 0):.1f}%" if total_income else None
            )
        
        with col4:
            # Calculate unique companies and transactions
            st.metric("Total Transactions", filtered_df.shape[0])
    
    # Trends over time (if applicable)
    with trends_container:
        st.subheader("Cash Flow Trends")
        
        # Group by date for trend analysis
        daily_data = filtered_df.groupby(["Date", "Type"])["Value"].sum().unstack(fill_value=0).reset_index()
        
        if "Income" not in daily_data.columns:
            daily_data["Income"] = 0
        
        if "Expense" not in daily_data.columns:
            daily_data["Expense"] = 0
        
        daily_data["Net"] = daily_data["Income"] - daily_data["Expense"]
        daily_data["Cumulative Net"] = daily_data["Net"].cumsum()
        
        # Line chart for cumulative cash flow
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_data["Date"],
            y=daily_data["Cumulative Net"],
            mode="lines",
            name="Cumulative Cash Flow",
            line=dict(width=3, color="blue")
        ))
        
        # Add income and expense as bar chart
        fig.add_trace(go.Bar(
            x=daily_data["Date"],
            y=daily_data["Income"],
            name="Income",
            marker_color="green",
            opacity=0.7
        ))
        
        fig.add_trace(go.Bar(
            x=daily_data["Date"],
            y=daily_data["Expense"] * -1,  # Negative to show below axis
            name="Expense",
            marker_color="red",
            opacity=0.7
        ))
        
        fig.update_layout(
            title="Daily Cash Flow Trends",
            barmode="relative",
            xaxis_title="Date",
            yaxis_title="Amount",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Breakdown by categories
    with breakdown_container:
        st.subheader("Expense & Income Breakdown")
        
        tab1, tab2 = st.tabs(["By Work Code", "By Supplier/Client"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            # Expense breakdown by work code
            with col1:
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
            
            # Income breakdown by work code
            with col2:
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
        
        with tab2:
            # Show top suppliers/clients
            col1, col2 = st.columns(2)
            
            # Top expense vendors
            with col1:
                top_suppliers = expense_df.groupby("Supplier/Client")["Value"].sum().reset_index()
                top_suppliers = top_suppliers.sort_values("Value", ascending=False).head(10)
                
                if not top_suppliers.empty:
                    fig = px.bar(
                        top_suppliers,
                        x="Value",
                        y="Supplier/Client",
                        orientation="h",
                        title="Top 10 Expense Suppliers",
                        labels={"Value": "Amount", "Supplier/Client": "Supplier/Vendor"}
                    )
                    
                    fig.update_layout(yaxis={"categoryorder": "total ascending"})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No supplier data available.")
            
            # Top income clients
            with col2:
                top_clients = income_df.groupby("Supplier/Client")["Value"].sum().reset_index()
                top_clients = top_clients.sort_values("Value", ascending=False).head(10)
                
                if not top_clients.empty:
                    fig = px.bar(
                        top_clients,
                        x="Value",
                        y="Supplier/Client",
                        orientation="h",
                        title="Top 10 Income Clients",
                        labels={"Value": "Amount", "Supplier/Client": "Client"}
                    )
                    
                    fig.update_layout(yaxis={"categoryorder": "total ascending"})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No client data available.")
    
    # Detailed transaction table
    st.subheader("Detailed Transactions")
    
    # Allow user to sort and filter the transaction table
    sort_by = st.selectbox(
        "Sort by",
        options=["Date (newest first)", "Date (oldest first)", "Value (highest first)", "Value (lowest first)"]
    )
    
    if sort_by == "Date (newest first)":
        filtered_df = filtered_df.sort_values("Date", ascending=False)
    elif sort_by == "Date (oldest first)":
        filtered_df = filtered_df.sort_values("Date", ascending=True)
    elif sort_by == "Value (highest first)":
        filtered_df = filtered_df.sort_values("Value", ascending=False)
    else:  # Value (lowest first)
        filtered_df = filtered_df.sort_values("Value", ascending=True)
    
    # Format the dataframe for display
    display_df = filtered_df.copy()
    display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
    display_df["Value"] = display_df["Value"].apply(lambda x: f"${x:,.2f}")
    
    # Show table with selected columns
    columns_to_show = ["Date", "Company", "Type", "Work", "Supplier/Client", "Value"]
    st.dataframe(display_df[columns_to_show], use_container_width=True)
