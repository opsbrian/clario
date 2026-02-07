import pandas as pd
from src.services.supabase_client import supabase

# --- CONTAS BANCÁRIAS ---
def salvar_conta(user_id, banco, saldo):
    try:
        payload = {"id_usuario": user_id, "nome_banco": banco, "saldo_inicial": float(saldo)}
        supabase.table("contas_bancarias").insert(payload).execute()
        return True, "Conta salva com sucesso."
    except Exception as e:
        return False, str(e)

def listar_contas(user_id):
    try:
        resp = supabase.table("contas_bancarias").select("*").eq("id_usuario", user_id).execute()
        return pd.DataFrame(resp.data)
    except:
        return pd.DataFrame()

# --- CARTÕES DE CRÉDITO ---
def salvar_cartao_config(user_id, nome, limite, dia_fech, dia_venc):
    try:
        payload = {
            "id_usuario": user_id, "nome_cartao": nome,
            "limite": float(limite), "dia_fechamento": int(dia_fech), "dia_vencimento": int(dia_venc)
        }
        supabase.table("config_cartoes").insert(payload).execute()
        return True, "Cartão configurado com sucesso."
    except Exception as e:
        return False, str(e)

def listar_cartoes_config(user_id):
    try:
        resp = supabase.table("config_cartoes").select("*").eq("id_usuario", user_id).execute()
        return pd.DataFrame(resp.data)
    except:
        return pd.DataFrame()

# --- GENÉRICO ---
def excluir_config(tabela, id_item):
    try:
        supabase.table(tabela).delete().eq("id", id_item).execute()
        return True
    except:
        return False