import streamlit as st
from postgrest import SyncPostgrestClient
from src.utils_seguranca import gerar_hash

# 1. MELHOR PRÁTICA: Usar st.secrets em vez de load_dotenv para apps no ar
# O Streamlit Cloud lê isso automaticamente do painel de segredos
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
except (KeyError, FileNotFoundError):
    # Fallback para desenvolvimento local (caso ainda use .env)
    import os
    from dotenv import load_dotenv
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

# 2. RENOMEADO: De 'client' para 'db' para bater com o seu src/__init__.py
headers = {"apikey": key, "Authorization": f"Bearer {key}"}
db = SyncPostgrestClient(f"{url}/rest/v1", headers=headers)

def criar_usuario_admin():
    email_admin = "admin@clario.com"

    # Busca se existe usando a variável 'db'
    response = db.table("usuarios").select("*").eq("email", email_admin).execute()

    if not response.data:
        senha_segura = gerar_hash('1234').decode('utf-8')
        novo_usuario = {
            "nome": "Administrador",
            "sobrenome": "Sistema",
            "email": email_admin,
            "senha": senha_segura,
            "pais": "Suíça", # Ajustado para o contexto de Genebra
            "cidade": "Genebra"
        }
        db.table("usuarios").insert(novo_usuario).execute()
        print("✅ Usuário admin criado com sucesso!")
    else:
        print("ℹ️ Usuário admin já existe.")


def buscar_usuario_por_email(email):
    """
    Busca o usuário completo para fins de autenticação (Login).
    """
    try:
        # Usamos a variável 'db' que configuramos anteriormente
        response = db.table("usuarios").select("*").eq("email", email).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Erro ao buscar usuário para login: {e}")
        return None


def buscar_perfil_usuario(email):
    """
    Busca apenas o essencial para a UI do Dashboard (Saudação).
    """
    try:
        response = db.table("usuarios").select("nome", "sobrenome").eq("email", email).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Erro ao buscar perfil: {e}")
        return None