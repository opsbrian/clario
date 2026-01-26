import streamlit as st
import time
from src.autenticacao import verificar_credenciais


def renderizar_login():
    """Desenha a tela de login centralizada"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("🔐 Clariô")
        st.markdown("Acesse sua conta")

        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")

        # Botão de entrar
        if st.button("Entrar", use_container_width=True):
            if verificar_credenciais(email, senha):
                st.success("Bem-vindo!")
                time.sleep(1)
                st.session_state['logado'] = True
                st.rerun()
            else:
                st.error("Dados incorretos.")

        # Espaçamento visual
        st.markdown("---")

        # Botão de cadastro alinhado
        if st.button("Não tem uma conta? Cadastre-se aqui", use_container_width=True):
            st.session_state['tela_atual'] = 'cadastro'
            st.rerun()