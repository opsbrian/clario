import streamlit as st
import pandas as pd
import math
import textwrap
import plotly.express as px
import plotly.graph_objects as go
from src.services.dashboard_service import (
    buscar_perfil_usuario, buscar_resumo_financeiro, buscar_transacoes_graficos
)
from src.utils.formatters import formatar_brl


# ==========================================
# 1. CSS PREMIUM MINIMALISTA & ADAPTATIVO
# ==========================================
def inject_clario_css():
    # CSS sem indentação interna para evitar que o Streamlit interprete como bloco de código
    st.markdown("""
<style>
:root { 
--brand-primary: #E73469; 
--brand-success: #18CB96;
--brand-warning: #FF751F; 
--brand-danger: #FF4B4B;
--bg-card: var(--secondary-background-color);
--text-primary: var(--text-color);
--text-secondary: color-mix(in srgb, var(--text-color), transparent 45%);
--border-subtle: rgba(128, 128, 128, 0.15);
}
.block-container { padding-top: 1.5rem; }
.material-symbols-rounded { font-size: 16px; vertical-align: middle; margin-right: 4px; }
.kpi-card { 
background-color: var(--bg-card); 
padding: 12px 16px;
border-radius: 10px;
border: 1px solid var(--border-subtle);
height: 125px; 
display: flex;
flex-direction: column;
justify-content: space-between;
position: relative;
box-sizing: border-box;
}
.card-header {
font-size: 0.62rem; font-weight: 700; text-transform: uppercase; 
color: var(--text-secondary); letter-spacing: 0.05em;
display: flex; align-items: center;
}
.card-value { 
font-size: 1.15rem; font-weight: 700; color: var(--text-primary); 
line-height: 1.1; margin-top: 2px;
white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.card-sub { 
font-size: 0.7rem; color: var(--text-secondary);
display: flex; align-items: center; gap: 4px;
white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.gauge-container {
width: 100%; display: flex; flex-direction: column; align-items: center; margin-top: -12px;
}
.gauge-footer {
width: 105px; display: flex; justify-content: space-between;
font-size: 0.55rem; font-weight: 700; color: var(--text-secondary); margin-top: -8px;
}
.gauge-status-tag {
font-size: 0.55rem; font-weight: 800; text-transform: uppercase;
padding: 1px 6px; border-radius: 3px; margin-top: 2px;
}
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0" />
""", unsafe_allow_html=True)


# ==========================================
# 2. RENDERIZADORES (ZERO INDENTAÇÃO)
# ==========================================

def render_kpi_card(icon, label, value, sub_html, color="#E73469"):
    html = f"""
<div class="kpi-card" style="border-left: 3px solid {color};">
<div class="card-header">
<span class="material-symbols-rounded" style="color:{color};">{icon}</span>{label}
</div>
<div class="card-body">
<div class="card-value">{value}</div>
<div class="card-sub">{sub_html}</div>
</div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


def render_gauge_card(score, status_text):
    if score >= 90:
        cor, bg_tag = "#E73469", "rgba(231,52,105,0.12)"
    elif score >= 70:
        cor, bg_tag = "#18CB96", "rgba(24,203,150,0.12)"
    elif score >= 40:
        cor, bg_tag = "#FF751F", "rgba(255,117,31,0.12)"
    else:
        cor, bg_tag = "#FF4B4B", "rgba(255,75,75,0.12)"

    rotation = (score * 1.8) - 90
    svg_gauge = f"""
<svg viewBox="0 0 100 60" width="105px" style="overflow: visible;">
<path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="rgba(128,128,128,0.15)" stroke-width="4" stroke-linecap="round" />
<path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="{cor}" stroke-width="4" stroke-linecap="round" stroke-dasharray="{(score / 100) * 125.6}, 125.6" />
<circle cx="50" cy="50" r="2.2" fill="var(--text-color)" />
<line x1="50" y1="50" x2="50" y2="20" stroke="var(--text-color)" stroke-width="1.2" stroke-linecap="round" transform="rotate({rotation}, 50, 50)" style="transition: transform 1s ease-in-out;" />
<text x="50" y="47" text-anchor="middle" font-size="9" font-weight="800" fill="var(--text-color)">{int(score)}</text>
</svg>
"""
    html = f"""
<div class="kpi-card" style="border-left: 3px solid {cor};">
<div class="card-header">
<span class="material-symbols-rounded" style="color:{cor};">health_and_safety</span>Saúde Financeira
</div>
<div class="gauge-container">
{svg_gauge}
<div class="gauge-footer"><span>0</span><span>100</span></div>
<span class="gauge-status-tag" style="color: {cor}; background: {bg_tag};">{status_text}</span>
</div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# ==========================================
# 3. CONSTRUÇÃO DO DASHBOARD
# ==========================================
def renderizar_dashboard():
    inject_clario_css()

    if 'user' not in st.session_state:
        st.error("Realize o login para acessar.")
        return

    uid = st.session_state.user.id
    perfil = buscar_perfil_usuario(uid)
    resumo = buscar_resumo_financeiro(uid)
    df = buscar_transacoes_graficos(uid)

    # Identificação do Usuário: Prioridade para o Nome no Banco -> Metadados do Auth
    nome_usuario = perfil.get('nome')
    if not nome_usuario or nome_usuario == "Usuário":
        nome_usuario = st.session_state.user.user_metadata.get('full_name', 'Usuário')

    primeiro_nome = nome_usuario.split()[0].title()
    st.markdown(f"### Salut, {primeiro_nome}! 👋")

    # --- KPIs ---
    k1, k2, k3, k4 = st.columns(4)

    with k1:  # SALDO EM CONTA
        contas = resumo.get('detalhe_contas', [])
        sub = "".join([
                          f"<span style='background:rgba(128,128,128,0.1); color:var(--text-secondary); padding:2px 5px; border-radius:3px; font-size:0.6rem; font-weight:600; margin-right:4px;'>{c['banco']}: {formatar_brl(c['saldo'])}</span>"
                          for c in contas[:2]]) if contas else "Saldo Disponível"
        render_kpi_card("account_balance", "Saldo Atual", formatar_brl(resumo.get('saldo_final', 0)), sub, "#18CB96")

    with k2:  # CARTÃO DE CRÉDITO
        dt_ini, dt_fim = resumo.get('cartao_inicio'), resumo.get('cartao_fim')
        sub = f"{dt_ini.split('-')[2]}/{dt_ini.split('-')[1]} a {dt_fim.split('-')[2]}/{dt_fim.split('-')[1]}" if dt_ini else "Ciclo de Fatura"
        render_kpi_card("credit_card", "Fatura Atual", formatar_brl(resumo.get('fatura_atual', 0)), sub, "#E73469")

    with k3:  # INVESTIMENTOS
        lucro_pct = resumo.get('invest_lucro_pct', 0.0)
        cor = "#18CB96" if lucro_pct >= 0 else "#FF4B4B"
        sub = f"<span style='color:{cor}; font-weight:600;'>Performance: {lucro_pct:.1f}%</span>"
        render_kpi_card("monitoring", "Investimentos", formatar_brl(resumo.get('invest_saldo_atual', 0.0)), sub,
                        "#FF751F")

    with k4:  # PATRIMÔNIO TOTAL
        render_kpi_card("savings", "Patrimônio Total", formatar_brl(resumo.get('balanco_liquido', 0.0)), "Consolidado",
                        "#18CB96")

    # --- GRÁFICOS ---
    st.markdown("<br>", unsafe_allow_html=True)
    if not df.empty:
        c1, c2 = st.columns([2.5, 1])
        with c1:
            st.caption("Evolução Patrimonial")
            df_evo = df[df['tipo'].isin(['entrada', 'saida'])].groupby('data')[
                'valor_grafico'].sum().reset_index().sort_values('data')
            df_evo['acumulado'] = df_evo['valor_grafico'].cumsum() + float(perfil.get('saldo_inicial', 0) or 0)
            fig = go.Figure(
                go.Scatter(x=df_evo['data'], y=df_evo['acumulado'], mode='lines', line=dict(color='#E73469', width=2),
                           fill='tozeroy', fillcolor='rgba(231, 52, 105, 0.02)'))
            fig.update_layout(height=220, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, tickfont=dict(size=9)),
                              yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.05)', tickfont=dict(size=9)))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        with c2:
            st.caption("Distribuição de Gastos")
            df_g = df[df['tipo'].isin(['saida', 'cartao', 'debito'])].copy()
            if not df_g.empty:
                fig = px.pie(df_g, values=df_g['valor'].abs(), names='categoria', hole=0.8,
                             color_discrete_sequence=['#E73469', '#FF85A2', '#18CB96', '#FF751F'])
                fig.update_layout(height=220, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- ANÁLISE ESTRATÉGICA ---
    st.markdown("<br>", unsafe_allow_html=True)
    a1, a2, a3 = st.columns(3)
    with a1:
        render_gauge_card(resumo.get('saude_score', 0.0), resumo.get('saude_texto', '---'))
    with a2:
        render_kpi_card("star", "Top Ativo", resumo.get('top_ativo_nome', '---'),
                        f"Lucro: {formatar_brl(resumo.get('top_ativo_lucro', 0.0))}", "#18CB96")
    with a3:
        render_kpi_card("event_repeat", "Pagamentos", formatar_brl(resumo.get('a_pagar', 0.0)), "Comprometido",
                        "#FF751F")


if __name__ == "__main__":
    renderizar_dashboard()