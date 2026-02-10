import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, datetime
import requests
import numpy as np
from src.services.supabase_client import supabase
from src.services.market_data_service import buscar_historico_cdi_diario, buscar_indicadores_economicos

# ==========================================
# 0. AJUSTES MANUAIS (ATIVOS SEM API)
# ==========================================
PRECOS_MANUAIS = {
    "SNLG11": 1.24,
    "SNLG11.SA": 1.24,
    "SNEL11": 1.24
}

TICKER_MAPPING = {
    "FB": "META"
}


# ==========================================
# 1. FUNÇÕES DE ESCRITA (SALVAR)
# ==========================================
def salvar_investimento(user_id, data_op, ativo, cat_id, preco_un, qtd, taxa=None, indexador=None):
    try:
        if int(cat_id) == 3:
            qtd = 1.0
            valor_total = float(preco_un)
        else:
            qtd = float(qtd)
            preco_un = float(preco_un)
            valor_total = preco_un * qtd

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
        return True, "Sucesso"
    except Exception as e:
        return False, str(e)


# ==========================================
# 2. MOTOR DE CÁLCULO RENDA FIXA
# ==========================================
def calcular_valor_presente_inteligente(row, df_cdi_historico, indicadores_atuais):
    try:
        if row['id_categoria'] != 3: return 0.0
        data_aporte = pd.to_datetime(row['data']).date()
        hoje = date.today()
        if data_aporte >= hoje: return float(row['valor_investido'])

        val_investido = float(row['valor_investido'])
        taxa_pct = float(row['taxa']) if pd.notnull(row['taxa']) else 100.0
        indexador = row['indexador'] if pd.notnull(row['indexador']) else 'CDI'

        if indexador in ['CDI', 'SELIC']:
            if df_cdi_historico.empty:
                dias_uteis = int((hoje - data_aporte).days * 0.69)
                taxa_aa = indicadores_atuais.get('CDI', 0.1115) * (taxa_pct / 100.0)
                return val_investido * ((1 + taxa_aa) ** (dias_uteis / 252.0))

            mask = (df_cdi_historico['data'] >= data_aporte) & (df_cdi_historico['data'] < hoje)
            df_periodo = df_cdi_historico.loc[mask].copy()
            if df_periodo.empty: return val_investido

            fator_usuario = taxa_pct / 100.0
            df_periodo['fator_ajustado'] = 1 + (df_periodo['valor'] * fator_usuario)
            return val_investido * df_periodo['fator_ajustado'].prod()

        elif indexador == 'PREFIXADO':
            dias_corridos = (hoje - data_aporte).days
            dias_uteis_est = int(dias_corridos * 0.6849)
            taxa_aa = taxa_pct / 100.0
            return val_investido * ((1 + taxa_aa) ** (dias_uteis_est / 252.0))

        elif indexador == 'IPCA':
            dias_corridos = (hoje - data_aporte).days
            ipca_aa = indicadores_atuais.get('IPCA', 0.045)
            taxa_fixa_aa = taxa_pct / 100.0
            taxa_combinada = ((1 + ipca_aa) * (1 + taxa_fixa_aa)) - 1
            return val_investido * ((1 + taxa_combinada) ** (dias_corridos / 365.0))

        return val_investido
    except:
        return float(row['valor_investido'])


# ==========================================
# 3. BUSCA DE PORTFOLIO (CORREÇÃO SOL-USD)
# ==========================================
def buscar_portfolio_real(user_id):
    try:
        # 1. Busca Dados
        res = supabase.table("investimento").select("*").eq("id_usuario", user_id).execute()
        if not res.data: return pd.DataFrame()
        df = pd.DataFrame(res.data)

        # 2. Renda Fixa
        df_cdi_hist = buscar_historico_cdi_diario()
        indicadores_atuais = buscar_indicadores_economicos()
        df['valor_projetado_fixa'] = df.apply(
            lambda r: calcular_valor_presente_inteligente(r, df_cdi_hist, indicadores_atuais), axis=1)

        # 3. Agrupamento
        portfolio = df.groupby(['descricao', 'id_categoria']).agg({
            'quantidade': 'sum', 'valor_investido': 'sum', 'valor_projetado_fixa': 'sum'
        }).reset_index()
        portfolio = portfolio[portfolio['quantidade'] > 0.000001].copy()

        # 4. Renda Variável
        df_mercado = portfolio[portfolio['id_categoria'].isin([1, 2])].copy()
        mapa_precos = {}

        if not df_mercado.empty:

            # --- PREÇOS MANUAIS (Prioridade 1) ---
            for ativo_man in PRECOS_MANUAIS:
                mapa_precos[ativo_man] = PRECOS_MANUAIS[ativo_man]

            # --- DÓLAR (Prioridade 2) ---
            try:
                usd_obj = yf.Ticker("USDBRL=X")
                usd_hist = usd_obj.history(period="1d")
                if not usd_hist.empty:
                    usd_rate = usd_hist['Close'].iloc[-1]
                else:
                    usd_rate = 5.80
            except:
                usd_rate = 5.80

            # --- PREPARAÇÃO INTELIGENTE DE TICKERS ---
            tickers_api = []
            mapa_ticker_banco_x_yahoo = {}

            for ativo_banco in df_mercado['descricao'].unique():
                # Se já tem preço manual, pula
                if ativo_banco in mapa_precos: continue

                ativo_limpo = ativo_banco.strip().upper()
                ativo_corrigido = TICKER_MAPPING.get(ativo_limpo, ativo_limpo)

                cat = df_mercado[df_mercado['descricao'] == ativo_banco]['id_categoria'].iloc[0]
                sym_yahoo = ativo_corrigido

                # --- CORREÇÃO DO ERRO SOL-USD ---
                # Se terminar em -USD, é Cripto/Exterior, NÃO adiciona .SA
                if ativo_corrigido.endswith("-USD"):
                    sym_yahoo = ativo_corrigido
                # Se terminar em .SA, já está certo
                elif ativo_corrigido.endswith(".SA"):
                    sym_yahoo = ativo_corrigido
                # Se for Cat 2 (Cripto), adiciona -USD
                elif cat == 2:
                    sym_yahoo = f"{ativo_corrigido}-USD"
                # Se for Cat 1 (Ação) e não tem ponto, adiciona .SA
                elif cat == 1:
                    sym_yahoo = f"{ativo_corrigido}.SA"

                tickers_api.append(sym_yahoo)
                mapa_ticker_banco_x_yahoo[sym_yahoo] = ativo_banco

            # --- BUSCA NO YAHOO ---
            cotacoes_temp = {}
            if tickers_api:
                # Tentativa 1: Bulk
                try:
                    dados = yf.download(tickers_api, period="2d", progress=False, auto_adjust=True, group_by='ticker')
                    for sym in tickers_api:
                        try:
                            if len(tickers_api) == 1:
                                series = dados['Close']
                            else:
                                if sym in dados:
                                    series = dados[sym]['Close']
                                else:
                                    continue

                            val = series.ffill().iloc[-1]
                            if pd.notnull(val) and val > 0:
                                cotacoes_temp[sym] = val
                        except:
                            pass
                except:
                    pass

                # Tentativa 2: Individual (Repescagem)
                for sym in tickers_api:
                    if sym not in cotacoes_temp:
                        try:
                            single = yf.Ticker(sym).history(period="5d")
                            if not single.empty:
                                val = single['Close'].iloc[-1]
                                if pd.notnull(val) and val > 0:
                                    cotacoes_temp[sym] = val
                        except:
                            pass

                # --- APLICAÇÃO E CONVERSÃO ---
                for sym_yahoo, preco in cotacoes_temp.items():
                    ativo_banco = mapa_ticker_banco_x_yahoo.get(sym_yahoo)
                    if not ativo_banco: continue

                    # Regra de Conversão:
                    # Se termina em -USD (Ex: SOL-USD), multiplica pelo Dólar
                    # Se NÃO tem .SA (Ex: AAPL), multiplica pelo Dólar

                    eh_dolarizado = sym_yahoo.endswith("-USD") or (".SA" not in sym_yahoo)

                    if eh_dolarizado:
                        mapa_precos[ativo_banco] = preco * usd_rate
                    else:
                        mapa_precos[ativo_banco] = preco

        # 5. Consolidação Final
        def get_valor_atual(row):
            if row['id_categoria'] == 3: return row['valor_projetado_fixa']

            ativo = row['descricao']
            custo = row['valor_investido']

            preco = mapa_precos.get(ativo)

            if preco and preco > 0:
                return preco * row['quantidade']

            return custo

        portfolio['Total Atual BRL'] = portfolio.apply(get_valor_atual, axis=1)
        portfolio['Valor Hoje BRL'] = portfolio.apply(
            lambda x: x['Total Atual BRL'] if x['id_categoria'] == 3 else (x['Total Atual BRL'] / x['quantidade']),
            axis=1)
        portfolio['Lucro/Prejuízo BRL'] = portfolio['Total Atual BRL'] - portfolio['valor_investido']
        portfolio['Rentabilidade %'] = portfolio.apply(
            lambda x: (x['Lucro/Prejuízo BRL'] / x['valor_investido'] * 100) if x['valor_investido'] > 0 else 0, axis=1)

        portfolio.rename(
            columns={'descricao': 'Ativo', 'quantidade': 'Quantidade', 'valor_investido': 'Custo Total BRL'},
            inplace=True)
        portfolio['Tipo'] = portfolio['id_categoria'].map({1: "Renda Variável", 2: "Cripto", 3: "Renda Fixa"})

        return portfolio.sort_values('Total Atual BRL', ascending=False)

    except Exception as e:
        print(f"Erro portfolio: {e}")
        return pd.DataFrame()


# ==========================================
# 3. AUXILIARES
# ==========================================
def pesquisar_ticker_yahoo(query):
    if not query or len(query) < 2: return []
    try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        headers = {'User-Agent': 'Mozilla/5.0'}
        params = {'q': query, 'quotesCount': 6}
        r = requests.get(url, params=params, headers=headers, timeout=2)
        data = r.json()
        sugestoes = []
        if 'quotes' in data:
            for q in data['quotes']:
                if q.get('quoteType') in ['EQUITY', 'ETF', 'CRYPTOCURRENCY', 'MUTUALFUND']:
                    s = q.get('symbol')
                    n = q.get('shortname', s)
                    sugestoes.append(f"{s} | {n}")
        return sugestoes
    except:
        return []


def buscar_sugestoes_yahoo(termo): return pesquisar_ticker_yahoo(termo)


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