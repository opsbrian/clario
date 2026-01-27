import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta


# ==========================================
# 1. ESTILIZAÇÃO E IDENTIDADE VISUAL
# ==========================================

def inject_clario_css():
    """DNA Visual Clariô: Cores, Cards e Botões."""
    st.markdown("""
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
        <style>
            :root { 
                --pink-clario: #E73469; 
                --green-clario: #18CB96; 
                --dark-clario: #373643;
            }

            /* Ícones */
            .pink-icon { color: var(--pink-clario); font-family: 'Material Symbols Outlined'; font-size: 24px; vertical-align: middle; margin-right: 8px; }
            .header-icon { font-size: 28px; vertical-align: middle; }

            /* Botão Primário (Rosa Clariô) */
            div.stButton > button[kind="primary"] {
                background-color: var(--pink-clario);
                border-color: var(--pink-clario);
                color: white;
                border-radius: 10px;
                font-weight: 600;
            }

            /* KPI Cards */
            .kpi-card {
                background-color: var(--secondary-background-color);
                padding: 20px; border-radius: 15px; border-left: 5px solid var(--pink-clario); 
                box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 15px;
            }
            .card-label { opacity: 0.7; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
            .card-value { font-size: 24px; font-weight: 800; margin: 5px 0; }

            /* Investment Cards (Feed Style) */
            .inv-card {
                background-color: var(--secondary-background-color);
                border-radius: 15px; padding: 22px; margin-bottom: 12px;
                border-left: 6px solid #ccc; transition: all 0.3s ease;
            }
            .inv-card:hover { 
                transform: translateY(-3px); 
                box-shadow: 0 8px 25px rgba(0,0,0,0.12);
                border-left-width: 10px;
            }
            .inv-symbol { font-size: 19px; font-weight: 800; color: var(--pink-clario); }
            .profit-pos { color: var(--green-clario); font-weight: 700; }
            .profit-neg { color: var(--pink-clario); font-weight: 700; }

            /* Modal/Dialog Header */
            div[data-testid="stDialog"] div[role="dialog"] {
                border-radius: 20px;
                border-top: 10px solid var(--pink-clario);
            }
        </style>
    """, unsafe_allow_html=True)


def render_kpi_card(icon, label, value, delta, is_positive=True, color="#e73469"):
    """Cards métricos do topo."""
    delta_prefix = "▲" if is_positive else "▼"
    st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {color};">
            <div class="card-label">
                <span class="pink-icon" style="color:{color}; font-size:20px;">{icon}</span>{label}
            </div>
            <div class="card-value">{value}</div>
            <div style="color:{color}; font-size:13px; font-weight:700;">{delta_prefix} {delta}</div>
        </div>
    """, unsafe_allow_html=True)


# ==========================================
# 2. POPUP: FORMULÁRIO DINÂMICO
# ==========================================

@st.dialog("Nova Operação Clariô 🚀")
def mostrar_popup_aporte():
    """Popup com lógica condicional por categoria."""
    st.markdown("Registre seu aporte com precisão.")

    with st.form("form_aporte_modal", clear_on_submit=True):
        col_cat, col_tipo = st.columns(2)
        with col_cat:
            categoria = st.selectbox("Categoria", ["Renda Variável", "Criptomoeda", "Renda Fixa"])
        with col_tipo:
            operacao = st.radio("Operação", ["Compra", "Venda"], horizontal=True)

        st.markdown("---")

        # --- CAMPOS CONDICIONAIS ---
        f1, f2, f3 = st.columns(3)

        if categoria == "Renda Fixa":
            with f1:
                tipo = st.selectbox("Título", ["CDB", "LCI/LCA", "Tesouro", "Debênture"])
            with f2:
                ativo = st.text_input("Instituição", placeholder="Ex: Banco ABC")
            with f3:
                rent = st.text_input("Rentabilidade", placeholder="Ex: 110% CDI")

        elif categoria == "Renda Variável":
            with f1:
                tipo = st.selectbox("Ativo", ["Ação BR", "Stock (US)", "FII", "ETF"])
            with f2:
                ativo = st.text_input("Ticker", placeholder="Ex: AAPL, WEGE3")
            with f3:
                corretora = st.text_input("Corretora", placeholder="Ex: Swissquote")

        else:  # Criptomoeda
            with f1:
                tipo = st.selectbox("Classe", ["Altcoin", "Stablecoin", "Memecoin"])
            with f2:
                ativo = st.text_input("Moeda", placeholder="Ex: BTC, SOL")
            with f3:
                custodia = st.selectbox("Carteira", ["Exchange", "Hardware Wallet", "Hot Wallet"])

        # --- VALORES E QUANTIDADES ---
        st.markdown("<br>", unsafe_allow_html=True)
        v1, v2, v3 = st.columns(3)
        with v1:
            # Precisão de 8 casas decimais para Cripto
            prec = 8 if categoria == "Criptomoeda" else 2
            step_q = 0.00000001 if categoria == "Criptomoeda" else 0.01
            qtd = st.number_input("Quantidade", min_value=0.0, step=step_q, format=f"%.{prec}f")
        with v2:
            preco = st.number_input("Preço Unit. (CHF)", min_value=0.0, step=0.01)
        with v3:
            taxa = st.number_input("Taxas (CHF)", min_value=0.0, step=0.01)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Confirmar Registro", use_container_width=True):
            st.success(f"Transação de {ativo} processada!")
            st.balloons()
            st.rerun()


# ==========================================
# 3. COMPONENTES DE INTERFACE
# ==========================================

def render_metrics_topo(df):
    k1, k2, k3, k4 = st.columns(4)
    with k1: render_kpi_card("account_balance_wallet", "Patrimônio", f"CHF {df['Total Atual'].sum():,.2f}", "3.2%")
    with k2: render_kpi_card("show_chart", "Lucro Total", f"CHF {df['Lucro/Prejuízo'].sum():,.2f}", "1.5%",
                             color="#18CB96")
    with k3: render_kpi_card("stars", "Top Ativo", "Bitcoin", "42%", color="#32BCAD")
    with k4: render_kpi_card("payments", "Dividendos", "CHF 420.00", "CHF 32.00")


def render_charts_performance(df):
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown('### <span class="pink-icon">bar_chart</span> Performance', unsafe_allow_html=True)
        fig = px.bar(df, x='Ativo', y='Lucro/Prejuízo', color='Lucro/Prejuízo',
                     color_continuous_scale=['#E73469', '#18CB96'])
        fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          template="plotly_white" if st.get_option("theme.base") == "light" else "plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown('### <span class="pink-icon">pie_chart</span> Alocação', unsafe_allow_html=True)
        fig_p = px.pie(df, values='Total Atual', names='Tipo', hole=0.6,
                       color_discrete_sequence=['#E73469', '#373643', '#18CB96', '#f3799d'])
        fig_p.update_layout(height=350, showlegend=True, paper_bgcolor='rgba(0,0,0,0)',
                            legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5))
        st.plotly_chart(fig_p, use_container_width=True)


def render_lista_cards_investimentos(df):
    st.markdown("---")
    st.markdown('### <span class="pink-icon header-icon">list_alt</span> Portfólio Detalhado', unsafe_allow_html=True)

    for _, row in df.iterrows():
        is_pos = row['Rentabilidade %'] >= 0
        cor = "#18CB96" if is_pos else "#E73469"
        cls = "profit-pos" if is_pos else "profit-neg"

        st.markdown(f"""
            <div class="inv-card" style="border-left-color: {cor};">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                    <div style="flex: 1.5;"><div class="inv-symbol">{row['Ativo']}</div><div style="font-size:12px; opacity:0.6;">{row['Tipo']}</div></div>
                    <div style="flex: 1; text-align: center;"><div class="card-label">Posição</div><div style="font-weight:700;">{row['Quantidade']:.2f}</div></div>
                    <div style="flex: 1; text-align: center;"><div class="card-label">Valor Hoje</div><div style="font-weight:700;">CHF {row['Total Atual']:,.2f}</div></div>
                    <div style="flex: 1; text-align: right;">
                        <div class="{cls}" style="font-size:16px;">{"+" if is_pos else ""}{row['Rentabilidade %']:.2f}%</div>
                        <div class="{cls}" style="font-size:12px; opacity:0.8;">CHF {row['Lucro/Prejuízo']:,.2f}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)


# ==========================================
# 4. LÓGICA DE DADOS E ORQUESTRAÇÃO
# ==========================================

def gerar_investimentos_fake():
    df = pd.DataFrame({
        'Ativo': ['BTC', 'ETH', 'AAPL', 'IVVB11', 'USD/CHF', 'PETR4'],
        'Tipo': ['Cripto', 'Cripto', 'Ação US', 'ETF', 'Moeda', 'Ação BR'],
        'Quantidade': [0.5, 2.0, 10, 50, 1000, 100],
        'Preço Médio': [45000.0, 2400.0, 180.0, 250.0, 0.88, 35.0],
        'Valor Atual': [62410.0, 3200.0, 195.0, 275.0, 0.89, 38.0],
    })
    df['Total Gasto'] = df['Quantidade'] * df['Preço Médio']
    df['Total Atual'] = df['Quantidade'] * df['Valor Atual']
    df['Lucro/Prejuízo'] = df['Total Atual'] - df['Total Gasto']
    df['Rentabilidade %'] = (df['Lucro/Prejuízo'] / df['Total Gasto']) * 100
    return df


def renderizar_investimentos():
    inject_clario_css()
    df_inv = gerar_investimentos_fake()

    # Cabeçalho com botão no topo
    c_title, _, c_btn = st.columns([2, 0.5, 1.5], vertical_alignment="bottom")
    with c_title:
        st.markdown('### <span class="pink-icon header-icon">trending_up</span> Meus Investimentos',
                    unsafe_allow_html=True)
    with c_btn:
        if st.button("Novo Aporte", icon=":material/add_card:", use_container_width=True, type="primary"):
            mostrar_popup_aporte()

    st.markdown("<br>", unsafe_allow_html=True)
    render_metrics_topo(df_inv)
    render_charts_performance(df_inv)
    render_lista_cards_investimentos(df_inv)


if __name__ == "__main__":
    renderizar_investimentos()