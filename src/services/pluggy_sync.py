import requests
import streamlit as st
from src.database import db
import time

# --- CONFIGURAÇÃO ---
BASE_URL = "https://api.pluggy.ai"

# Tenta pegar as credenciais
try:
    CLIENT_ID = "093721db-5e48-4df7-a14a-37d93533f003"
    CLIENT_SECRET = "68d306f7-56af-4184-8952-422b4bffe6ad"
except:
    CLIENT_ID = ""
    CLIENT_SECRET = ""


def get_api_token():
    """
    Autentica na Pluggy e pega a 'API Key' temporária.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        return None

    try:
        payload = {"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}
        response = requests.post(f"{BASE_URL}/auth", json=payload)

        if response.status_code == 200:
            return response.json().get("apiKey")
        else:
            print(f"Erro Auth Pluggy: {response.text}")
            return None
    except Exception as e:
        print(f"Erro conexão: {e}")
        return None


def gerar_token_widget(user_id):
    """
    Gera o token para abrir o Widget (Connect Token).
    """
    api_key = get_api_token()
    if not api_key: return None

    headers = {"X-API-KEY": api_key}
    # clientUserId liga essa conexão ao ID do usuário no Supabase
    payload = {"clientUserId": user_id}

    try:
        resp = requests.post(f"{BASE_URL}/connect_token", json=payload, headers=headers)
        if resp.status_code == 200:
            return resp.json().get("accessToken")
    except Exception as e:
        print(f"Erro widget: {e}")

    return None


def sincronizar_conta_usuario(user_id):
    """
    1. Busca contas (items)
    2. Baixa transações
    3. Salva no Supabase
    """
    api_key = get_api_token()
    if not api_key: return "Erro: Verifique CLIENT_ID e SECRET no secrets.toml"

    headers = {"X-API-KEY": api_key}

    try:
        # 1. Buscar Itens (Conexões Bancárias)
        # Nota: A Pluggy não filtra items por clientUserId na API direta facilmente,
        # então pegamos todos e filtramos na memória (para MVP ok).
        resp_items = requests.get(f"{BASE_URL}/items", headers=headers)
        if resp_items.status_code != 200:
            return f"Erro ao buscar itens: {resp_items.text}"

        all_items = resp_items.json().get("results", [])

        # Filtra apenas itens deste usuário
        user_items = [i for i in all_items if i.get("clientUserId") == user_id]

        if not user_items:
            return "Nenhuma conta conectada encontrada. Use o botão 'Conectar Conta' primeiro."

        total_salvo = 0

        # 2. Para cada banco conectado...
        for item in user_items:
            item_id = item.get("id")

            # Busca transações (últimos 30 dias é o padrão se não passar data)
            resp_trans = requests.get(f"{BASE_URL}/transactions?itemId={item_id}", headers=headers)

            if resp_trans.status_code == 200:
                transactions = resp_trans.json().get("results", [])

                for tr in transactions:
                    # Verifica duplicidade no banco
                    existe = db.table("transactions").select("id").eq("description", tr.get("description")).eq("date",
                                                                                                               tr.get(
                                                                                                                   "date")[
                                                                                                                   :10]).eq(
                        "amount", tr.get("amount")).execute()

                    if not existe.data:
                        # Prepara dados
                        dados = {
                            "user_id": user_id,
                            "description": tr.get("description"),
                            "amount": tr.get("amount"),
                            "date": tr.get("date")[:10],  # Formato YYYY-MM-DD
                            "category": tr.get("category", "Geral"),
                            "type": "CREDIT" if (tr.get("amount") or 0) > 0 else "DEBIT"
                        }
                        # Salva
                        db.table("transactions").insert(dados).execute()
                        total_salvo += 1

        return f"Sincronização concluída! {total_salvo} novas transações importadas."

    except Exception as e:
        return f"Erro crítico na sincronização: {e}"