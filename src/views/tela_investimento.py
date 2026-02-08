import streamlit as st
import pandas as pd
import plotly.express as px
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
# 1. IDENTIDADE VISUAL (UX/UI DEFINITIVA)
# ==========================================

def inject_clario_css():
    """CSS para botões primários (Pink) e ícones de venda (Transparentes)."""
    st.markdown("""
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0" />
        <style>
            :root {
                --pink-clario: #E73469;
                --brand-green: #18cb96;
            }

            .material-symbols-rounded {
                font-family: 'Material Symbols Rounded';
                font-size: 22px;
                vertical-align: middle;
            }

            /* 1. BOTÃO PRINCIPAL (Novo Aporte) */
            button[data-testid="baseButton-primary"] {
                background-color: var(--pink-clario) !important;
                color: white !important;
                border: none !important;
                border-radius: 10px !important;
                font-weight: 700 !important;
                height: 45px !important;
            }

            /* 2. BOTÃO DE VENDA (Estilo Ícone Compacto de Transações) */
            div[data-testid="stHorizontalBlock"] button[data-testid="baseButton-secondary"] {
                background-color: rgba(255, 255, 255, 0.05) !important;
                color: #EEE !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 8px !important;
                width: 40px !important;
                height: 40px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }
            div[data-testid="stHorizontalBlock"] button[data-testid="baseButton-secondary"]:hover {
                border-color: var(--pink-clario) !important;
                color: var(--pink-clario) !important;
                background-color: rgba(231, 52, 105, 0.1) !important;
            }

            /* KPI Cards Horizontais */
            .kpi-card {
                background-color: var(--secondary-background-color);
                padding: 15px 20px;
                border-radius: 12px;
                border-left: 4px solid var(--brand-green);
                min-height: 85px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            .card-label { 
                font-size: 10px; font-weight: 600; opacity: 0.7; 
                text-transform: uppercase; margin-bottom: 4px;
                display: flex; align-items: center; gap: 8px;
            }
            .card-value { font-size: 20px; font-weight: 800; color: #FFF; }

            /* Lista de Ativos */
            .inv-card {
                background-color: var(--secondary-background-color);
                border-radius: 12px; padding: 18px 25px;
                border-left: 5px solid #444;
            }
            .data-label { font-size: 9px; color: #888; text-transform: uppercase; margin-bottom: 2px; }
            .data-value { font-size: 13px; font-weight: 700; color: #FFF; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DIALOGS (MODAIS)
# ==========================================

@st.dialog("Registrar Venda :material/sell:")
def mostrar_popup_venda(ativo, qtd_total, cat_id):
    """Modal de venda simplificado para registro de saída."""
    st.markdown(f"### Venda de **{ativo}**")
    with st.form("form_venda"):
        v_col1, v_col2 = st.columns(2)
        with v_col1:
            data_v = st.date_input("Data", value=date.today())
            qtd_v = st.number_input("Qtd", min_value=0.0, max_value=float(qtd_total), format="%.4f")
        with v_col2:
            valor_v = st.number_input("Valor Recebido (R$)", min_value=0.0)

        if st.form_submit_button("Confirmar Venda", type="primary", use_container_width=True):
            if qtd_v > 0:
                preco_un = valor_v / qtd_v
                ok, msg = salvar_investimento(st.session_state.user.id, data_v, ativo, cat_id, preco_un, -qtd_v)
                if ok:
                    st.toast(f"Venda de {ativo} registrada!", icon="✅")
                    st.rerun()

@st.dialog("Novo Aporte :material/add_card:")
def mostrar_popup_aporte():
    """Formulário híbrido completo para Renda Fixa e Variável."""
    st.markdown("### :material/payments: Registrar Investimento")
    st.info(":material/info: Informe o **VALOR TOTAL** da operação. Calcularemos o preço médio automaticamente.")

    c_cat, c_data = st.columns(2)
    with c_cat:
        tipo = st.selectbox("Categoria", ["Ações/FIIs", "Criptomoedas", "Renda Fixa (CDB, Tesouro, LCI)"])
    with c_data:
        data_op = st.date_input("Data da Operação", value=date.today())

    st.divider()
    nome_ativo, rentabilidade_str, quantidade = "", None, 1.0

    if "Renda Fixa" in tipo:
        nome_ativo = st.text_input("Descrição do Título", placeholder="Ex: CDB Banco XP 110% CDI")
        col_rf = st.columns(3)
        with col_rf[0]:
            idx = st.selectbox("Indexador", ["CDI", "IPCA", "SELIC", "Prefixado"])
        with col_rf[1]:
            tx = st.number_input("Taxa (%)", min_value=0.0, step=0.1)
        with col_rf[2]:
            st.date_input("Vencimento", value=None)
        rentabilidade_str = f"{tx}% {idx}"
        quantidade = 1.0
    else:
        query = st.text_input(":material/search: Pesquisar Ticker", placeholder="Ex: PETR4, SOL")
        sugestoes = pesquisar_ticker_yahoo(query) if len(query) >= 2 else []
        if sugestoes:
            selecao = st.selectbox("Selecione o ativo oficial:", sugestoes)
            nome_ativo = selecao.split(" | ")[0]
            st.caption(f":material/verified: Selecionado: **{nome_ativo}**")
        else:
            nome_ativo = query.upper().strip()

    with st.form("form_final_aporte"):
        st.write(f"Confirmando aporte em: **{nome_ativo if nome_ativo else '---'}**")
        v_col1, v_col2 = st.columns(2)
        with v_col1:
            valor_total = st.number_input("Valor Total Investido (R$)", min_value=0.01, step=50.0)
        with v_col2:
            if "Renda Fixa" not in tipo:
                quantidade = st.number_input("Quantidade Adquirida", min_value=0.00000001, format="%.8f", value=1.0)

        if st.form_submit_button("Confirmar Investimento", type="primary", use_container_width=True):
            if nome_ativo and valor_total > 0:
                cat_id = 1 if "Ações" in tipo else (2 if "Cripto" in tipo else 3)
                ok, msg = salvar_investimento(st.session_state.user.id, data_op, nome_ativo, cat_id,
                                              valor_total / quantidade, quantidade, rentabilidade_str)
                if ok: st.rerun()

# ==========================================
# 3. COMPONENTES VISUAIS (KPIs e LISTA)
# ==========================================

def render_metrics_topo(df):
    """Cards horizontais com cotação do Dólar dinâmica via yfinance."""
    k1, k2, k3, k4 = st.columns(4)
    total = df['Total Atual BRL'].sum() if not df.empty else 0.0
    lucro = df['Lucro/Prejuízo BRL'].sum() if not df.empty else 0.0

    # Busca dinâmica do Dólar
    try:
        usd_ticker = yf.Ticker("USDBRL=X")
        usd_val = usd_ticker.history(period="1d")['Close'].iloc[-1]
    except Exception:
        usd_val = 5.22 # Fallback caso a API falhe

    with k1: st.markdown(
        f'<div class="kpi-card"><div class="card-label"><span class="material-symbols-rounded">account_balance_wallet</span>PATRIMÔNIO</div><div class="card-value">R$ {total:,.2f}</div></div>',
        unsafe_allow_html=True)
    with k2:
        cor = "#18CB96" if lucro >= 0 else "#E73469"
        st.markdown(
            f'<div class="kpi-card" style="border-left-color:{cor}"><div class="card-label"><span class="material-symbols-rounded" style="color:{cor}">trending_up</span>LUCRO/PREJUÍZO</div><div class="card-value">R$ {lucro:,.2f}</div></div>',
            unsafe_allow_html=True)
    with k3: st.markdown(
        f'<div class="kpi-card" style="border-left-color:#18cb96"><div class="card-label"><span class="material-symbols-rounded" style="color:#18cb96">grid_view</span>ATIVOS</div><div class="card-value">{len(df)}</div></div>',
        unsafe_allow_html=True)
    with k4: st.markdown(
        f'<div class="kpi-card" style="border-left-color:#ff751f"><div class="card-label"><span class="material-symbols-rounded" style="color:#ff751f">currency_exchange</span>DÓLAR HOJE</div><div class="card-value">R$ {usd_val:.2f}</div></div>',
        unsafe_allow_html=True)

def render_lista_detalhada(df):
    """Lista com labels restaurados e botão ícone puro."""
    st.markdown("---")
    st.markdown("### :material/list_alt: Detalhamento da Carteira")
    for _, row in df.iterrows():
        is_pos = row['Rentabilidade %'] >= 0
        cor = "#18CB96" if is_pos else "#E73469"
        p_medio = row['Custo Total BRL'] / row['Quantidade']

        # Definição das colunas para evitar NameError
        card_col, btn_col = st.columns([10, 1], vertical_alignment="center")

        with card_col:
            html = f"""<div class="inv-card" style="border-left-color: {cor};">
<div style="display: grid; grid-template-columns: 1.5fr repeat(4, 1fr) 1fr; gap: 10px; align-items: center;">
<div><div style="font-size:16px; font-weight:800; color:var(--pink-clario);">{row['Ativo']}</div><div style="font-size:10px; opacity:0.6;">{row['Tipo']}</div></div>
<div><div class="data-label">Qtd</div><div class="data-value">{row['Quantidade']:.4f}</div></div>
<div><div class="data-label">P. Médio</div><div class="data-value">R$ {p_medio:,.2f}</div></div>
<div><div class="data-label">V. Hoje</div><div class="data-value">R$ {row['Valor Hoje BRL']:,.2f}</div></div>
<div><div class="data-label">Patrimônio</div><div class="data-value">R$ {row['Total Atual BRL']:,.2f}</div></div>
<div style="text-align: right;"><div class="data-label">Retorno</div><div style="color:{cor}; font-size:14px; font-weight:800;">{"+" if is_pos else ""}{row['Rentabilidade %']:.2f}%</div></div>
</div></div>"""
            st.markdown(html, unsafe_allow_html=True)

        with btn_col:
            if st.button(
                    label="",
                    key=f"baixa_venda_{row['Ativo']}_{row['id_categoria']}",
                    icon=":material/payments:",
                    help=f"Registrar venda/baixa de {row['Ativo']}",
                    use_container_width=True
            ):
                mostrar_popup_venda(row['Ativo'], row['Quantidade'], row['id_categoria'])

# ==========================================
# 4. ORQUESTRAÇÃO FINAL
# ==========================================

def renderizar_investimentos():
    inject_clario_css()
    if "user" not in st.session_state: return
    uid = st.session_state.user.id

    # Header
    col_h, col_b = st.columns([3.2, 1.8], vertical_alignment="bottom")
    with col_h: st.title("Investimentos")
    with col_b:
        if st.button("Novo Aporte", icon=":material/add_card:", use_container_width=True, type="primary"):
            mostrar_popup_aporte()

    df_inv = buscar_portfolio_real(uid)
    if not df_inv.empty:
        render_metrics_topo(df_inv)

        st.markdown("### :material/timeline: Evolução do Patrimônio")
        df_tempo = buscar_evolucao_patrimonio(uid)
        if not df_tempo.empty:
            fig = px.area(df_tempo, x="Data", y="Patrimônio", color_discrete_sequence=["#E73469"])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#FFF",
                              height=280, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

        render_lista_detalhada(df_inv)