import os
from postgrest import SyncPostgrestClient  # Versão mais leve
from dotenv import load_dotenv
from src.utils_seguranca import gerar_hash

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# Conexão direta com a tabela via API REST do Supabase
# Isso substitui o 'create_client' do pacote pesado
headers = {"apikey": key, "Authorization": f"Bearer {key}"}
client = SyncPostgrestClient(f"{url}/rest/v1", headers=headers)


def criar_usuario_admin():
    email_admin = "admin@clario.com"

    # Busca se existe
    response = client.table("usuarios").select("*").eq("email", email_admin).execute()

    if not response.data:
        senha_segura = gerar_hash('1234').decode('utf-8')
        novo_usuario = {
            "nome": "Administrador",
            "sobrenome": "Sistema",
            "email": email_admin,
            "senha": senha_segura,
            "pais": "Brasil",
            "cidade": "São Paulo"
        }
        client.table("usuarios").insert(novo_usuario).execute()
        print("✅ Usuário admin criado com sucesso!")
    else:
        print("ℹ️ Usuário admin já existe.")


def buscar_usuario_por_email(email):
    response = client.table("usuarios").select("*").eq("email", email).execute()
    return response.data[0] if response.data else None