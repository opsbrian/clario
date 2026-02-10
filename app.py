import streamlit as st

# 1. Configuração da Página (DEVE SER A PRIMEIRA LINHA)
st.set_page_config(
    page_title="Clariô Finance",
    page_icon="img/clario_logo_dark.svg",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 2. Injeção de CSS Global
def carregar_estilos_globais():
    st.markdown("""
        <style>
        .clario-card {
            background-color: var(--secondary-background-color);
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 10px;
            padding: 20px;
            margin-top: 10px;
        }
        .clario-card p {
            color: var(--text-color);
            opacity: 0.8;
        }
        </style>
    """, unsafe_allow_html=True)

carregar_estilos_globais()

# Importações das Views
from src.views.tela_login import renderizar_login
from src.views.tela_dashboard import renderizar_dashboard
from src.views.tela_transacao import renderizar_nova_transacao
from src.views.sidebar import renderizar_sidebar
from src.views.tela_configuracao import renderizar_configuracoes
from src.views.tela_cartao_credito import renderizar_tela_cartao
from src.views.tela_investimento import renderizar_investimentos

# Função Auxiliar
def renderizar_construcao(titulo):
    st.markdown(f"""
        <div class="clario-card">
            <h2 style="color: #E73469; margin:0;">{titulo}</h2>
            <p>Módulo em desenvolvimento.</p>
        </div>
    """, unsafe_allow_html=True)

# 3. Lógica Principal de Roteamento
def main():
    # Inicializa variáveis de sessão se não existirem
    if "logado" not in st.session_state:
        st.session_state.logado = False
    if "user" not in st.session_state:
        st.session_state.user = None

    # Se NÃO estiver logado, exibe tela de login e encerra
    if not st.session_state.logado:
        renderizar_login()
        return

    # Se estiver logado, continua para o App
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