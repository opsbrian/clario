import streamlit as st
import requests

# Endereço da Pluggy
BASE_URL = "https://api.pluggy.ai"

print("\n--- INICIANDO DIAGNÓSTICO DE CREDENCIAIS ---")

# 1. Tenta ler o arquivo secrets.toml
try:
    CLIENT_ID = st.secrets["PLUGGY_CLIENT_ID"]
    SECRET = st.secrets["PLUGGY_CLIENT_SECRET"]
    print(f"✅ Arquivo secrets.toml lido.")
    print(f"   > ID: {CLIENT_ID[:5]}... (oculto)")
    print(f"   > Secret: {SECRET[:5]}... (oculto)")
except Exception as e:
    print(f"❌ ERRO: Não consegui ler o secrets.toml. Verifique a pasta .streamlit")
    exit()

# 2. Tenta fazer login na API (Isso gera o erro 401 se estiver errado)
print("\nTentando autenticar na Pluggy...")
payload = {
    "clientId": CLIENT_ID,
    "clientSecret": SECRET
}

response = requests.post(f"{BASE_URL}/auth", json=payload)

if response.status_code == 200:
    print("🎉 SUCESSO! Credenciais válidas.")
    token = response.json().get("apiKey")
    print(f"   > Token gerado: {token[:10]}...")
else:
    print(f"⛔ FALHA DE AUTENTICAÇÃO (Erro {response.status_code})")
    print(f"   > Mensagem da Pluggy: {response.text}")
    print("\n--- O QUE FAZER ---")
    print("1. Volte no dashboard da Pluggy (dashboard.pluggy.ai).")
    print("2. Gere um novo Client Secret.")
    print("3. Atualize o arquivo .streamlit/secrets.toml")