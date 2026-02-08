import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Clariô Finance",
    page_icon="img/clario_logo_dark.svg",  # Aponta para um arquivo local em vez de emoji
    layout="centered",
    initial_sidebar_state="expanded"
)

# Importações
from src.views.tela_login import renderizar_login
from src.views.tela_dashboard import renderizar_dashboard
from src.views.tela_transacao import renderizar_nova_transacao
from src.views.sidebar import renderizar_sidebar
from src.views.tela_configuracao import renderizar_configuracoes
from src.views.tela_cartao_credito import renderizar_tela_cartao
from src.views.tela_investimento import renderizar_investimentos


# Função auxiliar para telas em construção
def renderizar_construcao(titulo):
    st.markdown(f"""
        <div style="padding: 20px; border: 1px solid #333; border-radius: 10px; margin-top: 0px;">
            <h2 style="color: #E73469; margin:0;">{titulo}</h2>
            <p style="opacity: 0.7; margin-top: 10px;">Módulo em desenvolvimento.</p>
        </div>
    """, unsafe_allow_html=True)


# Lógica Principal
if "logado" not in st.session_state or not st.session_state.logado:
    renderizar_login()

else:
    # Renderiza Sidebar e captura a página selecionada
    page = renderizar_sidebar()

    # Roteamento
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