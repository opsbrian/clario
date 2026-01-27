import streamlit as st
from src.tela_login import renderizar_login
from src.tela_dashboard import renderizar_dashboard

# Inicializa o estado se for a primeira vez
if 'logado' not in st.session_state:
    st.session_state.logado = False

# LÓGICA DE NAVEGAÇÃO
if st.session_state.logado:
    renderizar_dashboard()
else:
    renderizar_login()