import streamlit as st

# 1. Configuração da página (Sempre a primeira coisa)
st.set_page_config(
    page_title="Clariô Assistente Financeiro",
    page_icon="💰",
    layout="wide"
)

# Importa as telas da pasta src
from src.tela_login import renderizar_login
from src.tela_dashboard import renderizar_dashboard

# 2. Inicializa o estado da sessão (Session State)
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

# Esta variável controla se mostramos Login ou Cadastro quando deslogado
if 'tela_atual' not in st.session_state:
    st.session_state['tela_atual'] = 'login'

# 3. Roteamento (Router) - O Maestro decide o que mostrar
if st.session_state['logado']:
    renderizar_dashboard()
else:
    if st.session_state['tela_atual'] == 'login':
        renderizar_login() # O botão agora estará aqui dentro
    else:
        renderizar_cadastro()