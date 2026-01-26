import streamlit as st

def renderizar_dashboard():
    """Desenha a tela principal após o login"""
    st.sidebar.title("Menu")

    if st.sidebar.button("Sair"):
        st.session_state['logado'] = False
        st.rerun()

    st.title("📊 Visão Geral")
    st.write("Aqui entrarão os gráficos do sistema.")