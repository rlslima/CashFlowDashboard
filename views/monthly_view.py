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
    st.header("Monthly Cash Flow Analysis")
    
    if df.empty:
        st.warning("No data available with the current filters.")
        return
    
    # Get current year and available years for selection
    current_year = datetime.now().year
    available_years = sorted(df["Year"].unique().tolist())
    
    if not available_years:
        st.warning("No year data available.")
        return
    
    default_year = current_year if current_year in available_years else available_years[-1]
    
    # Year selection
    selected_year = st.selectbox("Select Year", available_years, index=available_years.index(default_year) if default_year in available_years else 0)
    
    # Filter data for selected year
    year_df = df[df["Year"] == selected_year].copy()
    
    if year_df.empty:
        st.warning(f"No data available for {selected_year}.")
        return
    
    # Prepare monthly aggregation
    monthly_data = []
    
    for month in range(1, 13):
        month_name = calendar.month_name[month]
        month_df = year_df[year_df["Month"] == month]
        
        income = month_df[month_df["Type"] == "Income"]["Value"].sum()
        expense = month_df[month_df["Type"] == "Expense"]["Value"].sum()
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
            name="Income",
            marker_color="green"
        ))
        
        fig.add_trace(go.Bar(
            x=monthly_df["Month Name"],
            y=monthly_df["Expense"],
            name="Expense",
            marker_color="red"
        ))
        
        fig.add_trace(go.Scatter(
            x=monthly_df["Month Name"],
            y=monthly_df["Net"],
            name="Net Cash Flow",
            mode="lines+markers",
            line=dict(color="blue", width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title=f"Monthly Cash Flow for {selected_year}",
            xaxis_title="Month",
            yaxis_title="Amount",
            legend_title="Category",
            barmode="group",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Summary metrics
        st.subheader("Annual Summary")
        
        total_income = monthly_df["Income"].sum()
        total_expense = monthly_df["Expense"].sum()
        total_net = total_income - total_expense
        
        st.metric("Total Income", f"${total_income:,.2f}")
        st.metric("Total Expenses", f"${total_expense:,.2f}")
        st.metric("Net Cash Flow", f"${total_net:,.2f}", delta=f"{(total_net/total_income*100 if total_income else 0):.1f}%" if total_income else None)
        
        # Monthly average metrics
        st.subheader("Monthly Averages")
        avg_income = total_income / 12
        avg_expense = total_expense / 12
        avg_net = total_net / 12
        
        st.metric("Average Income", f"${avg_income:,.2f}")
        st.metric("Average Expenses", f"${avg_expense:,.2f}")
        st.metric("Average Net Flow", f"${avg_net:,.2f}")
    
    # Monthly breakdown table
    st.subheader("Monthly Breakdown")
    
    # Format the dataframe for display
    display_df = monthly_df.copy()
    display_df["Income"] = display_df["Income"].apply(lambda x: f"${x:,.2f}")
    display_df["Expense"] = display_df["Expense"].apply(lambda x: f"${x:,.2f}")
    display_df["Net"] = display_df["Net"].apply(lambda x: f"${x:,.2f}")
    
    # Only show Month Name and financial columns
    st.dataframe(display_df[["Month Name", "Income", "Expense", "Net"]], use_container_width=True)
    
    # Top transactions for the year
    st.subheader("Top Transactions")
    
    tab1, tab2 = st.tabs(["Top Expenses", "Top Income"])
    
    with tab1:
        top_expenses = year_df[year_df["Type"] == "Expense"].sort_values("Value", ascending=False).head(10)
        if not top_expenses.empty:
            expense_fig = px.bar(
                top_expenses,
                x="Value",
                y="Supplier/Client",
                color="Month Name",
                orientation="h",
                title="Top 10 Expenses",
                labels={"Value": "Amount", "Supplier/Client": "Supplier/Vendor"}
            )
            st.plotly_chart(expense_fig, use_container_width=True)
        else:
            st.info("No expense data available.")
    
    with tab2:
        top_income = year_df[year_df["Type"] == "Income"].sort_values("Value", ascending=False).head(10)
        if not top_income.empty:
            income_fig = px.bar(
                top_income,
                x="Value",
                y="Supplier/Client",
                color="Month Name",
                orientation="h",
                title="Top 10 Income Sources",
                labels={"Value": "Amount", "Supplier/Client": "Client"}
            )
            st.plotly_chart(income_fig, use_container_width=True)
        else:
            st.info("No income data available.")
