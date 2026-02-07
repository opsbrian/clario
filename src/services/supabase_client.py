import streamlit as st
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente se estiver rodando localmente
load_dotenv()

# Tenta pegar as chaves do .streamlit/secrets.toml OU do arquivo .env
url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

# Verificação de segurança
if not url or not key:
    st.error("🚨 Erro Crítico: Credenciais do Supabase não encontradas. Verifique se o arquivo .env ou secrets.toml está configurado corretamente.")
    st.stop()

# Cria a conexão única que será usada pelo app todo
supabase: Client = create_client(url, key)