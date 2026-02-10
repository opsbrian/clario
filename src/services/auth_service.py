import streamlit as st
from src.services.supabase_client import supabase


# ==========================================
# 1. FUNÇÃO DE LOGIN
# ==========================================
def login_user(email, password):
    """
    Tenta logar. Retorna SEMPRE dois valores: (user, erro)
    """
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})

        if response.user and response.session:
            return response.user, None
        else:
            return None, "Usuário não encontrado."

    except Exception as e:
        msg_erro = str(e)
        if "Invalid login credentials" in msg_erro:
            return None, "E-mail ou senha incorretos."
        elif "Email not confirmed" in msg_erro:
            return None, "E-mail não confirmado. Verifique sua caixa de entrada."
        else:
            return None, f"Erro no sistema: {msg_erro}"


# ==========================================
# 2. RECUPERAÇÃO DE SENHA (LINK OFICIAL)
# ==========================================
def enviar_email_recuperacao(email, data_nascimento):
    """
    Valida dados e envia para a URL de produção: clario.streamlit.app
    """
    try:
        # 1. Validação de Segurança (Checa data de nascimento)
        check = supabase.table("usuarios").select("*").eq("email", email).execute()

        # Se o usuário existir na tabela de perfil, validamos a data
        if check.data:
            usuario = check.data[0]
            data_banco = usuario.get('data_nascimento')

            # Se tiver data cadastrada, tem que bater
            if data_banco and str(data_banco) != str(data_nascimento):
                return False, "A data de nascimento não confere."

        # 2. LINK DE REDIRECIONAMENTO (PRODUÇÃO)
        # Adicionamos ?reset=true para ativar a tela de troca de senha
        redirect_url = "https://clario.streamlit.app/?reset=true"

        supabase.auth.reset_password_email(email, options={'redirect_to': redirect_url})
        return True, "Link enviado! Verifique seu e-mail."

    except Exception as e:
        if "User not found" in str(e):
            return False, "E-mail não encontrado."
        return False, f"Erro: {str(e)}"


def atualizar_senha_usuario(nova_senha):
    try:
        supabase.auth.update_user({"password": nova_senha})
        return True, "Senha atualizada com sucesso!"
    except Exception as e:
        return False, str(e)


# ==========================================
# 3. UTILITÁRIOS
# ==========================================
def obter_usuario_atual():
    """
    Verifica sessão ativa (Login ou Magic Link)
    """
    try:
        session = supabase.auth.get_session()
        if session: return session.user
        return None
    except:
        return None