import streamlit as st
import extra_streamlit_components as stx
from datetime import datetime, timedelta


def get_manager():
    """
    Cria o gerenciador de cookies APENAS UMA VEZ.
    Se já existir na sessão, retorna o existente para evitar o erro 'Duplicate Key'.
    """
    # Define uma chave única para o componente
    cookie_key = "clario_cookie_manager"

    # Se ainda não foi criado nesta sessão, cria agora
    if cookie_key not in st.session_state:
        # Cria e salva no session_state
        st.session_state[cookie_key] = stx.CookieManager(key=cookie_key)

    # Retorna a instância salva
    return st.session_state[cookie_key]


def salvar_token_no_cookie(token):
    """
    Salva o token de acesso no navegador do usuário.
    Dura 30 dias.
    """
    try:
        cookie_manager = get_manager()
        expires_at = datetime.now() + timedelta(days=30)

        # Salva o cookie 'clario_token'
        cookie_manager.set('clario_token', token, expires_at=expires_at)
    except Exception as e:
        print(f"Erro ao salvar cookie: {e}")


def pegar_token_do_cookie():
    """
    Tenta ler o token salvo no navegador.
    """
    try:
        cookie_manager = get_manager()
        # Pega todos os cookies para garantir atualização
        cookies = cookie_manager.get_all()
        return cookies.get('clario_token')
    except Exception as e:
        print(f"Erro ao ler cookie: {e}")
        return None


def limpar_cookie():
    """
    Remove o token (Logout).
    """
    try:
        cookie_manager = get_manager()
        cookie_manager.delete('clario_token')
    except Exception as e:
        print(f"Erro ao limpar cookie: {e}")