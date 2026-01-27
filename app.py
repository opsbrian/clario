import streamlit as st
import base64
from src.tela_login import renderizar_login
from src.tela_dashboard import renderizar_dashboard
from src.tela_investimento import renderizar_investimentos

# --- 1. CONFIGURAÇÃO DE PÁGINA (Deve ser o primeiro comando) ---
st.set_page_config(
    page_title="Clariô Finance",
    page_icon="🇨🇭",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- 2. AUXILIAR: CARREGAMENTO DE ASSETS ---
def get_svg_base64(path):
    """Lê o arquivo SVG e converte para string Base64 para evitar erros de path no deploy."""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        st.error(f"Erro ao carregar asset: {path}")
        return ""


def inject_sidebar_logo():
    """Injeta as duas logos via CSS e usa Media Queries para alternar entre elas."""
    logo_dark_theme = get_svg_base64("img/clario_logo_light.svg")  # Logo branca p/ fundo escuro
    logo_light_theme = get_svg_base64("img/clario_logo_dark.svg")  # Logo rosa/preta p/ fundo claro

    st.markdown(f"""
        <style>
            /* Container da Logo */
            .sidebar-logo-container {{
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 10px 0 20px 0;
            }}

            /* Lógica de Troca Dinâmica baseada no tema do Sistema/Navegador */
            .logo-dark {{ display: none; }}
            .logo-light {{ display: block; }}

            @media (prefers-color-scheme: dark) {{
                .logo-light {{ display: none !important; }}
                .logo-dark {{ display: block !important; }}
            }}

            /* Ajuste de tamanho da imagem */
            .sidebar-logo-container img {{
                width: 180px;
                height: auto;
            }}
        </style>

        <div class="sidebar-logo-container">
            <img class="logo-light" src="data:image/svg+xml;base64,{logo_light_theme}">
            <img class="logo-dark" src="data:image/svg+xml;base64,{logo_dark_theme}">
        </div>
    """, unsafe_allow_html=True)


# --- 3. ORQUESTRADOR PRINCIPAL ---
def main():
    # Inicialização do Estado
    if 'logado' not in st.session_state:
        st.session_state.logado = False

    if 'pagina_atual' not in st.session_state:
        st.session_state.pagina_atual = 'Home'

    # GATEKEEPER: Segurança de Acesso
    if not st.session_state.logado:
        renderizar_login()
        st.stop()

        # INTERFACE DO USUÁRIO LOGADO
    with st.sidebar:
        # Injeta a logo dinâmica (substitui o st.image estático)
        inject_sidebar_logo()

        # Navegação Principal
        if st.button("Home", icon=":material/home:", use_container_width=True, key="nav_home"):
            st.session_state.pagina_atual = 'Home'
            st.rerun()

        if st.button("Investimentos", icon=":material/trending_up:", use_container_width=True, key="nav_inv"):
            st.session_state.pagina_atual = 'Investimentos'
            st.rerun()

        st.markdown("---")

        # LOGOUT: Limpa o estado e volta para o login
        if st.button("Sair / Logout", icon=":material/logout:", use_container_width=True, key="nav_logout"):
            st.session_state.logado = False
            st.session_state.pagina_atual = 'Home'
            # del st.session_state['usuario_email'] # Limpe dados sensíveis se houver
            st.rerun()

    # ROTEAMENTO DE TELAS
    if st.session_state.pagina_atual == 'Home':
        renderizar_dashboard()
    else:
        renderizar_investimentos()


if __name__ == "__main__":
    main()