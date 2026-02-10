import streamlit as st
from streamlit_option_menu import option_menu
from src.services.supabase_client import supabase
from src.services.cookie_service import limpar_cookie


def renderizar_sidebar():
    # --- 1. LINKS (Confira se abrem no navegador) ---
    URL_LOGO_FUNDO_CLARO = "https://eyyqaqtqylpmvhcfvtmn.supabase.co/storage/v1/object/public/logo/clario_escuro.png"
    URL_LOGO_FUNDO_ESCURO = "https://eyyqaqtqylpmvhcfvtmn.supabase.co/storage/v1/object/public/logo/clario_claro.png"

    # --- 2. CSS À PROVA DE FALHAS ---
    st.markdown("""
        <style>
        .sidebar-logo {
            width: 180px;
            max-width: 100%;
            margin: 0 auto 20px auto;
        }

        /* --- LÓGICA DE EXIBIÇÃO --- */

        /* 1. Por PADRÃO (ou Light Mode), mostra a logo escura e esconde a clara */
        #img-logo-light { display: block !important; }
        #img-logo-dark { display: none !important; }

        /* 2. Se detectar DARK MODE, inverte a lógica */
        [data-theme="dark"] #img-logo-light { display: none !important; }
        [data-theme="dark"] #img-logo-dark { display: block !important; }

        </style>
    """, unsafe_allow_html=True)

    # --- 3. HTML ---
    with st.sidebar:
        # Injetamos as duas imagens
        st.markdown(f"""
            <div style="text-align: center; padding-top: 15px;">
                <img id="img-logo-light" class="sidebar-logo" src="{URL_LOGO_FUNDO_CLARO}" alt="Logo Clario">
                <img id="img-logo-dark" class="sidebar-logo" src="{URL_LOGO_FUNDO_ESCURO}" alt="Logo Clario Dark">
            </div>
        """, unsafe_allow_html=True)

        # Menu
        # Adicionei "Sair" como opção no menu
        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Transações", "Cartão de Crédito", "Investimentos", "Configurações", "Sair"],
            icons=["speedometer2", "arrow-left-right", "credit-card", "graph-up-arrow", "gear", "box-arrow-right"],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "nav-link-selected": {"background-color": "#E73469"},
            }
        )

        # Se o usuário clicou em Sair, executa a função IMEDIATAMENTE
        if selected == "Sair":
            fazer_logout()

    return selected


def fazer_logout():
    """Realiza o logout completo: Supabase, Cookies e Session State"""

    # 1. Limpa o Cookie do navegador (Impede auto-login)
    try:
        limpar_cookie()
    except Exception as e:
        print(f"Erro ao limpar cookie: {e}")

    # 2. Desloga do Supabase
    try:
        supabase.auth.sign_out()
    except Exception as e:
        print(f"Erro ao deslogar Supabase: {e}")

    # 3. Limpa a sessão do Streamlit
    st.session_state.clear()

    # Garante que as variáveis chaves foram resetadas
    st.session_state.logado = False
    st.session_state.user = None

    # 4. Recarrega a página (vai cair na tela de login)
    st.rerun()