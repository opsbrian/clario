import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
import yfinance as yf

# Importação dos serviços
from src.services.investment_service import (
    pesquisar_ticker_yahoo,
    salvar_investimento,
    buscar_portfolio_real,
    buscar_evolucao_patrimonio
)


# ==========================================
# 1. ESTILIZAÇÃO E IDENTIDADE VISUAL
# ==========================================

def inject_clario_css():
    """DNA Visual Clariô: Cores e Botões Personalizados."""
    st.markdown("""
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0" />
        <style>
            :root { 
                --pink-clario: #E73469; 
                --green-clario: #18CB96; 
                --dark-clario: #373643;
            }

            /* Botão Novo Aporte - Cor Clariô */
            div.stButton > button:first-child {
                background-color: var(--pink-clario) !important;
                color: white !important;
                border: none !important;
                border-radius: 10px;
                padding: 0.6rem 1.2rem;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            div.stButton > button:first-child:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(231, 52, 105, 0.4);
            }

            /* Estilo dos Cards de KPI */
            .kpi-card {
                background-color: var(--secondary-background-color);
                padding: 20px; border-radius: 15px; border-left: 5px solid var(--pink-clario); 
                margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            }
            .card-label { opacity: 0.7; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center; }
            .card-value { font-size: 24px; font-weight: 800; margin: 5px 0; color: #FFF; }

            /* Card de Ativo (Extrato) */
            .inv-card {
                background-color: var(--secondary-background-color);
                border-radius: 15px; padding: 22px; margin-bottom: 12px;
                border-left: 6px solid #ccc; transition: all 0.3s ease;
            }
            .inv-card:hover { border-left-color: var(--pink-clario); transform: translateX(5px); }
            .inv-symbol { font-size: 18px; font-weight: 800; color: var(--pink-clario); margin-bottom: 4px; }
            .data-label { font-size: 10px; color: #888; text-transform: uppercase; margin-bottom: 2px; }
            .data-value { font-size: 14px; font-weight: 600; }
        </style>
    """, unsafe_allow_html=True)


# ==========================================
# 2. FORMULÁRIO DE APORTE (MODAL)
# ==========================================

@st.dialog("Novo Aporte Clariô :material/add_card:")
def mostrar_popup_aporte():
    """Formulário dinâmico para Renda Fixa e Variável."""
    st.markdown("### Detalhes do Investimento")

    # Alerta solicitado sobre Valor Total
    st.warning(
        "⚠️ **Aviso de Preenchimento:** No campo 'Valor Total', insira o montante acumulado da compra (ex: R$ 2.500,00) e não o preço de uma única cota.")

    with st.form("form_novo_aporte", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            categoria_nome = st.selectbox(
                "Categoria",
                ["Ações/FIIs", "Criptomoedas", "Renda Fixa (CDB/Tesouro)"]
            )
            data_op = st.date_input("Data da Operação", value=date.today())

        with col2:
            if "Renda Fixa" in categoria_nome:
                ativo = st.text_input("Nome do Título", placeholder="Ex: CDB Prefixado 12%")
            else:
                query = st.text_input("Ticker ou Nome", placeholder="Ex: PETR4, SOL")
                sugestoes = pesquisar_ticker_yahoo(query) if len(query) > 1 else []
                ativo_selecionado = st.selectbox("Selecione o Ativo", sugestoes) if sugestoes else query
                ativo = ativo_selecionado.split(" | ")[0] if "|" in ativo_selecionado else ativo_selecionado

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            valor_total = st.number_input("Valor Total Investido (R$)", min_value=0.01, step=100.0)

        with c2:
            # Lógica para tratar Qtd em Renda Fixa como 1 unidade total
            if "Renda Fixa" in categoria_nome:
                quantidade = 1.0
                st.info("Para Renda Fixa, consideramos o aporte como 1 unidade total.")
            else:
                quantidade = st.number_input("Quantidade de Cotas", min_value=0.00000001, step=0.1)
                if quantidade > 0:
                    st.caption(f"Cálculo: R$ {(valor_total / quantidade):,.2f} por unidade")

        submit = st.form_submit_button("Confirmar Registro", use_container_width=True, type="primary")

        if submit:
            cat_id = 1 if "Ações" in categoria_nome else (2 if "Cripto" in categoria_nome else 3)
            # Salva o preço unitário calculado para manter compatibilidade com o histórico
            preco_unitario = valor_total / quantidade

            sucesso, msg = salvar_investimento(
                st.session_state.user.id, data_op, ativo, cat_id, preco_unitario, quantidade
            )

            if sucesso:
                st.success("Aporte registrado!")
                st.rerun()
            else:
                st.error(msg)


# ==========================================
# 3. COMPONENTES DE DASHBOARD
# ==========================================

def render_metrics_topo(df):
    """Cards superiores com a cotação real do Dólar."""
    k1, k2, k3, k4 = st.columns(4)

    total_patrimonio = df['Total Atual BRL'].sum() if not df.empty else 0.0
    lucro_geral = df['Lucro/Prejuízo BRL'].sum() if not df.empty else 0.0

    try:
        usd_data = yf.Ticker("USDBRL=X").history(period="1d")
        preco_dolar = usd_data['Close'].iloc[-1]
    except:
        preco_dolar = 5.20

    with k1:
        st.markdown(
            f"""<div class="kpi-card"><div class="card-label"><span class="material-symbols-rounded" style="color:var(--pink-clario); margin-right:8px;">account_balance_wallet</span>PATRIMÔNIO</div><div class="card-value">R$ {total_patrimonio:,.2f}</div><div style="color:var(--pink-clario); font-size:12px; font-weight:700;">Total BRL</div></div>""",
            unsafe_allow_html=True)
    with k2:
        cor_lucro = "var(--green-clario)" if lucro_geral >= 0 else "var(--pink-clario)"
        st.markdown(
            f"""<div class="kpi-card" style="border-left-color:{cor_lucro};"><div class="card-label"><span class="material-symbols-rounded" style="color:{cor_lucro}; margin-right:8px;">trending_up</span>LUCRO/PREJUÍZO</div><div class="card-value">R$ {lucro_geral:,.2f}</div><div style="color:{cor_lucro}; font-size:12px; font-weight:700;">Consolidado</div></div>""",
            unsafe_allow_html=True)
    with k3:
        st.markdown(
            f"""<div class="kpi-card" style="border-left-color:#32BCAD;"><div class="card-label"><span class="material-symbols-rounded" style="color:#32BCAD; margin-right:8px;">stars</span>ATIVOS</div><div class="card-value">{len(df)}</div><div style="color:#32BCAD; font-size:12px; font-weight:700;">Diversificação</div></div>""",
            unsafe_allow_html=True)
    with k4:
        st.markdown(
            f"""<div class="kpi-card" style="border-left-color:#888;"><div class="card-label"><span class="material-symbols-rounded" style="color:#888; margin-right:8px;">currency_exchange</span>DÓLAR HOJE</div><div class="card-value">R$ {preco_dolar:.2f}</div><div style="color:#888; font-size:12px; font-weight:700;">API Yahoo</div></div>""",
            unsafe_allow_html=True)


def render_grafico_tempo(user_id):
    """Eixo X: Tempo | Eixo Y: Patrimônio BRL."""
    st.markdown("### :material/timeline: Evolução do Patrimônio")
    df_tempo = buscar_evolucao_patrimonio(user_id)

    if df_tempo.empty:
        st.info("Aguardando mais dados históricos para gerar o gráfico.")
        return

    fig = px.area(df_tempo, x="Data", y="Patrimônio", color_discrete_sequence=["#E73469"])
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#FFF",
        hovermode="x unified", margin=dict(l=0, r=0, t=10, b=0), height=350,
        xaxis=dict(showgrid=False, title=""),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Total (R$)")
    )
    fig.update_traces(line=dict(width=3), fillcolor="rgba(231, 52, 105, 0.1)")
    st.plotly_chart(fig, use_container_width=True)


def render_lista_cards_investimentos(df):
    """Extrato rico em informações."""
    st.markdown("---")
    st.markdown('### :material/list_alt: Portfólio Detalhado', unsafe_allow_html=True)

    for _, row in df.iterrows():
        is_pos = row['Rentabilidade %'] >= 0
        cor = "var(--green-clario)" if is_pos else "var(--pink-clario)"
        preco_medio = row['Custo Total BRL'] / row['Quantidade']

        st.markdown(f"""
            <div class="inv-card" style="border-left-color: {cor};">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 15px;">
                    <div style="flex: 1.5; min-width: 140px;">
                        <div class="inv-symbol">{row['Ativo']}</div>
                        <div style="font-size:11px; opacity:0.6;">{row['Tipo']}</div>
                    </div>
                    <div style="flex: 1;"><div class="data-label">Qtd</div><div class="data-value">{row['Quantidade']}</div></div>
                    <div style="flex: 1;"><div class="data-label">Preço Médio</div><div class="data-value">R$ {preco_medio:,.2f}</div></div>
                    <div style="flex: 1;"><div class="data-label">Cotação</div><div class="data-value">R$ {row['Valor Hoje BRL']:,.2f}</div></div>
                    <div style="flex: 1;"><div class="data-label">Patrimônio</div><div class="data-value">R$ {row['Total Atual BRL']:,.2f}</div></div>
                    <div style="flex: 1; text-align: right;">
                        <div style="color:{cor}; font-size:16px; font-weight:800;">{"+" if is_pos else ""}{row['Rentabilidade %']:.2f}%</div>
                        <div style="color:{cor}; font-size:11px; opacity:0.8;">R$ {row['Lucro/Prejuízo BRL']:,.2f}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)


# ==========================================
# 4. ORQUESTRAÇÃO PRINCIPAL
# ==========================================

def renderizar_investimentos():
    inject_clario_css()
    if "user" not in st.session_state:
        st.error("Por favor, realize o login.")
        return

    user_id = st.session_state.user.id

    # Header
    col_t, col_b = st.columns([3, 1], vertical_alignment="bottom")
    with col_t:
        st.markdown("## Meus Investimentos")
    with col_b:
        if st.button("Novo Aporte", icon=":material/add_card:", use_container_width=True):
            mostrar_popup_aporte()

    # Dados
    with st.spinner("Sincronizando mercado..."):
        df_inv = buscar_portfolio_real(user_id)

    if df_inv.empty:
        st.info("Sua carteira está vazia. Adicione um ativo para começar.")
        return

    render_metrics_topo(df_inv)
    render_grafico_tempo(user_id)
    render_lista_cards_investimentos(df_inv)