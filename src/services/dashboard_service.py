import pandas as pd
import yfinance as yf
from datetime import datetime
from src.services.supabase_client import supabase


# ==========================================
# 1. PERFIL
# ==========================================
def buscar_perfil_usuario(user_id):
    try:
        res = supabase.table("usuarios").select("nome").eq("id_usuario", str(user_id)).maybe_single().execute()
        return res.data if res.data else {"nome": "Usuário"}
    except:
        return {"nome": "Usuário"}


# ==========================================
# 2. RESUMO FINANCEIRO (INTEGRADO COM VIEW DE CICLOS)
# ==========================================
def buscar_resumo_financeiro(user_id):
    uid_str = str(user_id)

    resumo = {
        "saldo_final": 0.0, "detalhe_contas": [],
        "fatura_atual": 0.0, "a_pagar": 0.0,
        "entradas": 0.0, "saidas": 0.0, "balanco_liquido": 0.0,
        "total_investido": 0.0, "rentabilidade_total": 0.0, "lucro_prejuizo_total": 0.0,
        "top_ativo_nome": "---", "top_ativo_lucro": 0.0,
        "saude_ratio": 0.0,
        "cartao_inicio": None, "cartao_fim": None,
        "cartao_uso_pct": 0.0, "cartao_qtd": 0
    }

    try:
        # A. SALDO BANCÁRIO (View Geral)
        res_kpi = supabase.table("view_dashboard_kpis").select("*").eq("id_usuario", uid_str).maybe_single().execute()
        if res_kpi.data:
            r = res_kpi.data
            resumo["saldo_final"] = float(r.get("saldo_final") or 0)
            resumo["balanco_liquido"] = float(r.get("balanco_liquido") or 0)
            resumo["a_pagar"] = float(r.get("a_pagar") or 0)
            resumo["entradas"] = float(r.get("entradas") or 0)
            resumo["saidas"] = float(r.get("saidas") or 0)

        # B. FATURA DO CARTÃO (Busca TODOS os ciclos e filtra o ATUAL no Python)
        res_ciclos = supabase.table("view_faturas_por_ciclo").select("*").eq("id_usuario", uid_str).execute()

        if res_ciclos.data:
            df_ciclos = pd.DataFrame(res_ciclos.data)
            df_ciclos['data_inicio'] = pd.to_datetime(df_ciclos['data_inicio'])
            df_ciclos['data_fim'] = pd.to_datetime(df_ciclos['data_fim'])

            # DATA HOJE: Aqui definimos o que é "Atual".
            # Se seu PC está com data certa, usa datetime.now().
            hoje = datetime.now()

            # Filtra a linha onde HOJE está entre Inicio e Fim
            mask_atual = (hoje >= df_ciclos['data_inicio']) & (hoje <= df_ciclos['data_fim'])
            fatura_atual_row = df_ciclos[mask_atual]

            # Se encontrou o ciclo vigente
            if not fatura_atual_row.empty:
                row = fatura_atual_row.iloc[0]
                resumo["fatura_atual"] = float(row['valor_fatura'])
                resumo["cartao_uso_pct"] = float(row['uso_limite_percentual'])
                resumo["cartao_qtd"] = int(row['qtd_transacoes'])
                resumo["cartao_inicio"] = str(row['data_inicio'].date())
                resumo["cartao_fim"] = str(row['data_fim'].date())
            else:
                # Se hoje não caiu em nenhum ciclo (ex: dados só no futuro), pega o mais próximo
                # Opcional: Pegar o primeiro ciclo futuro ou mostrar zero
                pass

            # Atualiza Saúde
            gastos_totais = resumo["saidas"] + resumo["fatura_atual"]
            if resumo["entradas"] > 0:
                resumo["saude_ratio"] = (gastos_totais / resumo["entradas"]) * 100

        # C. DETALHE CONTAS
        res_c = supabase.table("contas_bancarias").select("nome_banco, saldo_inicial").eq("id_usuario",
                                                                                          uid_str).execute()
        if res_c.data:
            resumo["detalhe_contas"] = [{"banco": c.get("nome_banco"), "saldo": c.get("saldo_inicial")} for c in
                                        res_c.data]

        # D. INVESTIMENTOS
        custo_investido = float(res_kpi.data.get("invest_custo_total") or 0) if res_kpi.data else 0
        res_inv = supabase.table("investimento").select("descricao, quantidade, valor_investido").eq("id_usuario",
                                                                                                     uid_str).execute()
        if res_inv.data:
            df_inv = pd.DataFrame(res_inv.data)
            df_inv['valor_investido'] = pd.to_numeric(df_inv['valor_investido'], errors='coerce').fillna(0)
            df_inv['quantidade'] = pd.to_numeric(df_inv['quantidade'], errors='coerce').fillna(0)

            carteira = df_inv.groupby('descricao').agg({'quantidade': 'sum', 'valor_investido': 'sum'}).reset_index()

            patrimonio = 0.0
            melhor_lucro = -float('inf')
            top_ativo = "---"

            try:
                tickers = carteira['descricao'].unique().tolist()
                cotacoes = {}
                if tickers:
                    q_tickers = [t + ".SA" if len(t) == 5 and t.isalpha() else t for t in tickers]
                    dl = yf.download(q_tickers, period="1d", progress=False)['Close']
                    if not dl.empty:
                        for i, t in enumerate(tickers):
                            try:
                                val = dl.iloc[-1].item() if len(tickers) == 1 else dl[q_tickers[i]].iloc[-1]
                                cotacoes[t] = val
                            except:
                                pass
            except:
                pass

            for _, row in carteira.iterrows():
                ativo = row['descricao']
                qtd = float(row['quantidade'])
                custo = float(row['valor_investido'])
                pm = custo / qtd if qtd > 0 else 0
                preco = cotacoes.get(ativo, pm)
                if pd.isna(preco): preco = pm

                val_pos = preco * qtd
                patrimonio += val_pos
                lucro = val_pos - custo
                if lucro > melhor_lucro:
                    melhor_lucro = lucro
                    top_ativo = ativo

            resumo["total_investido"] = patrimonio
            resumo["lucro_prejuizo_total"] = patrimonio - custo_investido
            if custo_investido > 0:
                resumo["rentabilidade_total"] = ((patrimonio - custo_investido) / custo_investido) * 100
            if top_ativo != "---":
                resumo["top_ativo_nome"] = top_ativo
                resumo["top_ativo_lucro"] = melhor_lucro

    except Exception as e:
        print(f"Erro service: {e}")

    return resumo


# ==========================================
# 3. GRÁFICOS
# ==========================================
def buscar_transacoes_graficos(user_id):
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