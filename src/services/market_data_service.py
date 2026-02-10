import requests
import streamlit as st
import pandas as pd
from datetime import date, timedelta


@st.cache_data(ttl=86400)  # Cache de 24h (Dados históricos não mudam toda hora)
def buscar_historico_cdi_diario():
    """
    Busca o histórico diário do CDI (Série 12 do BCB) dos últimos 5 anos.
    Retorna um DataFrame com Data e Fator Diário.
    """
    try:
        # Data de 5 anos atrás até hoje
        data_ini = (date.today() - timedelta(days=365 * 5)).strftime("%d/%m/%Y")
        data_fim = date.today().strftime("%d/%m/%Y")

        # Série 12: Taxa de juros - CDI acumulada no mês % a.d.
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial={data_ini}&dataFinal={data_fim}"

        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y').dt.date
            # O valor vem em string "0,0425". Converter para float e dividir por 100
            df['valor'] = df['valor'].str.replace(',', '.').astype(float) / 100
            return df

    except Exception as e:
        print(f"Erro ao buscar histórico CDI: {e}")

    return pd.DataFrame()  # Retorna vazio se falhar


@st.cache_data(ttl=3600)
def buscar_indicadores_economicos():
    """
    Mantém a busca de indicadores atuais para referência visual.
    """
    indicadores = {"SELIC": 0.1125, "CDI": 0.1115, "IPCA": 0.0450}
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # Selic Meta (432)
        r_selic = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json",
                               headers=headers, timeout=5)
        if r_selic.status_code == 200:
            val = float(r_selic.json()[0]['valor'].replace(',', '.')) / 100
            indicadores["SELIC"] = val
            indicadores["CDI"] = val - 0.0010

        # IPCA (13522)
        r_ipca = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1?formato=json",
                              headers=headers, timeout=5)
        if r_ipca.status_code == 200:
            val = float(r_ipca.json()[0]['valor'].replace(',', '.')) / 100
            indicadores["IPCA"] = val
    except:
        pass

    return indicadores