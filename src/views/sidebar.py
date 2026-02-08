import streamlit as st
from streamlit_option_menu import option_menu
from src.services.supabase_client import supabase
import time


def renderizar_sidebar():
    with st.sidebar:
        # --- 1. IDENTIDADE VISUAL ---
        # Substitui o título por imagem para um look de fintech premium
        st.image("img/clario_logo_light.svg", use_container_width=True)

        # Respiro entre a logo e o início dos links
        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

        # --- 2. MENU DE NAVEGAÇÃO ---
        selected = option_menu(
            menu_title=None,  # Título removido para dar lugar à logo
            options=["Dashboard", "Transações", "Cartão de Crédito", "Investimentos", "Configurações", "Sair"],
            icons=[
                "grid-1x2", "arrow-left-right", "credit-card", "graph-up", "sliders", "box-arrow-right"
            ],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#fafafa", "font-size": "16px"},
                "nav-link": {
                    "font-size": "15px",
                    "text-align": "left",
                    "margin": "5px",
                    "padding-left": "15px",
                    "--hover-color": "#262730",
                    "color": "#AAA",
                },
                "nav-link-selected": {
                    "background-color": "#E73469",
                    "font-weight": "600",
                    "border-radius": "8px",
                    "color": "#FFF"
                }
            }
        )

        # --- 3. LÓGICA DE LOGOUT ---
        if selected == "Sair":
            try:
                supabase.auth.sign_out()
            except Exception:
                pass

            st.session_state.clear()
            st.toast("Encerrando sessão...", icon="🔒")
            time.sleep(1)
            st.rerun()

        return selected