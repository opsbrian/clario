import streamlit as st
from src.tela_login import renderizar_login
from src.tela_dashboard import renderizar_dashboard

if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    renderizar_login()
else:
    # A mágica acontece aqui!
    renderizar_dashboard()