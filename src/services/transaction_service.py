import streamlit as st
import pandas as pd
from datetime import date
import calendar
from src.services.supabase_client import supabase


# --- SELETORES ---
def listar_bancos_selecao(user_id):
    try:
        resp = supabase.table("contas_bancarias").select("id, nome_banco").eq("id_usuario", user_id).execute()
        return [{'id_bank': i['id'], 'nome_banco': i['nome_banco']} for i in resp.data] if resp.data else []
    except:
        return []


def listar_categorias_selecao(tipo_filtro=None):
    try:
        resp = supabase.table("categorias").select("*").order("id_categoria").execute()
        todas = resp.data if resp.data else []
        if not todas: return []
        lista_filtrada = []
        filtro = str(tipo_filtro).lower().strip() if tipo_filtro else None
        for c in todas:
            tipo_db = str(c.get('tipo', '')).strip().lower()
            if filtro == 'receita':
                if tipo_db in ['receita', 'investimento']: lista_filtrada.append(c)
            elif filtro == 'despesa':
                if tipo_db in ['despesa', 'investimento']: lista_filtrada.append(c)
            elif filtro == 'investimento':
                if tipo_db == 'investimento': lista_filtrada.append(c)
            else:
                lista_filtrada.append(c)
        return sorted(lista_filtrada, key=lambda x: x['descricao'])
    except:
        return []


# --- HELPERS ---
def add_months(source_date, months):
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def confirmar_pagamento(id_transacao, data_real):
    try:
        supabase.table("transacoes_bancarias").update({
            "concluido": True, "data": str(data_real)
        }).eq("id_trans_bank", id_transacao).execute()
        return True
    except:
        return False


# --- SAVE CONTA CORRENTE ---
def salvar_transacao(user_id, id_bank, id_categoria, tipo, data_ref, descricao, valor, devedor=None,
                     is_emprestimo=False, parcelas=1, taxa_juros=0):
    try:
        payload = {"id_usuario": user_id, "id_bank": id_bank, "id_categoria": id_categoria, "tipo": tipo,
                   "data": str(data_ref), "descricao": descricao, "valor": float(valor), "devedor": devedor,
                   "concluido": True}
        supabase.table("transacoes_bancarias").insert(payload).execute()

        if is_emprestimo and parcelas > 0:
            valor_recebido = float(valor)
            total_divida = valor_recebido * (1 + (taxa_juros / 100))
            valor_parcela = total_divida / int(parcelas)
            for i in range(parcelas):
                data_pgto = add_months(data_ref, i + 1)
                payload_parcela = {"id_usuario": user_id, "id_bank": id_bank, "id_categoria": id_categoria,
                                   "tipo": "saida", "data": str(data_pgto),
                                   "descricao": f"Pgto Empréstimo ({i + 1}/{parcelas}) - {descricao}",
                                   "valor": valor_parcela, "devedor": devedor, "concluido": False}
                supabase.table("transacoes_bancarias").insert(payload_parcela).execute()
            return True, f"Empréstimo registrado."
        return True, "Transação salva."
    except Exception as e:
        return False, str(e)


# --- SAVE INVESTIMENTO ---
def salvar_investimento(user_id, id_bank, id_categoria, data, descricao, valor_investido, quantidade,
                        rentabilidade=None):
    try:
        payload = {"id_usuario": user_id, "id_bank": id_bank, "id_categoria": id_categoria, "data": str(data),
                   "descricao": descricao, "valor_investido": float(valor_investido), "quantidade": float(quantidade),
                   "rentabilidade": float(rentabilidade) if rentabilidade else None}
        supabase.table("investimento").insert(payload).execute()
        return True, "Sucesso"
    except Exception as e:
        return False, str(e)


# --- LISTAGEM UNIFICADA (Dashboard/Extrato) ---
def listar_transacoes_unificadas(user_id):
    try:
        resp_cats = supabase.table("categorias").select("id_categoria, icon, descricao, tipo").execute()
        mapa_cats = {c['id_categoria']: c for c in resp_cats.data} if resp_cats.data else {}

        r1 = supabase.table("transacoes_bancarias").select("*").eq("id_usuario", user_id).order("data",
                                                                                                desc=True).limit(
            1000).execute()
        df1 = pd.DataFrame(r1.data)
        if not df1.empty:
            df1['origem'] = 'Conta';
            df1['detalhe'] = 'Transação'
            if 'concluido' not in df1.columns: df1['concluido'] = True

        r2 = supabase.table("transacoes_cartao_credito").select("*").eq("id_usuario", user_id).order("data",
                                                                                                     desc=True).limit(
            1000).execute()
        df2 = pd.DataFrame(r2.data)
        if not df2.empty:
            df2['tipo'] = 'saida';
            df2['origem'] = 'Cartão';
            df2['valor'] = df2['valor_total']
            df2['detalhe'] = df2.apply(lambda x: f"{x.get('parcelas', 1)}x", axis=1)
            df2['concluido'] = True

        r3 = supabase.table("investimento").select("*").eq("id_usuario", user_id).order("data", desc=True).limit(
            1000).execute()
        df3 = pd.DataFrame(r3.data)
        if not df3.empty:
            df3 = df3.rename(columns={'valor_investido': 'valor'});
            df3['tipo'] = 'saida';
            df3['origem'] = 'Investimento';
            df3['detalhe'] = 'Aporte'
            df3['concluido'] = True

        dfs = [d for d in [df1, df2, df3] if not d.empty]
        if dfs:
            final = pd.concat(dfs, ignore_index=True)
            if 'data' in final.columns: final['data'] = pd.to_datetime(final['data'])

            def get_cat_info(id_cat):
                cat = mapa_cats.get(id_cat)
                if not cat: return 'receipt_long', 'outros'
                return cat['icon'], str(cat.get('tipo', '')).lower()

            final[['icon_db', 'cat_tipo']] = final['id_categoria'].apply(lambda x: pd.Series(get_cat_info(x)))
            final['concluido'] = final['concluido'].fillna(True)
            return final.sort_values('data', ascending=False)
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()


def excluir_item_generico(id_item, tabela, col_id):
    try:
        supabase.table(tabela).delete().eq(col_id, id_item).execute()
        return True
    except:
        return False