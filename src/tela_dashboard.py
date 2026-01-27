import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 0. CONFIGURAÇÃO DA PÁGINA (WIDE MODE) ---
st.set_page_config(
    page_title="Clariô Dashboard",
    page_icon="🇨🇭",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- 1. ESTILO CSS (SENSÍVEL AO TEMA LIGHT/DARK) ---
def inject_clario_css():
    st.markdown("""
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
        <style>
            :root {
                --pink-clario: #E73469;
                --green-clario: #18CB96;
            }

            .pink-icon {
                color: var(--pink-clario);
                font-family: 'Material Symbols Outlined';
                font-size: 24px;
                vertical-align: middle;
                margin-right: 8px;
            }

            .header-icon {
                font-size: 28px;
                vertical-align:text-bottom;
            }

            .kpi-card {
                background-color: var(--secondary-background-color);
                color: var(--text-color);
                padding: 20px; 
                border-radius: 15px;
                border-left: 5px solid var(--pink-clario); 
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                margin-bottom: 15px;
                min-height: 120px;
            }

            .card-label { opacity: 0.8; font-size: 14px; font-weight: 500; }
            .card-value { font-size: 26px; font-weight: 800; margin: 5px 0; }
            .card-delta-pos { color: #18CB96; font-size: 14px; font-weight: 600; }
            .card-delta-neg { color: var(--pink-clario); font-size: 14px; font-weight: 600; }

            .payment-list { font-size: 13px; opacity: 0.7; margin-top: 10px; line-height: 1.4; }
        </style>
    """, unsafe_allow_html=True)


# --- 2. FUNÇÃO AUXILIAR PARA OS CARDS ---
def render_kpi_card(icon, label, value, delta, is_positive=True, color="#e73469"):
    delta_class = "card-delta-pos" if is_positive else "card-delta-neg"
    delta_prefix = "▲" if is_positive else "▼"

    st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {color};">
            <div style="display: flex; align-items: center;">
                <span class="pink-icon" style="color: {color};">{icon}</span>
                <span class="card-label">{label}</span>
            </div>
            <div class="card-value">{value}</div>
            <div class="{delta_class}">{delta_prefix} {delta}</div>
        </div>
    """, unsafe_allow_html=True)


# --- 3. DADOS FICTÍCIOS ---
def gerar_dados_teste():
    hoje = datetime.now()
    datas = [hoje - timedelta(days=x) for x in range(30)]
    df = pd.DataFrame({
        'data': sorted(datas),
        'valor': np.random.uniform(100, 500, size=30).cumsum() + 5000,
        'categoria': np.random.choice(['Lazer', 'Alimentação', 'Moradia', 'Transporte', 'Saúde'], 30)
    })
    return df


# --- 4. RENDERIZAÇÃO DO DASHBOARD ---
def renderizar_dashboard():
    inject_clario_css()
    df_ficticio = gerar_dados_teste()

    # --- LÓGICA DE IDENTIFICAÇÃO DINÂMICA ---
    email_logado = st.session_state.get('usuario_email')

    if email_logado:
        try:
            from src.database import buscar_perfil_usuario
            perfil = buscar_perfil_usuario(email_logado)
            nome_exibicao = perfil['nome'] if perfil else "Visitante"
        except ImportError:
            nome_exibicao = "Brian (Local)" # Fallback caso a pasta src não esteja acessível
    else:
        nome_exibicao = "Brian"


    # --- CABEÇALHO ---
    st.markdown(f"""
        <div style='display: flex; align-items: center; gap: 15px;'>
            <span class="pink-icon" style="font-size: 40px;">waving_hand</span>
            <h1 style='margin: 0;'>Salut, {nome_exibicao}!</h1>
        </div>
        <p style='opacity: 0.7; margin-left: 55px;'>Seu panorama financeiro atualizado em Genebra.</p>
    """, unsafe_allow_html=True)

    # --- MÉTRICAS PRINCIPAIS ---
    st.markdown("<br>", unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    with k1:
        render_kpi_card("account_balance", "Saldo Total", "CHF 12.450,00", "2.5% (mês)")
    with k2:
        render_kpi_card("monitoring", "Investimentos", "CHF 45.102,00", "CHF 320,00")
    with k3:
        render_kpi_card("savings", "Economia", "CHF 1.250,00", "15%", color="#32BCAD")

    # --- SEÇÃO DE GRÁFICOS ---
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])

    with c1:
        st.markdown('### <span class="pink-icon header-icon">ssid_chart</span> Evolução Patrimonial',
                    unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_ficticio['data'], y=df_ficticio['valor'],
            fill='tozeroy', line=dict(color='#e73469', width=4),
            fillcolor='rgba(231, 52, 105, 0.1)'
        ))
        fig.update_layout(
            height=350,
            template="plotly_white" if st.get_option("theme.base") == "light" else "plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('### <span class="pink-icon header-icon">donut_small</span> Gastos por Categoria',
                    unsafe_allow_html=True)
        fig_pie = px.pie(df_ficticio, values='valor', names='categoria', hole=0.7,
                         color_discrete_sequence=['#e73469', '#373643', '#32BCAD', '#f3799d'])

        fig_pie.update_layout(
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5),
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=0, b=0)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- SEÇÃO MERCADO ---
    st.markdown("---")
    st.markdown('### <span class="pink-icon header-icon">monitoring</span> Mercado e Performance',
                unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        render_kpi_card("trending_up", "Rentabilidade", "+1.85%", "Mês atual")
    with m2:
        render_kpi_card("payments", "USD / CHF", "0.88", "0.2%", is_positive=False, color="#555")
    with m3:
        render_kpi_card("currency_bitcoin", "Bitcoin (BTC)", "CHF 62.4k", "4.1%", color="#555")
    with m4:
        render_kpi_card("show_chart", "B3 (Ibovespa)", "128.5k pts", "1.2%", is_positive=False, color="#555")

    # --- SEÇÃO PAGAMENTOS ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('### <span class="pink-icon header-icon">calendar_today</span> Pagamentos Pendentes',
                unsafe_allow_html=True)

    p1, p2, p3 = st.columns(3)

    with p1:
        st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #e73469;">
                <div style="display: flex; align-items: center;"><span class="pink-icon" style="color: #e73469;">calendar_month</span><span class="card-label">Fevereiro</span></div>
                <div class="card-value">CHF 2.100,00</div>
                <div class="payment-list">• Aluguel (Genebra)<br>• Seguro Saúde</div>
            </div>
        """, unsafe_allow_html=True)
    with p2:
        st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #e73469;">
                <div style="display: flex; align-items: center;"><span class="pink-icon" style="color: #e73469;">calendar_month</span><span class="card-label">Março</span></div>
                <div class="card-value">CHF 1.450,00</div>
                <div class="payment-list">• Assinaturas Cloud<br>• Leasing Carro</div>
            </div>
        """, unsafe_allow_html=True)
    with p3:
        st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #18cb96;">
                <div style="display: flex; align-items: center;"><span class="pink-icon" style="color: #18cb96;">check_circle</span><span class="card-label">Status Financeiro</span></div>
                <div class="card-value">Saudável</div>
                <div class="payment-list">Todas as provisões para o próximo trimestre estão garantidas.</div>
            </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    renderizar_dashboard()