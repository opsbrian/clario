import streamlit as st
import time

# 1. Configuração (PRIMEIRA LINHA)
st.set_page_config(page_title="Clariô Finance", page_icon="img/clario_logo_dark.svg", layout="centered")


# 2. CSS Global
def carregar_estilos_globais():
    st.markdown("""
        <style>
        .clario-card {
            background-color: var(--secondary-background-color);
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 10px; padding: 20px; margin-top: 10px;
        }
        </style>
    """, unsafe_allow_html=True)


carregar_estilos_globais()

# Importações
from src.views.tela_login import renderizar_login
from src.views.tela_dashboard import renderizar_dashboard
from src.views.tela_transacao import renderizar_nova_transacao
from src.views.sidebar import renderizar_sidebar
from src.views.tela_configuracao import renderizar_configuracoes
from src.views.tela_cartao_credito import renderizar_tela_cartao
from src.views.tela_investimento import renderizar_investimentos
from src.views.tela_reset_senha import renderizar_reset_senha
from src.services.auth_service import obter_usuario_atual, login_com_token
from src.services.cookie_service import pegar_token_do_cookie  # <--- IMPORT NOVO


# 3. Lógica Principal
def main():
    if "logado" not in st.session_state: st.session_state.logado = False
    if "user" not in st.session_state: st.session_state.user = None

    # --- AUTO-LOGIN (COOKIE) ---
    # Só tenta se não estiver logado
    if not st.session_state.logado:

        # 1. Tenta pegar token do Cookie (Persistência)
        token_cookie = pegar_token_do_cookie()
        if token_cookie:
            user_cookie = login_com_token(token_cookie)
            if user_cookie:
                st.session_state.user = user_cookie
                st.session_state.logado = True
                st.rerun()

        # 2. Tenta pegar sessão ativa (Link Mágico / Refresh)
        if not st.session_state.logado:
            user_ativo = obter_usuario_atual()
            if user_ativo:
                st.session_state.user = user_ativo
                st.session_state.logado = True
                st.rerun()

    # --- ROTEAMENTO ---

    if not st.session_state.logado:
        renderizar_login()
        return

    # Tela de Reset de Senha (via Link)
    if st.query_params.get("reset") == "true":
        renderizar_reset_senha()
        return

        # App Normal
    page = renderizar_sidebar()

    if page == "Dashboard":
        renderizar_dashboard()
    elif page == "Transações":
        renderizar_nova_transacao()
    elif page == "Cartão de Crédito":
        renderizar_tela_cartao()
    elif page == "Investimentos":
        renderizar_investimentos()
    elif page == "Configurações":
        renderizar_configuracoes()


if __name__ == "__main__":
    main()