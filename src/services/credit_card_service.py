import pandas as pd
from datetime import date, timedelta
import calendar
from src.services.supabase_client import supabase


# --- HELPERS ---
def add_months(source_date, months):
    """Adiciona meses a uma data (necessário para o parcelamento)"""
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def safe_date(year, month, day):
    last_day = calendar.monthrange(year, month)[1]
    safe_day = min(day, last_day)
    return date(year, month, safe_day)


# --- LEITURA E CONFIGURAÇÃO ---
def listar_cartoes(user_id):
    try:
        resp = supabase.table("config_cartoes").select("*").eq("id_usuario", user_id).execute()
        return resp.data if resp.data else []
    except:
        return []


def calcular_datas_fatura(mes_ref, ano_ref, dia_fechamento, dia_vencimento):
    if mes_ref == 1:
        mes_ant = 12;
        ano_ant = ano_ref - 1
    else:
        mes_ant = mes_ref - 1;
        ano_ant = ano_ref

    data_inicio = safe_date(ano_ant, mes_ant, int(dia_fechamento))
    data_fechamento_tecnico = safe_date(ano_ref, mes_ref, int(dia_fechamento))
    data_fim = data_fechamento_tecnico - timedelta(days=1)
    data_vencimento = safe_date(ano_ref, mes_ref, int(dia_vencimento))

    return data_inicio, data_fim, data_vencimento


def buscar_fatura_detalhada(user_id, card_id, mes_ref, ano_ref):
    try:
        card_resp = supabase.table("config_cartoes").select("dia_fechamento, dia_vencimento, limite").eq("id",
                                                                                                         card_id).single().execute()
        if not card_resp.data: return None

        card = card_resp.data
        dia_fech = card.get('dia_fechamento', 1)
        dia_venc = card.get('dia_vencimento', 10)
        limite = float(card.get('limite', 0))

        dt_ini, dt_fim, dt_venc = calcular_datas_fatura(mes_ref, ano_ref, dia_fech, dia_venc)

        resp_trans = supabase.table("transacoes_cartao_credito") \
            .select("*") \
            .eq("id_usuario", user_id) \
            .eq("id_cartao", card_id) \
            .gte("data", str(dt_ini)) \
            .lte("data", str(dt_fim)) \
            .order("data", desc=True) \
            .execute()

        df = pd.DataFrame(resp_trans.data)

        valor_fatura = 0.0
        itens = []

        if not df.empty:
            df['data'] = pd.to_datetime(df['data']).dt.date
            valor_fatura = df['valor'].sum()
            itens = df.to_dict('records')

        hoje = date.today()
        status = "Aberta"
        if hoje > dt_fim: status = "Fechada"
        if hoje > dt_venc and valor_fatura > 0: status = "Atrasada"

        return {
            "fatura_total": valor_fatura,
            "limite_total": limite,
            "limite_disponivel": limite - valor_fatura,
            "status": status,
            "vencimento": dt_venc,
            "fechamento": dt_fim,
            "itens": itens,
            "periodo": f"{dt_ini.strftime('%d/%m')} a {dt_fim.strftime('%d/%m')}"
        }
    except Exception as e:
        return None


# --- GRAVAÇÃO (MOVIDO DE TRANSACTION_SERVICE) ---
def salvar_compra_cartao(user_id, id_cartao, id_categoria, data_compra, descricao, valor_total, parcelas, devedor=None):
    try:
        qtd_parcelas = int(parcelas)
        if qtd_parcelas < 1: qtd_parcelas = 1

        valor_parcela = float(valor_total) / qtd_parcelas

        for i in range(qtd_parcelas):
            data_lancamento = add_months(data_compra, i)

            payload = {
                "id_usuario": user_id,
                "id_cartao": id_cartao,
                "id_categoria": id_categoria,
                "data": str(data_lancamento),
                "descricao": descricao,
                "valor": valor_parcela,
                "valor_total": float(valor_total),
                "parcelas": qtd_parcelas,
                "parcela_atual": i + 1,
                "devedor": devedor
            }
            supabase.table("transacoes_cartao_credito").insert(payload).execute()

        return True, f"Compra registrada em {qtd_parcelas}x com sucesso!"
    except Exception as e:
        return False, str(e)