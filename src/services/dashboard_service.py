import pandas as pd
from datetime import datetime
from src.services.supabase_client import supabase
from src.services.investment_service import buscar_dados_resumidos_dashboard

# IDs de categorias que consideramos "Investimento"
CAT_IDS_INVESTIMENTO = [1, 2, 3]


def buscar_perfil_usuario(user_id):
    try:
        res = supabase.table("usuarios").select("nome, saldo_inicial").eq("id_usuario",
                                                                          str(user_id)).maybe_single().execute()
        return res.data if res.data else {"nome": "Usuário", "saldo_inicial": 0}
    except:
        return {"nome": "Usuário", "saldo_inicial": 0}


def buscar_resumo_financeiro(user_id):
    uid_str = str(user_id)

    resumo = {
        "saldo_final": 0.0, "detalhe_contas": [],
        "fatura_atual": 0.0, "a_pagar": 0.0,
        "entradas": 0.0, "saidas": 0.0, "balanco_liquido": 0.0,

        # INVESTIMENTOS
        "invest_saldo_atual": 0.0,
        "invest_custo_total": 0.0,
        "invest_lucro_reais": 0.0,
        "invest_lucro_pct": 0.0,
        "top_ativo_nome": "---",
        "top_ativo_lucro": 0.0,

        # SAÚDE FINANCEIRA (Score 0-100)
        "saude_score": 0.0,
        "saude_texto": "---",

        "cartao_inicio": None, "cartao_fim": None,
        "cartao_uso_pct": 0.0, "cartao_qtd": 0
    }

    try:
        # A. KPI GERAIS
        res_kpi = supabase.table("view_dashboard_kpis").select("*").eq("id_usuario", uid_str).maybe_single().execute()
        if res_kpi.data:
            r = res_kpi.data
            resumo["saldo_final"] = float(r.get("saldo_final") or 0)
            resumo["a_pagar"] = float(r.get("a_pagar") or 0)
            resumo["entradas"] = float(r.get("entradas") or 0)
            resumo["saidas"] = float(r.get("saidas") or 0)

        # B. FATURA DO CARTÃO
        res_ciclos = supabase.table("view_faturas_por_ciclo").select("*").eq("id_usuario", uid_str).execute()
        if res_ciclos.data:
            df_ciclos = pd.DataFrame(res_ciclos.data)
            df_ciclos['data_inicio'] = pd.to_datetime(df_ciclos['data_inicio'])
            df_ciclos['data_fim'] = pd.to_datetime(df_ciclos['data_fim'])

            hoje = datetime.now()
            mask_atual = (hoje >= df_ciclos['data_inicio']) & (hoje <= df_ciclos['data_fim'])
            fatura_atual_row = df_ciclos[mask_atual]

            if not fatura_atual_row.empty:
                row = fatura_atual_row.iloc[0]
                resumo["fatura_atual"] = float(row['valor_fatura'])
                resumo["cartao_uso_pct"] = float(row['uso_limite_percentual'])
                resumo["cartao_qtd"] = int(row['qtd_transacoes'])
                resumo["cartao_inicio"] = str(row['data_inicio'].date())
                resumo["cartao_fim"] = str(row['data_fim'].date())

        # C. CONTAS
        res_c = supabase.table("contas_bancarias").select("nome_banco, saldo_inicial").eq("id_usuario",
                                                                                          uid_str).execute()
        if res_c.data:
            resumo["detalhe_contas"] = [{"banco": c.get("nome_banco"), "saldo": c.get("saldo_inicial")} for c in
                                        res_c.data]

        # D. INVESTIMENTOS
        try:
            saldo, custo, lucro, top_nome, top_lucro = buscar_dados_resumidos_dashboard(uid_str)
            resumo["invest_saldo_atual"] = saldo
            resumo["invest_custo_total"] = custo
            resumo["invest_lucro_reais"] = lucro
            resumo["invest_lucro_pct"] = (lucro / custo * 100) if custo > 0 else 0.0
            resumo["top_ativo_nome"] = top_nome
            resumo["top_ativo_lucro"] = top_lucro
        except:
            pass

        resumo["balanco_liquido"] = resumo["saldo_final"] + resumo["invest_saldo_atual"]

        # ==============================================================================
        # E. CÁLCULO DO SCORE DE SAÚDE (LÓGICA SCORE BANCÁRIO)
        # ==============================================================================
        entradas = resumo["entradas"]
        gastos_brutos = resumo["saidas"] + resumo["fatura_atual"]

        # Abate aportes de investimento dos gastos
        saidas_investimento = 0.0
        try:
            res_b_inv = supabase.table("transacoes_bancarias").select("valor").eq("id_usuario", uid_str).eq("tipo",
                                                                                                            "saida").in_(
                "id_categoria", CAT_IDS_INVESTIMENTO).execute()
            if res_b_inv.data: saidas_investimento += sum(float(x['valor']) for x in res_b_inv.data)

            res_c_inv = supabase.table("transacoes_cartao_credito").select("valor").eq("id_usuario", uid_str).in_(
                "id_categoria", CAT_IDS_INVESTIMENTO).execute()
            if res_c_inv.data: saidas_investimento += sum(float(x['valor']) for x in res_c_inv.data)
        except:
            pass

        gastos_ajustados = max(0.0, gastos_brutos - saidas_investimento)

        # 1. Calcula % Comprometido da Renda
        percentual_gasto = 100.0
        if entradas > 0:
            percentual_gasto = (gastos_ajustados / entradas) * 100
        elif gastos_ajustados == 0:
            percentual_gasto = 0.0  # Não ganhou nada, mas não gastou nada

        # 2. Inverte para SCORE (Quanto maior, melhor)
        # Se gastou 30%, o Score é 70 (Ótimo). Se gastou 100%, Score é 0 (Ruim).
        score = max(0.0, 100.0 - percentual_gasto)

        # Define Texto Baseado no Score
        if score >= 60:  # Gastou menos de 40% (Excelente/Perfeita)
            texto = "Perfeita"
        elif score >= 40:  # Gastou entre 40% e 60% (Ótima)
            texto = "Ótima"
        elif score >= 20:  # Gastou entre 60% e 80% (Boa/Regular)
            texto = "Regular"
        elif score >= 10:  # Gastou entre 80% e 90% (Atenção)
            texto = "Atenção"
        else:  # Gastou mais de 90% (Crítico)
            texto = "Crítica"

        resumo["saude_score"] = score
        resumo["saude_texto"] = texto

    except Exception as e:
        print(f"Erro service: {e}")

    return resumo


def buscar_transacoes_graficos(user_id):
    # (Código dos gráficos permanece igual ao anterior)
    try:
        uid = str(user_id)
        res_b = supabase.table("transacoes_bancarias").select("*").eq("id_usuario", uid).eq("concluido", True).execute()
        res_c = supabase.table("transacoes_cartao_credito").select("*").eq("id_usuario", uid).execute()
        frames = []
        if res_b.data:
            df = pd.DataFrame(res_b.data)
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
            df['valor_grafico'] = df.apply(lambda x: x['valor'] if x['tipo'] == 'entrada' else -x['valor'], axis=1)
            frames.append(df[['data', 'valor_grafico', 'tipo', 'id_categoria', 'valor']])
        if res_c.data:
            df = pd.DataFrame(res_c.data)
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
            df['valor_grafico'] = -df['valor']
            df['tipo'] = 'cartao'
            frames.append(df[['data', 'valor_grafico', 'tipo', 'id_categoria', 'valor']])
        if not frames: return pd.DataFrame()
        df_final = pd.concat(frames, ignore_index=True)
        df_final['data'] = pd.to_datetime(df_final['data'])
        if df_final['data'].dt.tz is not None: df_final['data'] = df_final['data'].dt.tz_localize(None)
        if 'id_categoria' in df_final.columns:
            try:
                ids = df_final['id_categoria'].dropna().unique().tolist()
                if ids:
                    ids = [int(i) for i in ids]
                    res_cat = supabase.table("categorias").select("id_categoria, nome").in_("id_categoria",
                                                                                            ids).execute()
                    if res_cat.data:
                        df_c = pd.DataFrame(res_cat.data)
                        df_final = df_final.merge(df_c, on='id_categoria', how='left')
                        df_final.rename(columns={'nome': 'categoria'}, inplace=True)
            except:
                pass
        if 'categoria' not in df_final.columns: df_final['categoria'] = 'Geral'
        return df_final.sort_values('data')
    except:
        return pd.DataFrame()