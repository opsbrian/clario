import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import time

# Importação consolidada e corrigida
from src.services.investment_service import (
    pesquisar_ticker_yahoo,
    salvar_investimento,
    buscar_portfolio_real
)


def inject_clario_css():
    st.markdown("""
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0" />
        <style>
            :root { --pink-clario: #E73469; --green-clario: #18CB96; }
            .kpi-card {
                background-color: var(--secondary-background-color);
                padding: 20px; border-radius: 15px; border-left: 5px solid var(--pink-clario);
                margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .card-label { opacity: 0.7; font-size: 11px; font-weight: 600; text-transform: uppercase; display: flex; align-items: center; }
            .card-value { font-size: 22px; font-weight: 800; margin: 5px 0; color: #FFF; }
            .inv-card {
                background-color: var(--secondary-background-color);
                border-radius: 12px; padding: 18px; margin-bottom: 10px;
                border-left: 6px solid #ccc; transition: 0.2s;
            }
            .inv-card:hover { border-left-width: 10px; background: rgba(255,255,255,0.02); }
            .profit-pos { color: var(--green-clario); font-weight: 700; }
            .profit-neg { color: var(--pink-clario); font-weight: 700; }
        </style>
    """, unsafe_allow_html=True)


def render_kpi_card(icon, label, value, delta, color="#e73469"):
    st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {color};">
            <div class="card-label">
                <span class="material-symbols-rounded" style="color:{color}; font-size:18px; margin-right:8px;">{icon}</span>{label}
            </div>
            <div class="card-value">{value}</div>
            <div style="color:{color}; font-size:12px; font-weight:700;">{delta}</div>
        </div>
    """, unsafe_allow_html=True)


@st.dialog("Nova Operação Clariô :material/rocket_launch:")
def mostrar_popup_aporte():
    busca = st.text_input(":material/search: Pesquisar Ativo", placeholder="Ex: Petrobras, Bitcoin...")
    ticker_sel = ""
    sugestoes = pesquisar_ticker_yahoo(busca)

    if sugestoes:
        escolha = st.selectbox("Selecione:", sugestoes, label_visibility="collapsed")
        ticker_sel = escolha.split(" | ")[0]
        st.caption(f":material/check_circle: Ativo: **{ticker_sel}**")

    with st.form("form_aporte", clear_on_submit=True):
        c1, c2 = st.columns(2)
        categoria = c1.selectbox(":material/category: Categoria", ["Renda Variável", "Criptomoeda", "Renda Fixa"])
        moeda = "USD" if categoria == "Criptomoeda" else "BRL"

        f1, f2, f3 = st.columns(3)
        ativo_final = f1.text_input(":material/label: Ticker", value=ticker_sel)
        data_op = f2.date_input(":material/calendar_month: Data", value=date.today())
        instituicao = f3.text_input(":material/account_balance: Banco", placeholder="Binance, B3")

        v1, v2, v3 = st.columns(3)
        prec = 8 if categoria == "Criptomoeda" else 2
        qtd = v1.number_input(":material/pin: Quantidade", min_value=0.0, step=0.01, format=f"%.{prec}f")
        preco = v2.number_input(f":material/payments: Preço ({moeda})", min_value=0.0)

        if st.form_submit_button("Registrar", icon=":material/task_alt:", use_container_width=True, type="primary"):
            if not ativo_final or qtd <= 0:
                st.error("Dados inválidos.")
            else:
                id_cat = {"Renda Variável": 1, "Criptomoeda": 2, "Renda Fixa": 3}[categoria]
                ok, msg = salvar_investimento(st.session_state.user.id, data_op, ativo_final, id_cat, preco, qtd)
                if ok: st.toast(msg); st.rerun()


def renderizar_investimentos():
    inject_clario_css()
    if "user" not in st.session_state: return st.error("Sessão expirada.")

    c_title, c_btn = st.columns([3, 1], vertical_alignment="bottom")
    with c_title:
        st.markdown("## Meus Investimentos")
    with c_btn:
        if st.button("Novo Aporte", icon=":material/add_card:", use_container_width=True, type="primary"):
            mostrar_popup_aporte()

    with st.spinner("Atualizando cotações BRL..."):
        df = buscar_portfolio_real(st.session_state.user.id)

    if df.empty: return st.info("Seu portfólio está vazio.")

    # KPIs e Gráficos
    render_metrics_topo(df)

    col_g1, col_g2 = st.columns([2, 1])
    with col_g1:
        st.plotly_chart(px.bar(df, x='Ativo', y='Lucro/Prejuízo BRL', color_discrete_sequence=['#E73469']),
                        use_container_width=True)
    with col_g2:
        st.plotly_chart(px.pie(df, values='Total Atual BRL', names='Tipo', hole=0.5), use_container_width=True)

    # Detalhamento
    st.markdown("---")
    for _, row in df.iterrows():
        cor = "#18CB96" if row['Rentabilidade %'] >= 0 else "#E73469"
        st.markdown(f"""
            <div class="inv-card" style="border-left-color: {cor};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 2;"><div class="inv-symbol">{row['Ativo']}</div><div style="font-size:11px; opacity:0.6;">{row['Tipo']}</div></div>
                    <div style="flex: 1; text-align: center;"><div class="card-label">Qtd</div><div style="font-weight:700;">{row['Quantidade']}</div></div>
                    <div style="flex: 1.5; text-align: center;"><div class="card-label">Valor Hoje</div><div style="font-weight:700;">R$ {row['Valor Hoje BRL']:,.2f}</div></div>
                    <div style="flex: 1; text-align: right;">
                        <div style="color:{cor}; font-size:16px; font-weight:700;">{row['Rentabilidade %']:.2f}%</div>
                        <div style="color:{cor}; font-size:11px; opacity:0.8;">R$ {row['Lucro/Prejuízo BRL']:,.2f}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)


def render_metrics_topo(df):
    k1, k2, k3, k4 = st.columns(4)
    total = df['Total Atual BRL'].sum()
    lucro = df['Lucro/Prejuízo BRL'].sum()
    with k1: render_kpi_card("account_balance_wallet", "Patrimônio", f"R$ {total:,.2f}", "Total BRL")
    with k2: render_kpi_card("show_chart", "Lucro/Prejuízo", f"R$ {lucro:,.2f}", "Geral",
                             color="#18CB96" if lucro >= 0 else "#E73469")
    with k3: render_kpi_card("stars", "Ativos", f"{len(df)}", "Diversificação", color="#32BCAD")
    with k4: render_kpi_card("currency_exchange", "Dólar Hoje", "Sincronizado", "API Yahoo", color="#888")