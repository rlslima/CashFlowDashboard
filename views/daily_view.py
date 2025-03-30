import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from datetime import date as date_class
import calendar
import io
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
    
    # Determinar a data atual (ou a mais próxima com dados)
    today = date_class.today()
    # Se a data atual é maior que a data máxima nos dados, usar a data máxima
    if today > max_date.date():
        current_date = max_date.date()
    # Se a data atual é menor que a data mínima nos dados, usar a data mínima
    elif today < min_date.date():
        current_date = min_date.date()
    else:
        # Encontrar a data mais próxima da atual que tenha dados
        dates = sorted(df["Date"].dt.date.unique())
        current_date = min(dates, key=lambda x: abs((x - today).days))
    
    # Encontrar uma data futura dentro dos próximos 10 dias que tenha dados
    # Se não houver, usar a data máxima disponível
    future_dates = [d for d in df["Date"].dt.date.unique() if d > current_date]
    if future_dates and len(future_dates) > 0:
        # Pegar no máximo 10 dias à frente, se disponível
        end_date_default = min(future_dates[min(9, len(future_dates)-1)], max_date.date())
    else:
        end_date_default = max_date.date()
    
    # Opções de seleção de período
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Data Inicial",
            value=current_date,
            min_value=min_date.date(),
            max_value=max_date.date()
        )
    
    with col2:
        end_date = st.date_input(
            "Data Final",
            value=end_date_default,
            min_value=min_date.date(),
            max_value=max_date.date()
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
    background_header_receita = "#D7FFE5"  # Verde claro
    background_header_despesa = "#FFE5E5"  # Vermelho claro
    background_total = "#FFFFCC"  # Amarelo claro
    
    # Obter todas as Obras únicas
    obras = sorted(filtered_df["Work"].unique())
    
    # Interface para seleção de como agrupar os dados
    view_option = st.radio(
        "Tipo de visualização:",
        options=["Tabela de Fluxo de Caixa", "Análise por Dia", "Análise por Obra"],
        horizontal=True
    )
    
    # Criar visualização em formato de tabela (semelhante à imagem)
    if view_option == "Tabela de Fluxo de Caixa":
        # Determine datas únicas no intervalo selecionado
        unique_dates = sorted(filtered_df["Date"].dt.date.unique())
        
        if len(unique_dates) == 0:
            st.warning("Não há dados para exibir no período selecionado.")
            return
            
        # Criar dataframe para a tabela de fluxo de caixa
        st.markdown("### Fluxo de Caixa Diário")
        
        # Gerar a tabela de fluxo de caixa no estilo da imagem
        with st.container():
            # Renderizar a tabela como HTML para maior controle visual
            html_table = """
            <style>
            .cash-flow-table {
                width: 100%;
                border-collapse: collapse;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            .cash-flow-table th, .cash-flow-table td {
                border: 1px solid #ddd;
                padding: 6px;
                text-align: center;
            }
            .table-header {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            .income-header {
                background-color: """ + background_header_receita + """;
                font-weight: bold;
            }
            .expense-header {
                background-color: """ + background_header_despesa + """;
                font-weight: bold;
            }
            .total-row {
                background-color: """ + background_total + """;
                font-weight: bold;
            }
            .balance-row {
                background-color: """ + background_total + """;
                font-weight: bold;
                color: #009900;
            }
            .negative-balance {
                color: #cc0000;
            }
            </style>
            
            <table class="cash-flow-table">
                <tr class="table-header">
                    <th>OBRA</th>
            """
            
            # Adicionar cabeçalhos de data
            for date in unique_dates:
                date_str = date.strftime("%d/%m/%Y")
                html_table += f"<th>{date_str}</th>"
            
            html_table += """
                </tr>
                <tr class="income-header">
                    <td colspan="{}" style="text-align:left;">RECEITAS</td>
                </tr>
            """.format(len(unique_dates) + 1)
            
            # Dados de receita por obra
            income_by_date_work = income_df.groupby([income_df["Date"].dt.date, "Work"])["Value"].sum().unstack(fill_value=0)
            
            # Total de receitas por data
            income_totals_by_date = income_df.groupby(income_df["Date"].dt.date)["Value"].sum()
            
            # Verificar quais obras têm pelo menos um valor não-zero para receitas
            obras_com_receita = []
            for obra in obras:
                has_value = False
                for date in unique_dates:
                    if date in income_by_date_work.index and obra in income_by_date_work.columns:
                        if income_by_date_work.loc[date, obra] > 0:
                            has_value = True
                            break
                if has_value:
                    obras_com_receita.append(obra)
            
            # Linhas para cada obra com receita (removendo linhas totalmente zeradas)
            for obra in obras_com_receita:
                html_table += f"<tr><td style='text-align:left;'>{obra}</td>"
                
                for date in unique_dates:
                    value = 0
                    if date in income_by_date_work.index and obra in income_by_date_work.columns:
                        value = income_by_date_work.loc[date, obra]
                    
                    value_str = format_currency_brl(value) if value > 0 else "R$ 0,00"
                    html_table += f"<td>{value_str}</td>"
                
                html_table += "</tr>"
            
            # Linha de total de receitas
            html_table += "<tr class='total-row'><td style='text-align:left;'>TOTAL RECEITA</td>"
            
            for date in unique_dates:
                total_value = income_totals_by_date.get(date, 0)
                total_str = format_currency_brl(total_value) if total_value > 0 else "R$ 0,00"
                html_table += f"<td>{total_str}</td>"
            
            html_table += "</tr>"
            
            # Cabeçalho das despesas
            html_table += """
                <tr class="expense-header">
                    <td colspan="{}" style="text-align:left;">DESPESAS</td>
                </tr>
            """.format(len(unique_dates) + 1)
            
            # Dados de despesa por obra
            expense_by_date_work = expense_df.groupby([expense_df["Date"].dt.date, "Work"])["Value"].sum().unstack(fill_value=0)
            
            # Total de despesas por data
            expense_totals_by_date = expense_df.groupby(expense_df["Date"].dt.date)["Value"].sum()
            
            # Verificar quais obras têm pelo menos um valor não-zero para despesas
            obras_com_despesa = []
            for obra in obras:
                has_value = False
                for date in unique_dates:
                    if date in expense_by_date_work.index and obra in expense_by_date_work.columns:
                        if expense_by_date_work.loc[date, obra] > 0:
                            has_value = True
                            break
                if has_value:
                    obras_com_despesa.append(obra)
            
            # Linhas para cada obra com despesa (removendo linhas totalmente zeradas)
            for obra in obras_com_despesa:
                html_table += f"<tr><td style='text-align:left;'>{obra}</td>"
                
                for date in unique_dates:
                    value = 0
                    if date in expense_by_date_work.index and obra in expense_by_date_work.columns:
                        value = expense_by_date_work.loc[date, obra]
                    
                    value_str = format_currency_brl(value) if value > 0 else "R$ 0,00"
                    html_table += f"<td>{value_str}</td>"
                
                html_table += "</tr>"
            
            # Linha de total de despesas
            html_table += "<tr class='total-row'><td style='text-align:left;'>TOTAL DESPESA</td>"
            
            for date in unique_dates:
                total_value = expense_totals_by_date.get(date, 0)
                total_str = format_currency_brl(total_value) if total_value > 0 else "R$ 0,00"
                html_table += f"<td>{total_str}</td>"
            
            html_table += "</tr>"
            
            # Linha de saldo diário
            html_table += "<tr class='balance-row'><td style='text-align:left;'>SALDO</td>"
            
            for date in unique_dates:
                income_value = income_totals_by_date.get(date, 0)
                expense_value = expense_totals_by_date.get(date, 0)
                balance = income_value - expense_value
                
                # Aplicar classe CSS para saldo negativo
                class_style = " class='negative-balance'" if balance < 0 else ""
                balance_str = format_currency_brl(balance)
                html_table += f"<td{class_style}>{balance_str}</td>"
            
            html_table += "</tr></table>"
            
            # Exibir a tabela HTML
            st.markdown(html_table, unsafe_allow_html=True)
            
            # Adicionar função para gerar PDF
            def generate_pdf():
                # Configurar documento PDF
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
                elements = []
                
                # Estilos
                styles = getSampleStyleSheet()
                style_title = ParagraphStyle(
                    name='TitleStyle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    alignment=1,  # Centralizado
                    spaceAfter=12
                )
                style_header = ParagraphStyle(
                    name='HeaderStyle',
                    parent=styles['Heading2'],
                    fontSize=12,
                    alignment=1,  # Centralizado
                    spaceAfter=10
                )
                
                # Título e Cabeçalho
                title = Paragraph(f"Combrasen Group - Fluxo de Caixa Diário", style_title)
                subtitle = Paragraph(f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}", style_header)
                elements.append(title)
                elements.append(subtitle)
                elements.append(Spacer(1, 10))
                
                # Dados para a tabela
                table_data = []
                
                # Cabeçalho da tabela
                header_row = ["OBRA"]
                for date in unique_dates:
                    header_row.append(date.strftime("%d/%m/%Y"))
                table_data.append(header_row)
                
                # Receitas
                table_data.append(["RECEITAS"] + ["" for _ in range(len(unique_dates))])
                
                # Dados de receitas
                for obra in obras_com_receita:
                    row = [obra]
                    for date in unique_dates:
                        value = 0
                        if date in income_by_date_work.index and obra in income_by_date_work.columns:
                            value = income_by_date_work.loc[date, obra]
                        row.append(format_currency_brl(value) if value > 0 else "R$ 0,00")
                    table_data.append(row)
                
                # Total de receitas
                row_total_income = ["TOTAL RECEITA"]
                for date in unique_dates:
                    total_value = income_totals_by_date.get(date, 0)
                    row_total_income.append(format_currency_brl(total_value) if total_value > 0 else "R$ 0,00")
                table_data.append(row_total_income)
                
                # Despesas
                table_data.append(["DESPESAS"] + ["" for _ in range(len(unique_dates))])
                
                # Dados de despesas
                for obra in obras_com_despesa:
                    row = [obra]
                    for date in unique_dates:
                        value = 0
                        if date in expense_by_date_work.index and obra in expense_by_date_work.columns:
                            value = expense_by_date_work.loc[date, obra]
                        row.append(format_currency_brl(value) if value > 0 else "R$ 0,00")
                    table_data.append(row)
                
                # Total de despesas
                row_total_expense = ["TOTAL DESPESA"]
                for date in unique_dates:
                    total_value = expense_totals_by_date.get(date, 0)
                    row_total_expense.append(format_currency_brl(total_value) if total_value > 0 else "R$ 0,00")
                table_data.append(row_total_expense)
                
                # Saldo
                row_balance = ["SALDO"]
                for date in unique_dates:
                    income_value = income_totals_by_date.get(date, 0)
                    expense_value = expense_totals_by_date.get(date, 0)
                    balance = income_value - expense_value
                    row_balance.append(format_currency_brl(balance))
                table_data.append(row_balance)
                
                # Criar tabela para PDF
                # Ajustar tamanho da coluna automaticamente
                col_widths = [120] + [90] * len(unique_dates)  # Primeira coluna maior para o nome da obra
                
                # Criar a tabela
                table = Table(table_data, colWidths=col_widths)
                
                # Estilos da tabela
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Cabeçalho
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, 1), colors.lightgreen),  # Seção de receitas
                    ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                    ('ALIGN', (0, 1), (0, 1), 'LEFT'),
                    ('SPAN', (0, 1), (-1, 1)),  # Mesclar células do cabeçalho de receitas
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ])
                
                # Índice da linha de total de receitas
                total_income_row = 2 + len(obras_com_receita)
                # Índice da linha de cabeçalho de despesas
                expense_header_row = total_income_row + 1
                # Índice da linha de total de despesas
                total_expense_row = expense_header_row + 1 + len(obras_com_despesa)
                # Índice da linha de saldo
                balance_row = total_expense_row + 1
                
                # Estilo para total de receitas
                style.add('BACKGROUND', (0, total_income_row), (-1, total_income_row), colors.lightyellow)
                style.add('FONTNAME', (0, total_income_row), (-1, total_income_row), 'Helvetica-Bold')
                
                # Estilo para cabeçalho de despesas
                style.add('BACKGROUND', (0, expense_header_row), (-1, expense_header_row), colors.lightcoral)
                style.add('FONTNAME', (0, expense_header_row), (-1, expense_header_row), 'Helvetica-Bold')
                style.add('ALIGN', (0, expense_header_row), (0, expense_header_row), 'LEFT')
                style.add('SPAN', (0, expense_header_row), (-1, expense_header_row))  # Mesclar células
                
                # Estilo para total de despesas
                style.add('BACKGROUND', (0, total_expense_row), (-1, total_expense_row), colors.lightyellow)
                style.add('FONTNAME', (0, total_expense_row), (-1, total_expense_row), 'Helvetica-Bold')
                
                # Estilo para saldo
                style.add('BACKGROUND', (0, balance_row), (-1, balance_row), colors.lightyellow)
                style.add('FONTNAME', (0, balance_row), (-1, balance_row), 'Helvetica-Bold')
                
                # Aplicar estilos
                table.setStyle(style)
                elements.append(table)
                
                # Construir o documento
                doc.build(elements)
                
                buffer.seek(0)
                return buffer.getvalue()
            
            # Botões para download
            col1, col2 = st.columns(2)
            
            with col1:
                # Botão para baixar como PDF
                st.download_button(
                    label="Baixar como PDF",
                    data=generate_pdf(),
                    file_name=f"fluxo_caixa_{start_date.strftime('%d%m%Y')}_a_{end_date.strftime('%d%m%Y')}.pdf",
                    mime="application/pdf"
                )
            
            with col2:
                # Adicionar botão para baixar como Excel (a ser implementado)
                st.download_button(
                    label="Baixar como Excel",
                    data="Funcionalidade em desenvolvimento",
                    file_name="fluxo_caixa_diario.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    disabled=True  # Temporariamente desativado
                )
            
    # Criar tabelas e gráficos com base na seleção
    elif view_option == "Análise por Dia":
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