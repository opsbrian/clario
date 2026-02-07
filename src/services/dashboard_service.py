import streamlit as st
import pandas as pd
from src.services.supabase_client import supabase


# --- 1. BUSCAR NOME DO USUÁRIO ---
def buscar_perfil_usuario(user_id):
    """Busca o nome e sobrenome do usuário no banco de dados."""
    try:
        response = supabase.table("usuarios").select("nome, sobrenome").eq("id_usuario", user_id).single().execute()

        if response.data:
            return response.data
        return None
    except Exception as e:
        return None


# --- 2. BUSCAR RESUMO (SALDO + TRANSAÇÕES CONCLUÍDAS) ---
def buscar_resumo_financeiro(user_id):
    """Calcula o Saldo Real (Soma das Contas + Transações EFETIVADAS)."""
    try:
        # A. Busca Saldo Inicial
        resp_contas = supabase.table("contas_bancarias").select("saldo_inicial").eq("id_usuario", user_id).execute()
        saldo_inicial_acumulado = sum(
            [float(c['saldo_inicial']) for c in resp_contas.data]) if resp_contas.data else 0.0

        # B. Busca APENAS Transações Concluídas (concluido = TRUE)
        # Transações pendentes não afetam o saldo atual
        resp_trans = supabase.table("transacoes_bancarias").select("valor, tipo") \
            .eq("id_usuario", user_id) \
            .eq("concluido", True) \
            .execute()

        total_entradas = 0.0
        total_saidas = 0.0

        if resp_trans.data:
            for t in resp_trans.data:
                valor = float(t['valor'])
                if t['tipo'] == 'entrada':
                    total_entradas += valor
                else:
                    total_saidas += valor

        # C. Cálculo Final
        saldo_final = saldo_inicial_acumulado + total_entradas - total_saidas

        return {
            "saldo_final": saldo_final,
            "entradas": total_entradas,
            "saidas": total_saidas,
            "qtd_transacoes": len(resp_trans.data)
        }
    except Exception as e:
        print(f"Erro resumo: {e}")
        return {"saldo_final": 0.0, "entradas": 0.0, "saidas": 0.0, "qtd_transacoes": 0}


# --- 3. BUSCAR DADOS PARA GRÁFICOS ---
def buscar_transacoes_graficos(user_id):
    """Busca as transações completas para montar os gráficos."""
    try:
        response = supabase.table("transacoes_bancarias").select("*").eq("id_usuario", user_id).execute()

        df = pd.DataFrame(response.data)

        # Garante que a coluna de data seja temporal
        if not df.empty and 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'])

        return df
    except Exception as e:
        return pd.DataFrame()