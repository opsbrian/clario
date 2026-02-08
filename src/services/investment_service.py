import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, datetime
from src.services.supabase_client import supabase
import requests

def salvar_investimento(user_id, data, ticker, categoria_id, preco_unitario_brl, qtd, rentabilidade=None):
    """
    Salva a operação garantindo que o nome customizado vá para a 'descricao'.
    """
    try:
        dados = {
            "id_usuario": user_id,
            "data": data.isoformat(),
            "descricao": ticker.strip(), # Mantém o nome como o usuário digitou
            "id_categoria": categoria_id,
            "valor_investido": preco_unitario_brl * qtd,
            "quantidade": qtd,
            "rentabilidade": rentabilidade # Novo campo para cálculos futuros
        }
        supabase.table("investimento").insert(dados).execute()
        return True, "Sucesso!"
    except Exception as e:
        return False, f"Erro: {str(e)}"

def buscar_portfolio_real(user_id):
    """
    Busca transações, converte preços internacionais e calcula Lucro/Prejuízo em BRL.
    """
    try:
        # 1. Busca transações no banco
        res = supabase.table("investimento").select("*").eq("id_usuario", user_id).execute()
        if not res.data:
            return pd.DataFrame()

        df_raw = pd.DataFrame(res.data)

        # 2. Consolida posição atual (Soma Qtd e Soma Custo em BRL)
        portfolio = df_raw.groupby(['descricao', 'id_categoria']).agg({
            'quantidade': 'sum',
            'valor_investido': 'sum'
        }).reset_index()

        # Filtra ativos que o usuário não possui mais (Qtd <= 0)
        portfolio = portfolio[portfolio['quantidade'] > 0]
        if portfolio.empty:
            return pd.DataFrame()

        # 3. Busca Cotação do Dólar Hoje (USDBRL=X)
        try:
            usd_brl_ticker = yf.Ticker("USDBRL=X")
            taxa_usd = usd_brl_ticker.history(period="1d")['Close'].iloc[-1]
        except:
            taxa_usd = 5.20  # Fallback caso a API falhe

        # 4. Busca Preços de Mercado e Converte para BRL
        precos_mercado_brl = {}
        for _, row in portfolio.iterrows():
            t = row['descricao']
            cat = row['id_categoria']
            try:
                # Define o símbolo correto para o Yahoo Finance
                if cat == 2:  # Cripto (Yahoo usa USD)
                    sym = f"{t}-USD" if "-" not in t else t
                elif cat == 1 and "." not in t and "-" not in t:  # Ação BR
                    sym = f"{t}.SA"
                else:
                    sym = t

                ticker_data = yf.Ticker(sym)
                preco_mercado = ticker_data.history(period="1d")['Close'].iloc[-1]

                # CONVERSÃO: Se for Cripto (Cat 2) ou Stock Americana (sem .SA), converte USD -> BRL
                if cat == 2 or (cat == 1 and ".SA" not in sym):
                    precos_mercado_brl[t] = preco_mercado * taxa_usd
                else:
                    precos_mercado_brl[t] = preco_mercado
            except:
                # Se falhar, assume que o valor atual é o preço médio de compra
                precos_mercado_brl[t] = row['valor_investido'] / row['quantidade']

        # 5. Cálculos Finais e Renomeação para bater com a VIEW
        portfolio['Valor Hoje BRL'] = portfolio['descricao'].map(precos_mercado_brl)
        portfolio['Total Atual BRL'] = portfolio['quantidade'] * portfolio['Valor Hoje BRL']

        # Lucro = (Valor de Mercado Hoje) - (Custo de Aquisição Total)
        portfolio['Lucro/Prejuízo BRL'] = portfolio['Total Atual BRL'] - portfolio['valor_investido']
        portfolio['Rentabilidade %'] = (portfolio['Lucro/Prejuízo BRL'] / portfolio['valor_investido']) * 100

        # Renomeação final de colunas para a interface
        portfolio.rename(columns={
            'descricao': 'Ativo',
            'quantidade': 'Quantidade',
            'valor_investido': 'Custo Total BRL'
        }, inplace=True)

        # Mapeia tipos para legibilidade nos gráficos
        portfolio['Tipo'] = portfolio['id_categoria'].map({1: "Renda Variável", 2: "Cripto", 3: "Renda Fixa"})

        return portfolio
    except Exception as e:
        print(f"Erro no Service: {e}")
        return pd.DataFrame()


def pesquisar_ticker_yahoo(query):
    """Consulta o autocomplete do Yahoo Finance."""
    if not query or len(query) < 2:
        return []

    try:
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=5&newsCount=0"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()

        sugestoes = []
        for q in data.get('quotes', []):
            symbol = q.get('symbol')
            name = q.get('shortname', q.get('longname', 'Ativo'))
            sugestoes.append(f"{symbol} | {name}")

        return sugestoes
    except Exception as e:
        print(f"Erro na busca: {e}")
        return []


@st.cache_data(ttl=3600)  # Cache de 1 hora para dados históricos
def buscar_evolucao_patrimonio(user_id):
    try:
        # 1. Busca todas as transações
        res = supabase.table("investimento").select("*").eq("id_usuario", user_id).order("data").execute()
        if not res.data:
            return pd.DataFrame()

        df_transacoes = pd.DataFrame(res.data)
        # Normaliza para datetime para facilitar cálculos
        df_transacoes['data'] = pd.to_datetime(df_transacoes['data']).dt.date

        # 2. Define o período: da primeira transação até hoje
        data_inicio = df_transacoes['data'].min()
        data_fim = date.today()  # Agora 'date' é a classe, então .today() funciona
        datas_periodo = pd.date_range(start=data_inicio, end=data_fim)

        # 3. Busca preços históricos e Dólar (USDBRL=X)
        tickers = df_transacoes['descricao'].unique().tolist()

        # Ajuste de tickers para Yahoo Finance
        tickers_yf = ["USDBRL=X"]
        for t in tickers:
            cat = df_transacoes[df_transacoes['descricao'] == t]['id_categoria'].iloc[0]
            if cat == 2:
                tickers_yf.append(f"{t}-USD")
            elif cat == 1 and "." not in t and "-" not in t:
                tickers_yf.append(f"{t}.SA")
            else:
                tickers_yf.append(t)

        # Download em massa para performance
        historico_precos = yf.download(tickers_yf, start=data_inicio, progress=False)['Close']
        historico_precos = historico_precos.ffill()  # Trata feriados e fins de semana

        # 4. Cálculo do Patrimônio Diário
        evolucao = []
        for d in datas_periodo:
            d_str = d.strftime('%Y-%m-%d')
            patrimonio_dia = 0

            # Filtra transações até este dia
            transacoes_ate_hoje = df_transacoes[df_transacoes['data'] <= d.date()]

            for t in tickers:
                qtd_no_dia = transacoes_ate_hoje[transacoes_ate_hoje['descricao'] == t]['quantidade'].sum()

                if qtd_no_dia > 0:
                    cat = transacoes_ate_hoje[transacoes_ate_hoje['descricao'] == t]['id_categoria'].iloc[0]
                    sym = f"{t}-USD" if cat == 2 else (f"{t}.SA" if cat == 1 and "." not in t and "-" not in t else t)

                    try:
                        if sym in historico_precos.columns:
                            preco_ref = historico_precos.loc[d_str, sym]

                            # Conversão para BRL se for internacional
                            if cat == 2 or (cat == 1 and ".SA" not in sym):
                                taxa_usd = historico_precos.loc[d_str, "USDBRL=X"]
                                preco_ref *= taxa_usd

                            patrimonio_dia += qtd_no_dia * preco_ref
                    except KeyError:
                        continue

            evolucao.append({"Data": d, "Patrimônio": patrimonio_dia})

        return pd.DataFrame(evolucao)
    except Exception as e:
        st.error(f"Erro ao calcular evolução: {e}")
        return pd.DataFrame()