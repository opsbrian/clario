import streamlit as st
import pandas as pd
from src.services.config_service import (
    salvar_conta, listar_contas,
    salvar_cartao_config, listar_cartoes_config,
    excluir_config
)

def renderizar_configuracoes():
    # CSS Customizado - Mantendo a identidade visual
    st.markdown("""
        <style>
        .stTextInput input, .stNumberInput input, .stSelectbox { border-radius: 8px; }
        div.stButton > button[kind="primary"] { background-color: #E73469; border: none; font-weight: 600; }
        /* Ajuste para o botão de deletar discreto */
        button[kind="secondary"] { border: none; background: transparent; color: #666; }
        button[kind="secondary"]:hover { color: #FF4B4B; background: rgba(255, 75, 75, 0.1); }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## Configurações")
    st.markdown(
        "<p style='opacity: 0.7; font-size: 0.9em;'>Gerencie suas contas e cartões para uma organização precisa.</p>",
        unsafe_allow_html=True)

    user_id = st.session_state.user.id

    # --- ABAS COM ICONS ---
    tab_contas, tab_cartoes = st.tabs([
        ":material/account_balance: Contas Bancárias",
        ":material/credit_card: Cartões de Crédito"
    ])

    # --- ABA 1: CONTAS E SALDO INICIAL ---
    with tab_contas:
        c1, c2 = st.columns([1, 1.5], gap="large")

        with c1:
            with st.container(border=True):
                st.markdown("##### Nova Conta")
                banco = st.text_input("Nome do Banco", placeholder="Ex: UBS, Neon, Caixa")
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

        with c2:
            st.markdown("##### Minhas Contas")
            df_contas = listar_contas(user_id)

            if not df_contas.empty:
                for index, row in df_contas.iterrows():
                    with st.container(border=True):
                        col_info, col_del = st.columns([5, 1], vertical_alignment="center")
                        with col_info:
                            st.markdown(f"**{row['nome_banco']}**")
                            st.markdown(
                                f"<span style='color:#18CB96; font-size:0.9em;'>Saldo: R$ {row['saldo_inicial']:,.2f}</span>",
                                unsafe_allow_html=True)
                        with col_del:
                            if st.button("", key=f"del_conta_{row['id']}", icon=":material/delete:", type="secondary", help="Remover conta"):
                                excluir_config("contas_bancarias", row['id'])
                                st.rerun()
            else:
                st.info("Nenhuma conta cadastrada.")

    # --- ABA 2: CARTÕES DE CRÉDITO ---
    with tab_cartoes:
        c1, c2 = st.columns([1, 1.5], gap="large")

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

        with c2:
            st.markdown("##### Meus Cartões")
            df_cartoes = listar_cartoes_config(user_id)

            if not df_cartoes.empty:
                for index, row in df_cartoes.iterrows():
                    with st.container(border=True):
                        col_info, col_del = st.columns([5, 1], vertical_alignment="center")
                        with col_info:
                            st.markdown(f"**{row['nome_cartao']}**")
                            st.caption(f"Fecha dia {row['dia_fechamento']} • Vence dia {row['dia_vencimento']}")
                            st.markdown(f"<small>Limite: R$ {row['limite']:,.2f}</small>", unsafe_allow_html=True)
                        with col_del:
                            if st.button("", key=f"del_card_{row['id']}", icon=":material/delete:", type="secondary", help="Remover cartão"):
                                excluir_config("config_cartoes", row['id'])
                                st.rerun()
            else:
                st.info("Nenhum cartão configurado.")