import streamlit as st
from streamlit_option_menu import option_menu
from src.services.supabase_client import supabase
import time


def renderizar_sidebar():
    with st.sidebar:
        # Espaçamento superior para não colar no topo
        st.markdown("<br>", unsafe_allow_html=True)

        # Menu Lateral com Ícones (Bootstrap Icons)
        selected = option_menu(
            menu_title="Clariô Finance",  # Título do Menu
            options=["Dashboard", "Transações", "Cartão de Crédito", "Investimentos", "Configurações", "Sair"],
            icons=[
                "grid-1x2",  # Dashboard (Mais minimalista que o velocímetro)
                "arrow-left-right",  # Transações
                "credit-card",  # Cartão
                "graph-up",  # Investimentos
                "sliders",  # Configurações (Mais técnico que a engrenagem)
                "box-arrow-right"  # Sair
            ],
            menu_icon="wallet2",  # Ícone do título
            default_index=0,

            # CSS Personalizado - Tema Dark/Rosa
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#fafafa", "font-size": "16px"},
                "nav-link": {
                    "font-size": "15px",
                    "text-align": "left",
                    "margin": "6px",
                    "padding-left": "15px",
                    "--hover-color": "#262730",
                },
                "nav-link-selected": {
                    "background-color": "#E73469",  # Rosa Clariô
                    "font-weight": "500",
                    "border-radius": "8px",
                },
                "menu-title": {
                    "font-size": "18px",
                    "font-weight": "700",
                    "color": "#E73469",
                    "margin-bottom": "20px"
                }
            }
        )

        # Lógica de Logout
        if selected == "Sair":
            try:
                supabase.auth.sign_out()
            except:
                pass

            st.session_state.clear()
            # Sem emojis na mensagem
            st.toast("Encerrando sessão...", icon="🔒")
            time.sleep(1)
            st.rerun()

        return selected