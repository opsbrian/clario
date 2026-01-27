import streamlit as st
from src.tela_login import renderizar_login
from src.tela_dashboard import renderizar_dashboard
from src.tela_investimento import renderizar_investimentos

# 1. Configuração de Página UNIFICADA (obrigatório ser aqui)
st.set_page_config(
    page_title="Clariô Finance",
    page_icon="🇨🇭",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    # 2. Inicialização do Estado
    if 'logado' not in st.session_state:
        st.session_state.logado = False

    if 'pagina_atual' not in st.session_state:
        st.session_state.pagina_atual = 'Home'

    # 3. SEGURANÇA: Se não estiver logado, para tudo e mostra login
    if not st.session_state.logado:
        renderizar_login()
        st.stop()  # ESSENCIAL: Impede que o código abaixo rode sem o login

    # 4. TELA DO USUÁRIO LOGADO
    theme_base = st.get_option("theme.base")
    logo_path = "img/clario_logo_dark.svg" if theme_base == "dark" else "img/clario_logo_light.svg"

    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)
        st.image(logo_path, width=220)  # Sua logo com presença!
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Home", icon=":material/home:", use_container_width=True):
            st.session_state.pagina_atual = 'Home'
            st.rerun()

        if st.button("Investimentos", icon=":material/trending_up:", use_container_width=True):
            st.session_state.pagina_atual = 'Investimentos'
            st.rerun()

        st.markdown("---")
        if st.button("Sair / Logout", icon=":material/logout:", use_container_width=True):
            # Limpa o login e força o rerun para o Gatekeeper agir
            st.session_state.logado = False
            st.session_state.pagina_atual = 'Home'
            st.rerun()

    # 5. ROTEADOR
    if st.session_state.pagina_atual == 'Home':
        renderizar_dashboard()
    else:
        renderizar_investimentos()


if __name__ == "__main__":
    main()