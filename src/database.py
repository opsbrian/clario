import streamlit as st
from supabase import create_client, Client
import os
import pandas as pd  # Importante para os gráficos!

# --- 1. CONFIGURAÇÃO DA CONEXÃO SUPABASE ---
# Tenta pegar as senhas do arquivo secrets.toml ou do ambiente
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
except:
    # Fallback para variáveis de ambiente (caso não use secrets)
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

# Cria a conexão se as chaves existirem
if url and key:
    db: Client = create_client(url, key)
else:
    # Se não achar as chaves, paramos o app para evitar erros em cascata
    st.error("ERRO CRÍTICO: Configure o arquivo .streamlit/secrets.toml com as chaves do Supabase!")
    st.stop()


# --- 2. FUNÇÕES DE BUSCA ---

def buscar_perfil_usuario(user_id):
    """
    Busca dados do perfil (Nome, Telefone, etc) na tabela 'profiles'
    """
    try:
        response = db.table("profiles").select("*").eq("id", user_id).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        print(f"Erro ao buscar perfil: {e}")
    return None


def buscar_transacoes_dashboard(user_id):
    """
    Busca as transações reais no Supabase e retorna um DataFrame
    formatado para o Dashboard.
    """
    try:
        # 1. Busca no banco (Filtrando pelo usuário)
        response = db.table("transactions").select("*").eq("user_id", user_id).execute()
        dados = response.data

        # 2. Se não tiver dados, retorna DataFrame vazio com as colunas certas
        if not dados:
            return pd.DataFrame(columns=['data', 'valor', 'categoria', 'tipo'])

        # 3. Converte para Pandas DataFrame
        df = pd.DataFrame(dados)

        # 4. Ajusta os tipos de dados para o Plotly não reclamar
        df['data'] = pd.to_datetime(df['date'])  # Converte string '2026-01-01' para Data real
        df['valor'] = pd.to_numeric(df['amount'])
        df['categoria'] = df['category']

        return df

    except Exception as e:
        print(f"Erro ao buscar transações: {e}")
        # Retorna vazio em caso de erro para não quebrar a tela
        return pd.DataFrame(columns=['data', 'valor', 'categoria', 'tipo'])