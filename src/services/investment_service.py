import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, datetime
import requests
import numpy as np
from src.services.supabase_client import supabase
from src.services.market_data_service import buscar_historico_cdi_diario, buscar_indicadores_economicos

# ==========================================
# 0. MAPAS E AJUSTES MANUAIS
# ==========================================
PRECOS_MANUAIS = {
    "SNLG11": 1.24, "SNLG11.SA": 1.24,
    "SNEL11": 1.24, "SNEL11.SA": 1.24
}

# Traduz nomes comuns para Tickers do Yahoo
TICKER_MAPPING = {
    "FB": "META",
    "SOL": "SOL-USD", "SOLANA": "SOL-USD",
    "BTC": "BTC-USD", "BITCOIN": "BTC-USD",
    "ETH": "ETH-USD", "ETHEREUM": "ETH-USD",
    "USDT": "USDT-USD"
}


# ==========================================
# 1. FUNÇÕES AUXILIARES (RESOLVER TICKER)
# ==========================================
def resolver_ticker_yahoo(ticker, categoria_id=None):
    """
    Lógica blindada para descobrir o ticker correto.
    """
    t = ticker.upper().strip()

    # 1. Checa mapa manual
    if t in TICKER_MAPPING:
        return TICKER_MAPPING[t]

    # 2. Se já tem sufixo, confia
    if t.endswith(".SA") or t.endswith("-USD"):
        return t

    # 3. Lógica por Categoria do Banco de Dados
    if categoria_id == 2:  # Categoria 2 = Cripto
        return f"{t}-USD"

    # 4. Lógica de Padrão Brasileiro (Tem número? Ex: PETR4, ALZR11)
    if any(char.isdigit() for char in t):
        if not t.endswith(".SA"):
            return f"{t}.SA"

    # 5. Default (Ações USA ou Cripto sem categoria definida)
    return f"{t}-USD"


def buscar_cotacao_dolar():
    try:
        usd = yf.Ticker("USDBRL=X").history(period="1d")
        if not usd.empty:
            return float(usd['Close'].iloc[-1])
    except:
        pass
    return 5.80  # Fallback seguro


# ==========================================
# 2. FUNÇÕES DE ESCRITA (SALVAR)
# ==========================================
def salvar_investimento(user_id, data_op, ativo, cat_id, preco_un, qtd, taxa=None, indexador=None):
    try:
        if int(cat_id) == 3:  # Renda Fixa
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
# 3. MOTOR DE CÁLCULO RENDA FIXA
# ==========================================
def calcular_valor_presente_inteligente(row, df_cdi_historico, indicadores_atuais):
    try:
        if row['id_categoria'] != 3: return 0.0

        # Converte para data segura
        data_str = str(row['data'])
        if 'T' in data_str:
            data_aporte = datetime.strptime(data_str.split('T')[0], '%Y-%m-%d').date()
        else:
            data_aporte = datetime.strptime(data_str, '%Y-%m-%d').date()

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
# 4. BUSCA DE PORTFOLIO (MOTOR PRINCIPAL)
# ==========================================
def buscar_portfolio_real(user_id):
    try:
        # 1. Busca Dados no Banco
        res = supabase.table("investimento").select("*").eq("id_usuario", user_id).execute()
        if not res.data: return pd.DataFrame()
        df = pd.DataFrame(res.data)

        # Garante tipos numéricos
        df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)
        df['valor_investido'] = pd.to_numeric(df['valor_investido'], errors='coerce').fillna(0)

        # 2. Processa Renda Fixa (Cat 3)
        df_cdi_hist = buscar_historico_cdi_diario()
        indicadores_atuais = buscar_indicadores_economicos()

        df['valor_projetado_fixa'] = df.apply(
            lambda r: calcular_valor_presente_inteligente(r, df_cdi_hist, indicadores_atuais), axis=1
        )

        # 3. Agrupamento Inicial
        portfolio = df.groupby(['descricao', 'id_categoria']).agg({
            'quantidade': 'sum',
            'valor_investido': 'sum',
            'valor_projetado_fixa': 'sum'
        }).reset_index()

        portfolio = portfolio[portfolio['quantidade'] > 0.000001].copy()

        # 4. Precificação de Mercado (Renda Variável)
        df_var = portfolio[portfolio['id_categoria'].isin([1, 2])].copy()

        cotacoes_finais = {}
        usd_rate = buscar_cotacao_dolar()

        tickers_para_buscar = []
        mapa_ticker_yahoo_para_nome_banco = {}

        for idx, row in df_var.iterrows():
            nome_banco = row['descricao']

            if nome_banco in PRECOS_MANUAIS:
                cotacoes_finais[nome_banco] = PRECOS_MANUAIS[nome_banco]
                continue

            ticker_y = resolver_ticker_yahoo(nome_banco, row['id_categoria'])
            tickers_para_buscar.append(ticker_y)
            mapa_ticker_yahoo_para_nome_banco[ticker_y] = nome_banco

        tickers_unicos = list(set(tickers_para_buscar))
        if tickers_unicos:
            try:
                dados = yf.download(tickers_unicos, period="1d", progress=False)['Close']

                for t in tickers_unicos:
                    preco = 0.0
                    try:
                        if len(tickers_unicos) == 1:
                            preco = float(dados.iloc[-1])
                        else:
                            preco = float(dados[t].iloc[-1])
                    except:
                        pass

                    if preco > 0:
                        if "-USD" in t:
                            preco_brl = preco * usd_rate
                        else:
                            preco_brl = preco

                        nome_original = mapa_ticker_yahoo_para_nome_banco.get(t)
                        if nome_original:
                            cotacoes_finais[nome_original] = preco_brl
            except Exception as e:
                print(f"Erro Yahoo Batch: {e}")

        # 5. Consolidação Final
        def calcular_total_atual(row):
            if row['id_categoria'] == 3:
                return row['valor_projetado_fixa']

            nome = row['descricao']
            custo = row['valor_investido']
            qtd = row['quantidade']

            preco_mercado = cotacoes_finais.get(nome)

            if preco_mercado and preco_mercado > 0:
                return preco_mercado * qtd

            return custo  # Fallback

        portfolio['Total Atual BRL'] = portfolio.apply(calcular_total_atual, axis=1)

        # --- CORREÇÃO: ADICIONANDO A COLUNA QUE FALTAVA ---
        portfolio['Valor Hoje BRL'] = portfolio.apply(
            lambda x: x['Total Atual BRL'] if x['id_categoria'] == 3 else (
                x['Total Atual BRL'] / x['quantidade'] if x['quantidade'] > 0 else 0),
            axis=1
        )

        portfolio['Lucro/Prejuízo BRL'] = portfolio['Total Atual BRL'] - portfolio['valor_investido']
        portfolio['Rentabilidade %'] = portfolio.apply(
            lambda x: (x['Lucro/Prejuízo BRL'] / x['valor_investido'] * 100) if x['valor_investido'] > 0 else 0, axis=1
        )

        portfolio.rename(columns={
            'descricao': 'Ativo',
            'quantidade': 'Quantidade',
            'valor_investido': 'Custo Total BRL'
        }, inplace=True)

        portfolio['Tipo'] = portfolio['id_categoria'].map({1: "Renda Variável", 2: "Cripto", 3: "Renda Fixa"})

        return portfolio.sort_values('Total Atual BRL', ascending=False)

    except Exception as e:
        print(f"Erro Portfolio Geral: {e}")
        return pd.DataFrame()


# ==========================================
# 5. INTEGRAÇÃO COM DASHBOARD
# ==========================================
def buscar_dados_resumidos_dashboard(user_id):
    """
    Retorna apenas os números finais para o dashboard.
    """
    df = buscar_portfolio_real(user_id)

    if df.empty:
        return 0.0, 0.0, 0.0, "---", 0.0

    saldo_total = df['Total Atual BRL'].sum()
    custo_total = df['Custo Total BRL'].sum()
    lucro_reais = saldo_total - custo_total

    # Top Ativo
    try:
        top_row = df.loc[df['Lucro/Prejuízo BRL'].idxmax()]
        top_nome = top_row['Ativo']
        top_lucro = top_row['Lucro/Prejuízo BRL']
    except:
        top_nome = "---"
        top_lucro = 0.0

    return saldo_total, custo_total, lucro_reais, top_nome, top_lucro


# ==========================================
# 6. AUXILIARES E SUGESTÕES
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