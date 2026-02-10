import streamlit as st
import pandas as pd
from src.services.config_service import (
    salvar_conta, listar_contas,
    salvar_cartao_config, listar_cartoes_config,
    excluir_config
)
# Importação do formatador de moeda
from src.utils.formatters import formatar_brl


def renderizar_configuracoes():
    # --- CSS CUSTOMIZADO (THEME AWARE) ---
    st.markdown("""
        <style>
        /* Ajuste de inputs para ficarem arredondados */
        .stTextInput input, .stNumberInput input, .stSelectbox { border-radius: 8px; }

        /* Botão Primário (Pink Clariô) */
        div.stButton > button[kind="primary"] { 
            background-color: #E73469 !important; 
            border: none !important; 
            font-weight: 600 !important; 
            color: white !important;
        }

        /* Botão Secundário (Deletar Discreto) - Adaptativo */
        button[kind="secondary"] { 
            border: 1px solid rgba(128, 128, 128, 0.2) !important; 
            background: transparent !important; 
            color: var(--text-color) !important; 
            opacity: 0.6;
        }
        button[kind="secondary"]:hover { 
            color: #FF4B4B !important; 
            border-color: #FF4B4B !important;
            background: rgba(255, 75, 75, 0.1) !important; 
            opacity: 1;
        }

        /* Estilos de Texto */
        .config-card-title { font-weight: 600; font-size: 1rem; color: var(--text-color); }
        .config-card-sub { font-size: 0.85rem; color: var(--text-color); opacity: 0.7; }
        .config-card-value { font-weight: 700; color: #18CB96; font-size: 0.9rem; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## Configurações")
    st.markdown(
        "<p style='opacity: 0.7; font-size: 0.9em; margin-bottom: 20px;'>Gerencie suas contas e cartões para uma organização precisa.</p>",
        unsafe_allow_html=True)

    user_id = st.session_state.user.id

    # --- ABAS COM ICONS ---
    tab_contas, tab_cartoes = st.tabs([
        ":material/account_balance: Contas Bancárias",
        ":material/credit_card: Cartões de Crédito"
    ])

    # ==========================================
    # ABA 1: CONTAS E SALDO INICIAL
    # ==========================================
    with tab_contas:
        c1, c2 = st.columns([1, 1.5], gap="large")

        # COLUNA 1: FORMULÁRIO
        with c1:
            with st.container(border=True):
                st.markdown("##### Nova Conta")
                banco = st.text_input("Nome do Banco", placeholder="Ex: UBS, Neon, Caixa")

                # Input numérico mantém raw number (melhor para digitação)
                saldo = st.number_input("Saldo Inicial Atual (R$)", min_value=0.00, step=100.0, format="%.2f")

                if st.button("Adicionar Conta", type="primary", use_container_width=True):
                    if not banco:
                        st.warning("Informe o nome do banco.")
                    else:
                        ok, msg = salvar_conta(user_id, banco, saldo)
                        if ok:
                            st.toast("Conta adicionada com sucesso!", icon=":material/check_circle:")
                            st.rerun()
                        else:
                            st.error(msg)

        # COLUNA 2: LISTAGEM
        with c2:
            st.markdown("##### Minhas Contas")
            df_contas = listar_contas(user_id)

            if not df_contas.empty:
                for index, row in df_contas.iterrows():
                    saldo_fmt = formatar_brl(row['saldo_inicial'])

                    with st.container(border=True):
                        col_info, col_del = st.columns([5, 1], vertical_alignment="center")

                        with col_info:
                            st.markdown(f"<div class='config-card-title'>{row['nome_banco']}</div>",
                                        unsafe_allow_html=True)
                            st.markdown(f"<div class='config-card-value'>Saldo Inicial: {saldo_fmt}</div>",
                                        unsafe_allow_html=True)

                        with col_del:
                            if st.button("", key=f"del_conta_{row['id']}", icon=":material/delete:", type="secondary",
                                         help="Remover conta"):
                                excluir_config("contas_bancarias", row['id'])
                                st.rerun()
            else:
                st.info("Nenhuma conta cadastrada.")

    # ==========================================
    # ABA 2: CARTÕES DE CRÉDITO
    # ==========================================
    with tab_cartoes:
        c1, c2 = st.columns([1, 1.5], gap="large")

        # COLUNA 1: FORMULÁRIO
        with c1:
            with st.container(border=True):
                st.markdown("##### Novo Cartão")
                nome_card = st.text_input("Apelido do Cartão", placeholder="Ex: Visa Infinite")
                limite = st.number_input("Limite Total (R$)", min_value=0.0, step=500.0)

                cc1, cc2 = st.columns(2)
                dia_fech = cc1.number_input("Dia Fechamento", min_value=1, max_value=31, value=1)
                dia_venc = cc2.number_input("Dia Vencimento", min_value=1, max_value=31, value=10)

                if st.button("Salvar Cartão", type="primary", use_container_width=True):
                    if not nome_card:
                        st.warning("Nome do cartão obrigatório.")
                    else:
                        ok, msg = salvar_cartao_config(user_id, nome_card, limite, dia_fech, dia_venc)
                        if ok:
                            st.toast("Cartão configurado!", icon=":material/credit_card:")
                            st.rerun()

        # COLUNA 2: LISTAGEM
        with c2:
            st.markdown("##### Meus Cartões")
            df_cartoes = listar_cartoes_config(user_id)

            if not df_cartoes.empty:
                for index, row in df_cartoes.iterrows():
                    limite_fmt = formatar_brl(row['limite'])

                    with st.container(border=True):
                        col_info, col_del = st.columns([5, 1], vertical_alignment="center")

                        with col_info:
                            st.markdown(f"<div class='config-card-title'>{row['nome_cartao']}</div>",
                                        unsafe_allow_html=True)
                            st.markdown(
                                f"<div class='config-card-sub'>Fecha dia {row['dia_fechamento']} • Vence dia {row['dia_vencimento']}</div>",
                                unsafe_allow_html=True)
                            st.markdown(
                                f"<div class='config-card-sub' style='margin-top:4px;'>Limite: <b>{limite_fmt}</b></div>",
                                unsafe_allow_html=True)

                        with col_del:
                            if st.button("", key=f"del_card_{row['id']}", icon=":material/delete:", type="secondary",
                                         help="Remover cartão"):
                                excluir_config("config_cartoes", row['id'])
                                st.rerun()
            else:
                st.info("Nenhum cartão configurado.")