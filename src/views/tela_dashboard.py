import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.services.dashboard_service import (
    buscar_perfil_usuario, buscar_resumo_financeiro, buscar_transacoes_graficos
)
# IMPORTAÇÃO DO FORMATADOR (Certifique-se que o arquivo src/utils/formatters.py existe)
from src.utils.formatters import formatar_brl


# ==========================================
# 1. CSS E ESTILIZAÇÃO (THEME AWARE)
# ==========================================
def inject_clario_css():
    st.markdown("""
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
        <style>
            /* Variáveis Globais da Clariô */
            :root { 
                --pink-clario: #E73469; 
                --green-clario: #18CB96; 
                --pill-bg: rgba(128, 128, 128, 0.15);
            }

            /* Ícones Material Symbols */
            .material-symbols-outlined { 
                font-size: 20px; 
                vertical-align: middle; 
                margin-right: 6px;
            }

            /* Card KPI - Adaptativo */
            .kpi-card { 
                background-color: var(--secondary-background-color); 
                padding: 15px 20px;
                border-radius: 12px; 
                border-left: 4px solid var(--pink-clario);
                border-top: 1px solid rgba(128, 128, 128, 0.1);
                border-right: 1px solid rgba(128, 128, 128, 0.1);
                border-bottom: 1px solid rgba(128, 128, 128, 0.1);
                box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
                margin-bottom: 15px; 
                transition: transform 0.2s, box-shadow 0.2s;
            }

            .kpi-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.1);
            }

            /* Rótulo (Título do Card) */
            .card-label { 
                color: var(--text-color);
                opacity: 0.8; 
                font-size: 13px; 
                font-weight: 600; 
                text-transform: uppercase; 
                display: flex; 
                align-items: center; 
                margin-bottom: 8px; 
                white-space: nowrap; 
            }

            /* Valor Principal */
            .card-value { 
                font-size: 22px; 
                font-weight: 800; 
                color: var(--text-color); 
                margin-bottom: 4px;
                white-space: nowrap; /* Evita quebra de valor monetário */
            }

            /* Subtexto */
            .card-sub { 
                font-size: 12px; 
                color: var(--text-color);
                opacity: 0.6; 
                line-height: 1.4; 
                white-space: nowrap; 
                overflow: hidden; 
                text-overflow: ellipsis;
            }

            /* Pílula de conta (Tags) */
            .pill { 
                background: var(--pill-bg); 
                color: var(--text-color);
                padding: 2px 8px; 
                border-radius: 6px; 
                margin-right: 4px; 
                display: inline-block; 
                font-size: 10px;
                font-weight: 600;
            }
        </style>
    """, unsafe_allow_html=True)


def render_kpi_card(icon, label, value, sub_html, color="#E73469"):
    st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {color};">
            <div class="card-label">
                <span class="material-symbols-outlined" style="color:{color};">{icon}</span>
                {label}
            </div>
            <div class="card-value" title="{value}">{value}</div>
            <div class="card-sub">{sub_html}</div>
        </div>
    """, unsafe_allow_html=True)


# ==========================================
# 2. RENDERIZAÇÃO DO DASHBOARD
# ==========================================
def renderizar_dashboard():
    inject_clario_css()

    if 'user' not in st.session_state:
        st.error("Faça login para visualizar.")
        return

    uid = st.session_state.user.id

    # Buscas de dados
    perfil = buscar_perfil_usuario(uid)
    resumo = buscar_resumo_financeiro(uid)
    df = buscar_transacoes_graficos(uid)

    # Saudação Personalizada
    nome = perfil.get('nome', 'Usuário').split()[0].title()
    st.markdown(f"## :material/waving_hand: Salut, {nome}!")
    st.markdown(
        "<p style='opacity: 0.7; font-size: 14px; margin-top: -10px; margin-bottom: 30px;'>Aqui está o resumo das suas finanças.</p>",
        unsafe_allow_html=True)

    # --- LINHA 1: KPIs Principais ---
    k1, k2, k3, k4 = st.columns(4)

    with k1:  # SALDO ATUAL
        contas = resumo.get('detalhe_contas', [])
        sub = "Disponível"
        if len(contas) > 0:
            # Pílulas com formatação BRL
            sub = "".join([f"<span class='pill'>{c['banco']}: {formatar_brl(c['saldo'])}</span>" for c in contas[:2]])

        val_final = formatar_brl(resumo.get('saldo_final', 0))
        render_kpi_card("account_balance", "Saldo Atual", val_final, sub, "#18CB96")

    with k2:  # FATURA CARTÃO
        dt_ini = resumo.get('cartao_inicio')
        dt_fim = resumo.get('cartao_fim')
        sub = "Ciclo Vigente"

        if dt_ini and dt_fim:
            try:
                d1 = dt_ini.split('-')[2] + "/" + dt_ini.split('-')[1]
                d2 = dt_fim.split('-')[2] + "/" + dt_fim.split('-')[1]
                sub = f"{d1} até {d2}"
            except:
                pass

        val_fatura = formatar_brl(resumo.get('fatura_atual', 0))
        render_kpi_card("credit_card", "Fatura Atual", val_fatura, sub, "#E73469")

    with k3:  # INVESTIMENTOS
        r = resumo.get('rentabilidade_total', 0.0)
        l = resumo.get('lucro_prejuizo_total', 0.0)

        if pd.isna(r): r = 0.0
        if pd.isna(l): l = 0.0

        cor = "#18CB96" if l >= 0 else "#FF4B4B"
        sinal = "+" if l >= 0 else ""

        # Subtexto formatado com BRL
        sub = f"<span style='color:{cor}; font-weight:bold;'>{sinal}{r:.1f}% ({formatar_brl(l)})</span>"
        val_invest = formatar_brl(resumo.get('total_investido', 0))

        render_kpi_card("monitoring", "Investimentos", val_invest, sub, "#FF751F")

    with k4:  # BALANÇO LÍQUIDO
        balanco = resumo.get('balanco_liquido', 0.0)
        cor = "#18CB96" if balanco >= 0 else "#FF4B4B"
        sinal = "+" if balanco >= 0 else ""

        val_balanco = formatar_brl(balanco)
        render_kpi_card("savings", "Balanço Líquido", val_balanco, "Saldo Final - Inicial", cor)

    # --- LINHA 2: GRÁFICOS ---
    st.markdown("<br>", unsafe_allow_html=True)
    if not df.empty:
        c1, c2 = st.columns([2, 1])

        with c1:
            st.markdown("### :material/insights: Evolução Patrimonial")
            if 'data' in df.columns:
                df_evo = df[df['tipo'].isin(['entrada', 'saida'])].groupby('data')[
                    'valor_grafico'].sum().reset_index().sort_values('data')

                saldo_inicial = float(perfil.get('saldo_inicial', 0) or 0)
                df_evo['acumulado'] = df_evo['valor_grafico'].cumsum() + saldo_inicial

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_evo['data'], y=df_evo['acumulado'],
                    mode='lines',
                    line=dict(color='#E73469', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(231, 52, 105, 0.1)',
                    hovertemplate='<b>Data:</b> %{x|%d/%m/%Y}<br><b>Saldo:</b> R$ %{y:,.2f}<extra></extra>'
                    # Tooltip personalizado
                ))

                fig.update_layout(
                    height=320,
                    margin=dict(l=0, r=0, t=20, b=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, linecolor='rgba(128,128,128,0.5)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', zeroline=False, tickprefix="R$ ")
                )
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.markdown("### :material/pie_chart: Gastos")
            filtro = df['tipo'].isin(['saida', 'cartao', 'debito'])
            df_g = df[filtro].copy()
            if not df_g.empty:
                df_g['valor_abs'] = df_g['valor'].abs()
                fig = px.pie(
                    df_g, values='valor_abs', names='categoria',
                    hole=0.7,
                    color_discrete_sequence=['#E73469', '#FF85A2', '#880E4F', '#BDBDBD', '#616161']
                )
                fig.update_layout(
                    height=320,
                    showlegend=False,
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                fig.update_traces(textposition='inside', textinfo='percent',
                                  hovertemplate='<b>%{label}</b><br>R$ %{value:,.2f}<extra></extra>')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem gastos registrados.")
    else:
        st.info("Registre movimentações para ver os gráficos.")

    # --- LINHA 3: ESTRATÉGIA ---
    st.markdown("### :material/analytics: Análise Estratégica")
    a1, a2, a3 = st.columns(3)

    with a1:  # SAÚDE FINANCEIRA
        r = resumo.get('saude_ratio', 0.0)
        if pd.isna(r): r = 0.0
        cor = "#18CB96" if r < 70 else "#FF751F"
        render_kpi_card("health_and_safety", "Saúde dos Gastos", f"{r:.1f}% da Renda", "Meta ideal: < 70%", cor)

    with a2:  # TOP ATIVO
        nome = resumo.get('top_ativo_nome', '---')
        lucro = resumo.get('top_ativo_lucro', 0.0)
        if pd.isna(lucro): lucro = 0.0

        cor_top = "#18CB96" if lucro >= 0 else "#E73469"
        render_kpi_card("star", "Top Ativo", nome, f"Retorno: {formatar_brl(lucro)}", cor_top)

    with a3:  # PAGAMENTOS FUTUROS
        pagar = resumo.get('a_pagar', 0.0)
        val_pagar = formatar_brl(pagar)
        render_kpi_card("event_repeat", "Pagamentos Futuros", val_pagar, "Comprometido", "#FF751F")


if __name__ == "__main__":
    renderizar_dashboard()