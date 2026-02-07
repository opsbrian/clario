import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.services.dashboard_service import buscar_perfil_usuario, buscar_resumo_financeiro, buscar_transacoes_graficos


# --- CSS GLOBAL ---
def inject_clario_css():
    st.markdown("""
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
        <style>
            :root { --pink-clario: #E73469; --green-clario: #18CB96; --dark-bg: #373643; }
            .pink-icon { color: var(--pink-clario); font-family: 'Material Symbols Outlined'; font-size: 24px; vertical-align: middle; margin-right: 8px; }
            .kpi-card { 
                background-color: var(--secondary-background-color); 
                padding: 20px; 
                border-radius: 15px; 
                border-left: 5px solid var(--pink-clario); 
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }
            .card-label { opacity: 0.8; font-size: 14px; font-weight: 500; }
            .card-value { font-size: 26px; font-weight: 800; margin: 5px 0; }
            .card-sub { font-size: 12px; opacity: 0.6; }
        </style>
    """, unsafe_allow_html=True)


# --- COMPONENTE DE CARD ---
def render_kpi_card(icon, label, value, subtext, color="#e73469"):
    st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {color};">
            <div class="card-label"><span class="pink-icon" style="color:{color};">{icon}</span>{label}</div>
            <div class="card-value">{value}</div>
            <div class="card-sub">{subtext}</div>
        </div>
    """, unsafe_allow_html=True)


# --- DASHBOARD PRINCIPAL ---
def renderizar_dashboard():
    inject_clario_css()

    # 1. Identificação do Usuário
    nome_exibicao = "Usuário"
    user_id = None

    if 'user' in st.session_state and st.session_state.user:
        user_id = st.session_state.user.id
        perfil = buscar_perfil_usuario(user_id)
        if perfil and perfil.get('nome'):
            nome_exibicao = perfil.get('nome').split()[0].title()

    st.markdown(f"""
        <div style='display: flex; align-items: center; gap: 15px; margin-bottom: 20px;'>
            <span class="pink-icon" style="font-size: 36px;">waving_hand</span>
            <div>
                <h2 style='margin: 0;'>Salut, {nome_exibicao}!</h2>
                <p style='opacity: 0.7; margin: 0; font-size: 0.9em;'>Aqui está o resumo das suas finanças.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if user_id:
        # 2. Busca Dados Consolidados
        resumo = buscar_resumo_financeiro(user_id)
        df = buscar_transacoes_graficos(
            user_id)  # Deve conter colunas: data, valor, tipo (saida, entrada, cartao), categoria

        st.markdown("<br>", unsafe_allow_html=True)

        # 3. KPIs (Ajustados conforme solicitado)
        k1, k2, k3 = st.columns(3)

        with k1:
            # KPI 1: Saldo Atual (Dinheiro em conta)
            saldo_atual = resumo.get('saldo_final', 0.0)
            render_kpi_card("account_balance", "Saldo Atual", f"R$ {saldo_atual:,.2f}",
                            "Disponível em conta", color="#18CB96")

        with k2:
            # KPI 2: Fatura Atual (Cartão de Crédito)
            # Assume que o serviço retorna 'fatura_atual'. Se não, soma transações do tipo 'cartao'
            fatura_atual = resumo.get('fatura_atual', 0.0)
            render_kpi_card("credit_card", "Fatura Atual", f"R$ {fatura_atual:,.2f}",
                            "Cartão de Crédito", color="#e73469")

        with k3:
            # KPI 3: Balanço Líquido (Entradas - Saídas Totais)
            # Entradas Totais - (Saídas Conta + Gastos Cartão)
            balanco = resumo.get('entradas', 0) - resumo.get('saidas', 0)
            cor_balanco = "#18CB96" if balanco >= 0 else "#ff4b4b"
            render_kpi_card("savings", "Balanço Líquido", f"R$ {balanco:,.2f}",
                            "Entradas vs Gastos", color=cor_balanco)

        # 4. Gráficos
        st.markdown("<br>", unsafe_allow_html=True)

        if not df.empty:
            c1, c2 = st.columns([2, 1])

            with c1:
                st.markdown('### Evolução Patrimonial')
                if 'data' in df.columns and 'valor' in df.columns:
                    # Agrupa por data e soma valores do dia
                    df_chart = df.groupby('data')['valor'].sum().reset_index().sort_values('data')

                    # LOGICA AJUSTADA: Soma Acumulada (Cumsum) para ver evolução e não apenas fluxo diário
                    df_chart['saldo_acumulado'] = df_chart['valor'].cumsum() + resumo.get('saldo_inicial', 0)

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_chart['data'],
                        y=df_chart['saldo_acumulado'],  # Usando o acumulado
                        mode='lines+markers',
                        line=dict(color='#e73469', width=3),
                        marker=dict(size=6),
                        fill='tozeroy',
                        fillcolor='rgba(231, 52, 105, 0.1)'
                    ))
                    fig.update_layout(
                        height=350, template="plotly_white",
                        margin=dict(l=0, r=0, t=10, b=0),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        yaxis_title="Patrimônio (R$)"
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with c2:
                st.markdown('### Gastos por Categoria')
                if 'categoria' in df.columns:
                    # LOGICA AJUSTADA: Filtra 'saida' (conta) E 'cartao' (crédito)
                    # Assumindo que o DF unificado usa tipos como 'saida' e 'cartao' ou valores negativos
                    filtro_gastos = df['tipo'].isin(['saida', 'cartao', 'debito', 'credito'])
                    df_saidas = df[filtro_gastos]

                    # Se o filtro por string falhar, fallback para valores negativos (saídas)
                    if df_saidas.empty and not df.empty:
                        df_saidas = df[df['valor'] < 0]

                    if not df_saidas.empty:
                        # Garante valores positivos para o gráfico de rosca
                        df_saidas['valor_abs'] = df_saidas['valor'].abs()

                        fig_pie = px.donut(
                            df_saidas, values='valor_abs', names='categoria',
                            hole=0.6,
                            color_discrete_sequence=['#e73469', '#373643', '#18CB96', '#f3799d', '#ffb703']
                        )
                        fig_pie.update_layout(
                            height=350, showlegend=False,
                            margin=dict(l=10, r=10, t=10, b=10),
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_pie, use_container_width=True)
                    else:
                        st.info("Sem gastos registrados para exibir gráfico.")
        else:
            st.markdown("""
                <div style="text-align: center; opacity: 0.6; padding: 30px; border: 1px dashed #555; border-radius: 10px;">
                    <p>O Saldo Inicial já consta no topo! 👆</p>
                    <p>Comece a registrar transações bancárias ou de cartão para ver os gráficos.</p>
                </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    renderizar_dashboard()