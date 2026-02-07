import streamlit as st
from supabase import create_client, Client
from pluggy_sdk import PluggyClient

# ... (Configurações de API Key iguais ao anterior) ...

# IDs das suas contas (Extraídos dos dados que você mandou)
NUBANK_ITEM_ID = st.secrets["pluggy"]["item_id_nubank"]
CONTA_CORRENTE_ID = "4703b762-fd42-4537-8df5-c7c32d9b41b7"
CARTAO_CREDITO_ID = "5674612b-ff61-4362-9b2f-414cd23c17b5"


def sync_nubank_transactions():
    """
    Busca transações especificamente do seu Item Nubank
    """
    st.info(f"Conectando ao Nubank (Item: {NUBANK_ITEM_ID[:8]}...)...")

    # Busca transações de TODAS as contas desse Item
    try:
        # Nota: Na prática, você pode precisar iterar pelas contas (accounts)
        # transactions = pluggy.fetch_transactions(account_id=CONTA_CORRENTE_ID)
        # Mas muitas vezes buscar pelo Item traz tudo. Vamos assumir busca por conta para precisão:

        all_transactions = []

        # 1. Busca Conta Corrente
        tr_conta = pluggy.fetch_transactions(CONTA_CORRENTE_ID)
        all_transactions.extend(tr_conta.results)

        # 2. Busca Cartão de Crédito
        tr_cartao = pluggy.fetch_transactions(CARTAO_CREDITO_ID)
        all_transactions.extend(tr_cartao.results)

        transactions_to_insert = []

        for tr in all_transactions:
            # Lógica de Sinais e Tipos
            valor = tr.amount * -1 if tr.type == 'DEBIT' else tr.amount

            # Define o tipo baseado na conta de origem
            tipo = 'pix'  # Default genérico
            if tr.account_id == CARTAO_CREDITO_ID:
                tipo = 'credit_card'
            elif tr.category and 'Invest' in tr.category:
                tipo = 'investment'

            transactions_to_insert.append({
                "description": tr.description,
                "amount": valor,
                "date": tr.date[:10],
                "transaction_type": tipo,
                "status": "completed",
                "metadata": {
                    "pluggy_id": tr.id,
                    "account_id": tr.account_id,  # Para saber se veio da conta ou cartão
                    "original_category": tr.category
                }
            })

        # Insere no Supabase
        if transactions_to_insert:
            data = supabase.table("transactions").upsert(
                transactions_to_insert,
                on_conflict="metadata->>pluggy_id"
            ).execute()
            st.success(f"{len(transactions_to_insert)} transações do Nubank sincronizadas!")

    except Exception as e:
        st.error(f"Erro na sincronização: {e}")