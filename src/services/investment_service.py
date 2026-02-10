import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, datetime
import requests
from src.services.supabase_client import supabase


# ==========================================
# 1. FUNÇÕES DE ESCRITA (SALVAR)
# ==========================================

def salvar_investimento(user_id, data_op, ativo, cat_id, preco_un, qtd, taxa=None, indexador=None):
    """
    Salva o investimento no Supabase.
    """
    try:
        qtd = float(qtd)
        preco_un = float(preco_un)
        valor_total = preco_un * qtd

        # Garante que o ativo esteja limpo e maiúsculo
        ativo_clean = ativo.strip().upper()

        dados = {
            "id_usuario": user_id,
            "data": data_op.isoformat(),
            "descricao": ativo_clean,
            "id_categoria": int(cat_id),
            "valor_investido": valor_total,
            "quantidade": qtd,
            "taxa": float(taxa) if taxa is not None else None,
            "indexador": indexador if indexador else None
        }

        supabase.table("investimento").insert(dados).execute()
        return True, "Investimento registrado com sucesso!"
    except Exception as e:
        return False, f"Erro ao salvar no banco: {str(e)}"


# ==========================================
# 2. FUNÇÕES DE LEITURA (PORTFOLIO ROBUSTO)
# ==========================================

def buscar_portfolio_real(user_id):
    """
    Calcula o portfólio atual.
    CORREÇÃO: Tratamento robusto para falhas do Yahoo Finance e Tickers com .SA
    """
    try:
        # 1. Busca dados no Supabase
        res = supabase.table("investimento").select("*").eq("id_usuario", user_id).execute()
        if not res.data:
            return pd.DataFrame()

        df = pd.DataFrame(res.data)

        # 2. Agrupa por Ativo
        portfolio = df.groupby(['descricao', 'id_categoria']).agg({
            'quantidade': 'sum',
            'valor_investido': 'sum'
        }).reset_index()

        # Filtra ativos zerados
        portfolio = portfolio[portfolio['quantidade'] > 0.000001].copy()

        if portfolio.empty:
            return pd.DataFrame()

        # 3. Separação de Estratégia
        df_mercado = portfolio[portfolio['id_categoria'].isin([1, 2])].copy()

        # --- PROCESSAMENTO DE PREÇOS (YAHOO) ---
        mapa_precos = {}

        if not df_mercado.empty:
            tickers_yahoo = []
            mapa_ticker_original = {}

            for ativo in df_mercado['descricao'].unique():
                cat = df_mercado[df_mercado['descricao'] == ativo]['id_categoria'].iloc[0]

                sym_yf = ativo
                # Lógica de Sufixo
                if cat == 2:  # Cripto
                    if not ativo.endswith("-USD"): sym_yf = f"{ativo}-USD"
                elif cat == 1:  # Ações/FIIs BR
                    # Se NÃO tem ponto, adiciona .SA
                    # Se JÁ tem (ex: HGLG11.SA), mantém como está
                    if "." not in ativo:
                        sym_yf = f"{ativo}.SA"

                tickers_yahoo.append(sym_yf)
                mapa_ticker_original[sym_yf] = ativo

                # Adiciona Dólar
            tickers_yahoo.append("USDBRL=X")

            # Download Seguro
            try:
                # auto_adjust=True ajuda a pegar o preço real ajustado
                dados_mercado = yf.download(tickers_yahoo, period="1d", progress=False, auto_adjust=True)['Close']

                # Normaliza para Dicionário
                vals = {}
                if isinstance(dados_mercado, pd.Series):
                    # Apenas 1 ativo retornado
                    vals = {dados_mercado.name: dados_mercado.iloc[-1]}
                elif isinstance(dados_mercado, pd.DataFrame) and not dados_mercado.empty:
                    # Vários ativos: pega a última linha válida
                    # ffill garante que se hoje for feriado/fds, pega o último dia útil
                    dados_filled = dados_mercado.ffill()
                    vals = dados_filled.iloc[-1].to_dict()

                # Cotação Dólar
                usd_brl = vals.get("USDBRL=X", 5.50)
                if pd.isna(usd_brl): usd_brl = 5.50

                # Preenche Mapa
                for sym_yf, val_ativo in vals.items():
                    if sym_yf == "USDBRL=X": continue

                    ativo_orig = mapa_ticker_original.get(sym_yf, sym_yf)

                    # Se veio NaN do Yahoo, ignoramos aqui para cair no fallback depois
                    if pd.isna(val_ativo) or val_ativo == 0:
                        continue

                    # Conversão Dólar se necessário
                    if sym_yf.endswith("-USD") or (cat == 1 and ".SA" not in sym_yf and "-USD" not in sym_yf):
                        # Lógica simplificada: Cripto sempre converte. Ações sem .SA assumimos EUA.
                        # Se o seu ticker for "AAPL" (EUA), converte. Se for "HGLG11.SA", não.
                        if cat == 2 or ("." not in sym_yf):
                            mapa_precos[ativo_orig] = val_ativo * usd_brl
                        else:
                            mapa_precos[ativo_orig] = val_ativo
                    else:
                        mapa_precos[ativo_orig] = val_ativo

            except Exception as e:
                print(f"Erro YFinance: {e}")

        # --- APLICAÇÃO DOS PREÇOS COM FALLBACK ---

        def get_preco_atual(row):
            ativo = row['descricao']
            # Custo Médio (Plano B)
            custo_medio = row['valor_investido'] / row['quantidade'] if row['quantidade'] > 0 else 0

            # Se for Renda Fixa (3), o preço é o custo (simplificado)
            if row['id_categoria'] == 3:
                return custo_medio

            # Se for Renda Variável, tenta pegar do mapa
            preco_mercado = mapa_precos.get(ativo)

            # SE O PREÇO VIER ZERO OU NONE (Falha Yahoo), USA O CUSTO MÉDIO
            # Assim nunca mostra R$ 0,00 e Retorno NaN%
            if preco_mercado is None or preco_mercado == 0 or pd.isna(preco_mercado):
                return custo_medio

            return preco_mercado

        portfolio['Valor Hoje BRL'] = portfolio.apply(get_preco_atual, axis=1)

        # --- CÁLCULOS FINAIS ---
        portfolio['Total Atual BRL'] = portfolio['quantidade'] * portfolio['Valor Hoje BRL']
        portfolio['Lucro/Prejuízo BRL'] = portfolio['Total Atual BRL'] - portfolio['valor_investido']

        portfolio['Rentabilidade %'] = portfolio.apply(
            lambda x: (x['Lucro/Prejuízo BRL'] / x['valor_investido'] * 100) if x['valor_investido'] > 0 else 0,
            axis=1
        )

        portfolio.rename(columns={
            'descricao': 'Ativo',
            'quantidade': 'Quantidade',
            'valor_investido': 'Custo Total BRL'
        }, inplace=True)

        portfolio['Tipo'] = portfolio['id_categoria'].map({
            1: "Renda Variável",
            2: "Cripto",
            3: "Renda Fixa"
        })

        cols = ['Ativo', 'Tipo', 'id_categoria', 'Quantidade', 'Custo Total BRL',
                'Valor Hoje BRL', 'Total Atual BRL', 'Lucro/Prejuízo BRL', 'Rentabilidade %']

        return portfolio[cols].sort_values('Total Atual BRL', ascending=False)

    except Exception as e:
        print(f"Erro crítico no portfolio: {e}")
        return pd.DataFrame()


# ==========================================
# 3. FUNÇÕES AUXILIARES
# ==========================================

def pesquisar_ticker_yahoo(query):
    if not query or len(query) < 2: return []
    try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        headers = {'User-Agent': 'Mozilla/5.0'}
        params = {'q': query, 'quotesCount': 6, 'newsCount': 0}
        r = requests.get(url, params=params, headers=headers, timeout=3)
        data = r.json()
        sugestoes = []
        if 'quotes' in data:
            for q in data['quotes']:
                if q.get('quoteType') in ['EQUITY', 'ETF', 'CRYPTOCURRENCY', 'MUTUALFUND']:
                    s = q.get('symbol')
                    n = q.get('shortname') or q.get('longname') or s
                    e = q.get('exchange', 'N/A')
                    sugestoes.append(f"{s} | {n} ({e})")
        return sugestoes
    except:
        return []


def buscar_sugestoes_yahoo(termo):
    return pesquisar_ticker_yahoo(termo)


@st.cache_data(ttl=3600)
def buscar_evolucao_patrimonio(user_id):
    try:
        res = supabase.table("investimento").select("data, valor_investido").eq("id_usuario", user_id).order(
            "data").execute()
        if not res.data: return pd.DataFrame()

        df = pd.DataFrame(res.data)
        df['data'] = pd.to_datetime(df['data'])
        df_evo = df.groupby('data')['valor_investido'].sum().reset_index()
        df_evo['Patrimônio'] = df_evo['valor_investido'].cumsum()
        df_evo.rename(columns={'data': 'Data'}, inplace=True)
        return df_evo[['Data', 'Patrimônio']]
    except:
        return pd.DataFrame()