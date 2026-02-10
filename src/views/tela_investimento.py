import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import yfinance as yf

# Importação dos serviços
from src.services.market_data_service import buscar_indicadores_economicos
from src.services.investment_service import (
    salvar_investimento,
    buscar_portfolio_real,
    buscar_evolucao_patrimonio,
    buscar_sugestoes_yahoo
)
# Importação do formatador de moeda
from src.utils.formatters import formatar_brl


# ==========================================
# 1. IDENTIDADE VISUAL (THEME AWARE)
# ==========================================
def inject_clario_css():
    """CSS adaptativo para Light/Dark mode."""
    st.markdown("""
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0" />
        <style>
            :root {
                --pink-clario: #E73469;
                --brand-green: #18cb96;
            }

            .material-symbols-rounded {
                font-family: 'Material Symbols Rounded';
                font-size: 20px; /* Tamanho padrão do ícone */
                vertical-align: sub; /* Alinhamento vertical melhorado */
            }

            /* 1. BOTÃO PRIMÁRIO (Novo Aporte) */
            button[kind="primary"] {
                background-color: var(--pink-clario) !important;
                color: white !important;
                border: none !important;
                border-radius: 10px !important;
                font-weight: 700 !important;
                height: 45px !important;
            }

            /* 2. BOTÃO SECUNDÁRIO (Ícone de Venda) */
            button[kind="secondary"] {
                background-color: transparent !important;
                color: var(--text-color) !important;
                border: 1px solid rgba(128, 128, 128, 0.2) !important;
                border-radius: 8px !important;
                width: 40px !important;
                height: 40px !important;
                opacity: 0.6;
            }
            button[kind="secondary"]:hover {
                border-color: var(--pink-clario) !important;
                color: var(--pink-clario) !important;
                background-color: rgba(231, 52, 105, 0.1) !important;
                opacity: 1;
            }

            /* KPI Cards Horizontais */
            .kpi-card {
                background-color: var(--secondary-background-color);
                padding: 15px 20px;
                border-radius: 12px;
                border-left: 4px solid var(--brand-green);
                min-height: 90px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                border: 1px solid rgba(128,128,128,0.1);
            }
            .card-label { 
                font-size: 11px; font-weight: 600; opacity: 0.7; 
                color: var(--text-color);
                text-transform: uppercase; margin-bottom: 6px;
                display: flex; align-items: center; gap: 6px;
            }
            .card-value { 
                font-size: 20px; font-weight: 800; color: var(--text-color); 
                white-space: nowrap;
            }

            /* Lista de Ativos */
            .inv-card {
                background-color: var(--secondary-background-color);
                border-radius: 12px; 
                padding: 15px;
                border-left: 5px solid #888;
                margin-bottom: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                border: 1px solid rgba(128,128,128,0.1);
            }

            .ativo-titulo { font-size:15px; font-weight:800; color: var(--text-color); }
            .ativo-sub { font-size:11px; opacity:0.6; color: var(--text-color); }

            .data-label { font-size: 10px; color: var(--text-color); opacity: 0.6; text-transform: uppercase; margin-bottom: 2px; }
            .data-value { font-size: 13px; font-weight: 600; color: var(--text-color); }

            /* Badge de Indicadores (Popup) */
            .badge-container {
                display: flex; gap: 15px; margin-bottom: 15px; 
                font-size: 0.85em; opacity: 0.9; 
                background: rgba(128,128,128,0.1); 
                padding: 10px 15px; border-radius: 8px;
                align-items: center; flex-wrap: wrap;
            }
            .badge-item { display: flex; align-items: center; gap: 5px; color: var(--text-color); }
        </style>
    """, unsafe_allow_html=True)


# ==========================================
# 2. DIALOGS (MODAIS)
# ==========================================

@st.dialog("Registrar Venda :material/sell:")
def mostrar_popup_venda(ativo, qtd_total, cat_id):
    """Modal de venda para registro de saída."""
    st.markdown(f"### Venda de **{ativo}**")
    st.info(f"Quantidade atual em carteira: {qtd_total}")

    with st.form("form_venda"):
        v_col1, v_col2 = st.columns(2)
        with v_col1:
            data_v = st.date_input("Data", value=date.today())
            qtd_v = st.number_input("Qtd Vendida", min_value=0.0, max_value=float(qtd_total), format="%.8f")
        with v_col2:
            valor_v = st.number_input("Valor Total Recebido (R$)", min_value=0.0)

        if st.form_submit_button("Confirmar Venda", type="primary", use_container_width=True):
            if qtd_v > 0 and valor_v > 0:
                # Preço unitário de venda
                preco_un = valor_v / qtd_v
                # Quantidade negativa indica saída
                qtd_negativa = qtd_v * -1

                ok, msg = salvar_investimento(
                    st.session_state.user.id, data_v, ativo, cat_id, preco_un, qtd_negativa,
                    taxa=None, indexador=None
                )
                if ok:
                    st.toast(f"Venda de {ativo} registrada!", icon=":material/check_circle:")
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Preencha quantidade e valor.")


@st.dialog("Novo Aporte :material/add_card:")
def mostrar_popup_aporte():
    """Formulário para registrar novo investimento com Taxa e Indexador separados."""
    st.markdown("### :material/payments: Registrar Investimento")

    # --- BARRA DE INDICADORES (Com Icons ao invés de Emojis) ---
    taxas = buscar_indicadores_economicos()

    st.markdown(f"""
    <div class="badge-container">
        <div class="badge-item">
            <span class="material-symbols-rounded" style="font-size:18px; color:#E73469;">account_balance</span>
            <b>Selic:</b> {taxas.get('SELIC', 0) * 100:.2f}%
        </div>
        <div class="badge-item">
            <span class="material-symbols-rounded" style="font-size:18px; color:#18CB96;">trending_up</span>
            <b>CDI:</b> {taxas.get('CDI', 0) * 100:.2f}%
        </div>
        <div class="badge-item">
            <span class="material-symbols-rounded" style="font-size:18px; color:#FFBD45;">shopping_cart</span>
            <b>IPCA (12m):</b> {taxas.get('IPCA', 0) * 100:.2f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Seleção de Tipo
    c_cat, c_data = st.columns(2)
    with c_cat:
        map_cats = {
            "Ações/FIIs/ETFs": 1,
            "Criptomoedas": 2,
            "Renda Fixa": 3
        }
        tipo_selecionado = st.selectbox("Categoria", list(map_cats.keys()))
        cat_id = map_cats[tipo_selecionado]

    with c_data:
        data_op = st.date_input("Data da Operação", value=date.today())

    st.divider()

    # 2. Dados do Ativo
    nome_ativo = ""
    taxa_val = None
    indexador_val = None

    # Variáveis de controle
    quantidade = 0.0
    valor_total = 0.0

    if cat_id == 3:  # Renda Fixa
        nome_ativo = st.text_input("Descrição do Título", placeholder="Ex: CDB Banco XP")

        col_rf = st.columns(3)
        with col_rf[0]:
            indexador_val = st.selectbox("Indexador", ["CDI", "IPCA", "PREFIXADO", "SELIC"])
        with col_rf[1]:
            taxa_val = st.number_input("Taxa (+% ou %)", min_value=0.0, step=0.1, format="%.2f")
        with col_rf[2]:
            venc = st.date_input("Vencimento", value=None)

        if venc:
            nome_ativo += f" - Venc: {venc.strftime('%d/%m/%Y')}"
    else:
        # Renda Variável
        termo_busca = st.text_input("Buscar Ativo (Nome ou Ticker)", placeholder="Ex: PETR4, BTC")
        if termo_busca:
            opcoes = buscar_sugestoes_yahoo(termo_busca)
            if opcoes:
                selecao = st.selectbox("Selecione o ativo correto:", opcoes)
                nome_ativo = selecao.split(" | ")[0].strip()
                st.caption(f":material/check_circle: Selecionado: **{nome_ativo}**")
            else:
                st.warning("Ativo não encontrado na base. Usando o texto digitado.")
                nome_ativo = termo_busca.upper()

    # 3. Valores Financeiros
    with st.form("form_final_aporte"):
        # Layout Condicional: Se for Renda Fixa, esconde quantidade
        if cat_id == 3:
            valor_total = st.number_input("Valor Investido (R$)", min_value=0.01, step=100.0)
            quantidade = 1.0  # Padrão interno para RF
            st.caption("Para Renda Fixa, a quantidade é registrada como 1 unidade do valor total.")
        else:
            c_val, c_qtd = st.columns(2)
            with c_val:
                valor_total = st.number_input("Valor Total Investido (R$)", min_value=0.01, step=100.0)
            with c_qtd:
                quantidade = st.number_input("Quantidade", min_value=0.00000001, format="%.8f", value=1.0)

        if st.form_submit_button("Confirmar Investimento", type="primary", use_container_width=True):
            if not nome_ativo:
                st.warning("O nome/ticker do ativo é obrigatório.")
            elif valor_total <= 0 or quantidade <= 0:
                st.warning("Valores inválidos.")
            else:
                # Se for RF, preco_unitario = valor_total (já que qtd=1)
                preco_unitario = valor_total / quantidade

                ok, msg = salvar_investimento(
                    st.session_state.user.id,
                    data_op,
                    nome_ativo,
                    cat_id,
                    preco_unitario,
                    quantidade,
                    taxa=taxa_val,
                    indexador=indexador_val
                )

                if ok:
                    st.toast("Investimento salvo com sucesso!", icon=":material/check_circle:")
                    st.rerun()
                else:
                    st.error(f"Erro ao salvar: {msg}")


# ==========================================
# 3. COMPONENTES VISUAIS (KPIs e LISTA)
# ==========================================

def render_metrics_topo(df):
    """Cards horizontais com formatação BRL e tema."""
    k1, k2, k3, k4 = st.columns(4)

    total = df['Total Atual BRL'].sum() if not df.empty else 0.0
    lucro = df['Lucro/Prejuízo BRL'].sum() if not df.empty else 0.0

    try:
        usd_ticker = yf.Ticker("USDBRL=X")
        hist = usd_ticker.history(period="1d")
        if not hist.empty:
            usd_val = hist['Close'].iloc[-1]
        else:
            usd_val = 5.80
    except:
        usd_val = 5.80

    # Helper para renderizar card HTML com Ícone
    def kpi_html(label, valor, cor, icon_name):
        return f"""
        <div class="kpi-card" style="border-left-color: {cor};">
            <div class="card-label">
                <span class="material-symbols-rounded" style="color:{cor};">{icon_name}</span>
                {label}
            </div>
            <div class="card-value" style="color:{cor if label == 'LUCRO/PREJUÍZO' else 'var(--text-color)'}">{valor}</div>
        </div>
        """

    with k1:
        st.markdown(kpi_html("PATRIMÔNIO", formatar_brl(total), "#E73469", "account_balance_wallet"),
                    unsafe_allow_html=True)

    with k2:
        cor = "#18CB96" if lucro >= 0 else "#E73469"
        icon = "trending_up" if lucro >= 0 else "trending_down"
        st.markdown(kpi_html("LUCRO/PREJUÍZO", formatar_brl(lucro), cor, icon), unsafe_allow_html=True)

    with k3:
        st.markdown(kpi_html("ATIVOS", str(len(df)), "#9C27B0", "grid_view"), unsafe_allow_html=True)

    with k4:
        st.markdown(kpi_html("DÓLAR", f"R$ {usd_val:.2f}", "#FFBD45", "currency_exchange"), unsafe_allow_html=True)


def render_lista_detalhada(df):
    """Lista detalhada com HTML sanitizado."""
    st.markdown("---")
    st.markdown("### :material/list_alt: Detalhamento da Carteira")

    st.markdown("""
    <style>
        .grid-row {
            display: grid;
            grid-template-columns: 2fr 1fr 1.5fr 1.5fr 1.5fr 1fr;
            gap: 10px;
            align-items: center;
        }
        /* Ajustes para telas menores se necessário */
    </style>
    """, unsafe_allow_html=True)

    for idx, row in df.iterrows():
        is_pos = row['Rentabilidade %'] >= 0
        cor = "#18CB96" if is_pos else "#E73469"
        sinal = "+" if is_pos else ""

        qtd = float(row['Quantidade'])
        custo = float(row['Custo Total BRL'])
        # Preço Médio: Se qtd > 0, calcula. Se for RF e qtd=1, mostra o custo.
        p_medio = custo / qtd if qtd > 0 else 0

        val_hoje_fmt = formatar_brl(row['Valor Hoje BRL'])
        patrimonio_fmt = formatar_brl(row['Total Atual BRL'])
        p_medio_fmt = formatar_brl(p_medio)
        rentab_fmt = f"{sinal}{row['Rentabilidade %']:.2f}%"

        c_card, c_btn = st.columns([10, 1], vertical_alignment="center")

        with c_card:
            card_html = f"""
            <div class="inv-card" style="border-left: 4px solid {cor};">
                <div class="grid-row">
                    <div style="line-height:1.2;">
                        <div class="ativo-titulo" style="color:{cor};">{row['Ativo']}</div>
                        <div class="ativo-sub">{row['Tipo']}</div>
                    </div>
                    <div><div class="data-label">Qtd</div><div class="data-value">{qtd:.4f}</div></div>
                    <div><div class="data-label">P. Médio</div><div class="data-value">{p_medio_fmt}</div></div>
                    <div><div class="data-label">Hoje</div><div class="data-value">{val_hoje_fmt}</div></div>
                    <div><div class="data-label">Total</div><div class="data-value">{patrimonio_fmt}</div></div>
                    <div style="text-align: right;">
                        <div class="data-label">Retorno</div>
                        <div style="color:{cor}; font-weight:bold;">{rentab_fmt}</div>
                    </div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

        with c_btn:
            if st.button(
                    label="",
                    icon=":material/sell:",
                    key=f"btn_venda_{idx}",
                    help=f"Vender {row['Ativo']}",
                    type="secondary"
            ):
                mostrar_popup_venda(row['Ativo'], qtd, row['id_categoria'])


def renderizar_investimentos():
    inject_clario_css()

    if "user" not in st.session_state:
        st.warning("Faça login.")
        return

    uid = st.session_state.user.id

    # Header
    col_h, col_b = st.columns([3, 1], vertical_alignment="center")
    with col_h:
        st.title("Investimentos")
    with col_b:
        if st.button("Novo Aporte", icon=":material/add_card:", use_container_width=True, type="primary"):
            mostrar_popup_aporte()

    # Busca Dados
    df_inv = buscar_portfolio_real(uid)

    if not df_inv.empty:
        render_metrics_topo(df_inv)

        st.markdown("### :material/timeline: Evolução do Patrimônio")
        df_tempo = buscar_evolucao_patrimonio(uid)

        if not df_tempo.empty:
            fig = px.area(df_tempo, x="Data", y="Patrimônio")
            fig.update_traces(line_color='#E73469', fillcolor='rgba(231, 52, 105, 0.1)')
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="gray"),
                height=300,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', tickprefix="R$ ")
            )
            st.plotly_chart(fig, use_container_width=True)

        render_lista_detalhada(df_inv)
    else:
        st.info("Você ainda não possui investimentos registrados.")