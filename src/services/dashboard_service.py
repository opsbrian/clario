import pandas as pd
from datetime import datetime, timedelta
from src.services.supabase_client import supabase
from src.services.investment_service import buscar_dados_resumidos_dashboard

# IDs de categorias que consideramos "Investimento" (Aportes não são gastos!)
CAT_IDS_INVESTIMENTO = [1, 2, 3]


# --- FUNÇÃO AUXILIAR DE LIMPEZA ---
def limpar_valor_moeda(valor):
    """Converte qualquer formato (float, int, str 'R$ 1.000,00') para float python"""
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    try:
        # É string? Limpa caracteres de moeda
        v_str = str(valor).strip()
        v_str = v_str.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        return float(v_str)
    except:
        return 0.0


# ==============================================================================
# 1. PERFIL DO USUÁRIO
# ==============================================================================
def buscar_perfil_usuario(user_id):
    try:
        res = supabase.table("usuarios").select("nome, saldo_inicial").eq("id_usuario",
                                                                          str(user_id)).maybe_single().execute()
        return res.data if res.data else {"nome": "Usuário", "saldo_inicial": 0}
    except:
        return {"nome": "Usuário", "saldo_inicial": 0}


# ==============================================================================
# 2. RESUMO FINANCEIRO E SCORE (MOTOR PRINCIPAL)
# ==============================================================================
def buscar_resumo_financeiro(user_id):
    uid_str = str(user_id)

    # Estrutura padrão de retorno
    resumo = {
        "saldo_final": 0.0, "detalhe_contas": [],
        "fatura_atual": 0.0, "a_pagar": 0.0,
        "entradas": 0.0, "saidas": 0.0, "balanco_liquido": 0.0,
        "invest_saldo_atual": 0.0, "invest_custo_total": 0.0,
        "invest_lucro_reais": 0.0, "invest_lucro_pct": 0.0,
        "top_ativo_nome": "---", "top_ativo_lucro": 0.0,
        "saude_score": 0.0, "saude_texto": "Calculando...",
        "cartao_inicio": None, "cartao_fim": None,
        "cartao_uso_pct": 0.0, "cartao_qtd": 0
    }

    try:
        # --- A. BUSCA DADOS ATUAIS (SNAPSHOT) ---

        # 1. KPIs Básicos (View)
        res_kpi = supabase.table("view_dashboard_kpis").select("*").eq("id_usuario", uid_str).maybe_single().execute()
        if res_kpi.data:
            r = res_kpi.data
            resumo["saldo_final"] = float(r.get("saldo_final") or 0)
            resumo["a_pagar"] = float(r.get("a_pagar") or 0)
            resumo["entradas"] = float(r.get("entradas") or 0)  # Entradas do mês atual
            resumo["saidas"] = float(r.get("saidas") or 0)  # Saídas do mês atual

        # 2. Fatura Atual
        res_ciclos = supabase.table("view_faturas_por_ciclo").select("*").eq("id_usuario", uid_str).execute()
        if res_ciclos.data:
            df = pd.DataFrame(res_ciclos.data)
            if 'data_inicio' in df.columns:
                df['data_inicio'] = pd.to_datetime(df['data_inicio']).dt.tz_localize(None)
                df['data_fim'] = pd.to_datetime(df['data_fim']).dt.tz_localize(None)
                hoje = datetime.now()
                mask = (hoje >= df['data_inicio']) & (hoje <= df['data_fim'])
                atual = df[mask]
                if not atual.empty:
                    row = atual.iloc[0]
                    resumo["fatura_atual"] = float(row.get('valor_fatura', 0))
                    resumo["cartao_uso_pct"] = float(row.get('uso_limite_percentual', 0))
                    resumo["cartao_inicio"] = str(row['data_inicio'].date())
                    resumo["cartao_fim"] = str(row['data_fim'].date())

        # 3. Contas Bancárias
        res_c = supabase.table("contas_bancarias").select("nome_banco, saldo_inicial").eq("id_usuario",
                                                                                          uid_str).execute()
        if res_c.data:
            resumo["detalhe_contas"] = [{"banco": c.get("nome_banco"), "saldo": float(c.get("saldo_inicial", 0))} for c
                                        in res_c.data]

        # 4. Investimentos (Service Externo)
        try:
            saldo, custo, lucro, top_nome, top_lucro = buscar_dados_resumidos_dashboard(uid_str)
            resumo["invest_saldo_atual"] = float(saldo)
            resumo["invest_custo_total"] = float(custo)
            resumo["invest_lucro_reais"] = float(lucro)
            resumo["invest_lucro_pct"] = (lucro / custo * 100) if custo > 0 else 0.0
            resumo["top_ativo_nome"] = top_nome
            resumo["top_ativo_lucro"] = top_lucro
        except:
            pass

        # Patrimônio Total
        resumo["balanco_liquido"] = resumo["saldo_final"] + resumo["invest_saldo_atual"]

        # --- B. CÁLCULO DE SCORE DE LONGO PRAZO (12 MESES) ---

        # Define janela de tempo (Últimos 365 dias)
        data_limite = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        # Variáveis acumuladoras 12m
        ganhos_12m = 0.0
        gastos_brutos_12m = 0.0
        aportes_12m = 0.0

        # Busca Transações Bancárias (Últimos 12 meses)
        res_b_12m = supabase.table("transacoes_bancarias").select("valor, tipo, id_categoria") \
            .eq("id_usuario", uid_str).gte("data", data_limite).execute()

        if res_b_12m.data:
            for t in res_b_12m.data:
                val = limpar_valor_moeda(t.get('valor'))
                tipo = t.get('tipo')
                cat = t.get('id_categoria')

                if tipo == 'entrada':
                    ganhos_12m += val
                elif tipo == 'saida':
                    gastos_brutos_12m += val
                    # Se for saída para investimento, somamos aos aportes
                    if cat in CAT_IDS_INVESTIMENTO:
                        aportes_12m += val

        # Busca Transações Cartão (Últimos 12 meses) - Consideramos tudo gasto, exceto se categ. for invest
        res_c_12m = supabase.table("transacoes_cartao_credito").select("valor, id_categoria") \
            .eq("id_usuario", uid_str).gte("data", data_limite).execute()

        if res_c_12m.data:
            for t in res_c_12m.data:
                val = limpar_valor_moeda(t.get('valor'))
                cat = t.get('id_categoria')
                gastos_brutos_12m += val
                if cat in CAT_IDS_INVESTIMENTO:
                    aportes_12m += val

        # --- LÓGICA DO SCORE (0 a 100) ---
        # Gasto Real = Tudo que saiu MENOS o que foi para investimentos
        despesa_real_12m = max(0.0, gastos_brutos_12m - aportes_12m)
        patrimonio = resumo["balanco_liquido"]

        score = 50.0  # Começa neutro

        # 1. Taxa de Poupança Anual (Savings Rate)
        # Quanto da sua renda anual você reteve (seja em caixa ou investindo)?
        taxa_poupanca = 0.0
        if ganhos_12m > 0:
            sobra_anual = ganhos_12m - despesa_real_12m
            taxa_poupanca = sobra_anual / ganhos_12m  # Ex: 0.25 (25%)

            # Bonificação pela Taxa
            if taxa_poupanca >= 0.30:
                score += 30  # Poupa 30%+ (Excelência)
            elif taxa_poupanca >= 0.15:
                score += 20  # Poupa 15%+
            elif taxa_poupanca > 0:
                score += 10  # Fecha no azul
            else:
                score -= 10  # Gasta mais que ganha no ano

        # 2. Solidez Patrimonial (Net Worth Coverage)
        # Quantos meses você sobrevive com seu patrimônio atual baseada na média de gasto anual?
        media_gasto_mensal = despesa_real_12m / 12 if despesa_real_12m > 0 else 1.0
        meses_cobertura = patrimonio / media_gasto_mensal

        if meses_cobertura > 12:
            score += 20  # Liberdade Financeira (1 ano garantido)
        elif meses_cobertura > 6:
            score += 15  # Ótima reserva
        elif meses_cobertura > 3:
            score += 10  # Reserva de emergência ok
        elif meses_cobertura > 0:
            score += 5  # Tem algo guardado

        # 3. Penalidades Graves
        if patrimonio < 0:
            score = 20.0  # Dívida líquida

        # Ajuste Final (Clamp 0-100)
        score = max(0.0, min(100.0, score))

        # Texto Explicativo
        if score >= 90:
            txt = "Impecável"
        elif score >= 80:
            txt = "Excelente"
        elif score >= 70:
            txt = "Sólida"
        elif score >= 50:
            txt = "Equilibrada"
        elif score >= 30:
            txt = "Instável"
        else:
            txt = "Crítica"

        resumo["saude_score"] = int(score)
        resumo["saude_texto"] = txt

    except Exception as e:
        print(f"Erro Service Geral: {e}")

    return resumo


# ==============================================================================
# 3. GRÁFICOS (FLUXO DE CAIXA E COMPOSIÇÃO)
# ==============================================================================
def buscar_transacoes_graficos(user_id):
    try:
        uid = str(user_id)
        frames = []

        # 1. BANCÁRIAS
        res_b = supabase.table("transacoes_bancarias").select("*").eq("id_usuario", uid).execute()

        if res_b.data:
            df_b = pd.DataFrame(res_b.data)
            if 'valor' in df_b.columns:
                df_b['valor'] = df_b['valor'].apply(limpar_valor_moeda)
            else:
                df_b['valor'] = 0.0

            if 'tipo' not in df_b.columns: df_b['tipo'] = 'saida'
            df_b['valor_grafico'] = df_b.apply(lambda x: x['valor'] if x['tipo'] == 'entrada' else -x['valor'], axis=1)

            cols = [c for c in ['data', 'valor_grafico', 'tipo', 'id_categoria', 'valor'] if c in df_b.columns]
            frames.append(df_b[cols])

        # 2. CARTÃO
        res_c = supabase.table("transacoes_cartao_credito").select("*").eq("id_usuario", uid).execute()

        if res_c.data:
            df_c = pd.DataFrame(res_c.data)
            if 'valor' in df_c.columns:
                df_c['valor'] = df_c['valor'].apply(limpar_valor_moeda)
            else:
                df_c['valor'] = 0.0

            df_c['valor_grafico'] = -df_c['valor']  # Saída
            df_c['tipo'] = 'cartao'

            cols = [c for c in ['data', 'valor_grafico', 'tipo', 'id_categoria', 'valor'] if c in df_c.columns]
            frames.append(df_c[cols])

        if not frames:
            return pd.DataFrame()

        df_final = pd.concat(frames, ignore_index=True)

        if 'data' in df_final.columns:
            df_final['data'] = pd.to_datetime(df_final['data'])
            if df_final['data'].dt.tz is not None:
                df_final['data'] = df_final['data'].dt.tz_localize(None)

        # Categorias
        if 'id_categoria' in df_final.columns:
            ids = df_final['id_categoria'].dropna().unique().tolist()
            if ids:
                try:
                    ids = [int(i) for i in ids]
                    res_cat = supabase.table("categorias").select("id_categoria, nome").in_("id_categoria",
                                                                                            ids).execute()
                    if res_cat.data:
                        df_cat = pd.DataFrame(res_cat.data)
                        df_final = df_final.merge(df_cat, on='id_categoria', how='left')
                        df_final.rename(columns={'nome': 'categoria'}, inplace=True)
                except:
                    pass

        if 'categoria' not in df_final.columns:
            df_final['categoria'] = 'Geral'
        else:
            df_final['categoria'] = df_final['categoria'].fillna('Geral')

        return df_final.sort_values('data')

    except Exception as e:
        print(f"Erro Gráficos: {e}")
        return pd.DataFrame()