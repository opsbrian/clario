import streamlit as st
import pandas as pd
from datetime import date
from src.services.transaction_service import (
    salvar_transacao,
    listar_transacoes_unificadas, excluir_item_generico, confirmar_pagamento,
    listar_bancos_selecao, listar_categorias_selecao
)

# --- MAPA DE TRADUÇÃO (PT-BR) ---
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

MESES_ABREV = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
}


# --- CONFIGURAÇÕES VISUAIS & CSS ---
def carregar_estilos():
    st.markdown("""
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

        <style>
            .block-container { padding-top: 3rem; }

            /* KPI CARDS */
            .kpi-card {
                background-color: #1A1A1A;
                border-radius: 12px;
                padding: 20px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                height: 110px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                position: relative;
                overflow: hidden;
            }
            .kpi-accent { position: absolute; left: 0; top: 15%; bottom: 15%; width: 4px; border-radius: 0 4px 4px 0; }
            .kpi-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
            .kpi-title { font-family: 'Inter'; font-size: 13px; color: #A0A0A0; font-weight: 500; }
            .kpi-value { font-family: 'Inter'; font-size: 22px; font-weight: 700; color: #FFFFFF; letter-spacing: -0.5px; }
            .kpi-sub { font-family: 'Inter'; font-size: 11px; color: #666; margin-top: 4px; }

            /* LISTA */
            .transacao-row { padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
            .icon-box { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background-color: rgba(255, 255, 255, 0.03); }

            .tx-title { font-family: 'Inter'; font-weight: 600; font-size: 15px; color: #EEE; }
            .tx-sub { font-family: 'Inter'; font-size: 12px; color: #888; }
            .tx-val { font-family: 'Inter'; font-weight: 600; font-size: 15px; text-align: right; }
            .tx-status { font-family: 'Inter'; font-size: 11px; text-align: right; }

            .material-symbols-rounded { font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24; }

            button[kind="secondary"] { border: 1px solid rgba(255,255,255,0.1); }
            button[kind="secondary"]:hover { border-color: rgba(255,255,255,0.3); color: #FF4B4B; }
        </style>
    """, unsafe_allow_html=True)


# --- COMPONENTE KPI ---
def render_kpi_card(icon, title, value, sub, color):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-accent" style="background-color: {color};"></div>
        <div style="padding-left: 12px;">
            <div class="kpi-header">
                <span class="material-symbols-rounded" style="color: {color}; font-size: 20px;">{icon}</span>
                <span class="kpi-title">{title}</span>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- POPUPS ---
@st.dialog("Baixar Pagamento")
def popup_pagamento(item):
    st.markdown(f"### Baixar: {item['descricao']}")
    st.caption("Confirmar recebimento/pagamento?")
    c1, c2 = st.columns(2)
    c1.metric("Valor", f"R$ {item['valor']:,.2f}")
    c2.metric("Vencimento", item['data'].strftime('%d/%m/%Y'))
    st.divider()
    dt_baixa = st.date_input("Data da Efetivação", value=date.today())
    if st.button("Confirmar Baixa", type="primary", use_container_width=True):
        if confirmar_pagamento(item['id_trans_bank'], dt_baixa):
            st.toast("Confirmado!", icon="✅");
            st.rerun()


@st.dialog("Nova Transação")
def popup_formulario(user_id):
    lista_bancos = listar_bancos_selecao(user_id)
    cats_receita = listar_categorias_selecao("receita")
    cats_despesa = listar_categorias_selecao("despesa")

    def f_nome(o):
        return o.get('nome_banco')

    def f_cat(o):
        return o['descricao']

    if not lista_bancos:
        st.warning("É necessário cadastrar uma conta bancária primeiro.")
        return

    # --- FORMULÁRIO (SÓ CONTA) ---
    tipo = st.radio("Operação", ["Saída", "Entrada"], horizontal=True, label_visibility="collapsed")
    tipo_db = "saida" if tipo == "Saída" else "entrada"
    lst = cats_despesa if tipo == "Saída" else cats_receita
    if not lst: lst = [{'id_categoria': None, 'descricao': 'Geral'}]

    c1, c2 = st.columns(2)
    bk = c1.selectbox("Conta", lista_bancos, format_func=f_nome)
    cat = c2.selectbox("Categoria", lst, format_func=f_cat, key="cc_cat")

    is_emp = (cat['descricao'] == 'Empréstimo' and tipo_db == 'entrada')

    c3, c4 = st.columns([1, 2])
    val = c3.number_input("Valor", min_value=0.01, step=100.0)
    desc = c4.text_input("Descrição")

    parc = 1;
    jur = 0.0
    if is_emp:
        st.markdown("---")
        cp1, cp2 = st.columns(2)
        parc = cp1.number_input("Parcelas", 1)
        jur = cp2.number_input("Juros %", 0.0)
        st.caption(f"Serão geradas {parc} parcelas futuras de saída.")
        st.markdown("---")

    c5, c6 = st.columns(2)
    dt = c5.date_input("Data", value=date.today())
    dev = c6.text_input("Devedor")

    if st.button("Salvar Lançamento", type="primary", use_container_width=True):
        if not desc:
            st.warning("Descrição obrigatória.")
        else:
            ok, msg = salvar_transacao(user_id, bk['id_bank'], cat['id_categoria'], tipo_db, dt, desc, val, dev,
                                       is_emprestimo=is_emp, parcelas=parc, taxa_juros=jur)
            if ok:
                st.toast("Salvo!", icon="✅"); st.rerun()
            else:
                st.error(msg)


# --- TELA PRINCIPAL ---
def renderizar_nova_transacao():
    carregar_estilos()

    # --- HEADER ---
    c_title, c_filter, c_btn = st.columns([3, 1.5, 1.2], vertical_alignment="center")

    with c_title:
        st.markdown("<h2 style='margin:0'>Extrato</h2>", unsafe_allow_html=True)

    with c_filter:
        data_ref = st.date_input(
            "Mês de Referência",
            value=date.today(),
            format="DD/MM/YYYY",
            label_visibility="collapsed",
            help="Selecione qualquer dia do mês para filtrar."
        )

    with c_btn:
        if st.button("Novo Lançamento", type="primary", use_container_width=True):
            popup_formulario(st.session_state.user.id)

    # Dados
    user_id = st.session_state.user.id
    df_raw = listar_transacoes_unificadas(user_id)

    if not df_raw.empty:
        # --- FILTRO CRÍTICO: REMOVE CARTÃO DE CRÉDITO DA TELA DE TRANSAÇÕES ---
        # Mantém apenas 'Conta' e 'Investimento' (que é o que afeta saldo imediato)
        df = df_raw[df_raw['origem'] != 'Cartão'].copy()
        # ----------------------------------------------------------------------

        # Filtros de Data
        mes_sel = data_ref.month
        ano_sel = data_ref.year
        df_mes = df[(df['data'].dt.month == mes_sel) & (df['data'].dt.year == ano_sel)]

        # --- LÓGICA DE KPI ---
        df_mes_pago = df_mes[df_mes['concluido'] == True]

        is_invest = (df_mes_pago['cat_tipo'] == 'investimento') | (df_mes_pago['origem'] == 'Investimento')
        ent = df_mes_pago[df_mes_pago['tipo'] == 'entrada']['valor'].sum()
        sai = df_mes_pago[df_mes_pago['tipo'] == 'saida']['valor'].sum()
        inv = df_mes_pago[is_invest]['valor'].sum()

        # Pendente (Contas a Pagar / Receber)
        pen = df[df['concluido'] == False]['valor'].sum()

        st.markdown("<br>", unsafe_allow_html=True)

        # --- CARDS KPI ---
        k1, k2, k3, k4 = st.columns(4)
        mes_nome = MESES_PT[data_ref.month]

        with k1:
            render_kpi_card("arrow_upward", "Entradas", f"R$ {ent:,.2f}", f"Recebido em {mes_nome}", "#18CB96")
        with k2:
            render_kpi_card("arrow_downward", "Saídas", f"R$ {sai:,.2f}", f"Pago em {mes_nome}", "#E91E63")
        with k3:
            render_kpi_card("trending_up", "Investido", f"R$ {inv:,.2f}", f"Aportes em {mes_nome}", "#9C27B0")
        with k4:
            render_kpi_card("pending_actions", "A Pagar", f"R$ {pen:,.2f}", "Total Pendente Geral", "#FFBD45")

        st.markdown(f"<br><h4 style='color:#DDD; margin-bottom:15px'>Histórico de {mes_nome}/{ano_sel}</h4>",
                    unsafe_allow_html=True)

        if df_mes.empty:
            st.info(f"Nenhuma movimentação em conta/investimento encontrada em {mes_nome}/{ano_sel}.")
        else:
            for idx, row in df_mes.iterrows():
                # Tratamento de ID para evitar duplicidade
                raw_id = row.get('id_trans_bank') if row['origem'] == 'Conta' else row.get('id_invest')
                uid = str(raw_id) if pd.notna(raw_id) else f"temp_{idx}"

                with st.container():
                    c_icon, c_info, c_val, c_btn = st.columns([0.8, 5, 2, 1.2], vertical_alignment="center")

                    # 1. ÍCONE
                    icon_name = row.get('icon_db', 'receipt_long')
                    if not row['concluido']:
                        icon_color = "#FFBD45"
                        icon_name = "schedule"
                    else:
                        cat_t = row.get('cat_tipo', 'outros')
                        if cat_t == 'investimento' or row['origem'] == 'Investimento':
                            icon_color = "#9C27B0"
                        elif row['tipo'] == 'entrada':
                            icon_color = "#18CB96"
                        else:
                            icon_color = "#E91E63"

                    with c_icon:
                        st.markdown(
                            f"<div class='icon-box'><span class='material-symbols-rounded' style='color:{icon_color}; font-size:22px'>{icon_name}</span></div>",
                            unsafe_allow_html=True)

                    # 2. TEXTO
                    with c_info:
                        dia = row['data'].day
                        mes_abrev = MESES_ABREV[row['data'].month]
                        data_fmt = f"{dia:02d} {mes_abrev}"

                        sub = f"{data_fmt} • {row['origem']}"
                        if row.get('detalhe'): sub += f" • {row['detalhe']}"
                        st.markdown(
                            f"<div><div class='tx-title'>{row['descricao']}</div><div class='tx-sub'>{sub}</div></div>",
                            unsafe_allow_html=True)

                    # 3. VALOR
                    with c_val:
                        if row['tipo'] == 'entrada':
                            val_color = "#18CB96";
                            sinal = "+"
                        else:
                            val_color = "#E91E63";
                            sinal = "-"

                        st_txt = "Pendente" if not row['concluido'] else "Pago"
                        st_clr = "#FFBD45" if not row['concluido'] else "#666"

                        st.markdown(
                            f"<div style='text-align:right'><div class='tx-val' style='color:{val_color}'>{sinal} R$ {row['valor']:,.2f}</div><div class='tx-status' style='color:{st_clr}'>{st_txt}</div></div>",
                            unsafe_allow_html=True)

                    # 4. BOTÕES
                    with c_btn:
                        if row['origem'] == 'Conta' and not row['concluido']:
                            if st.button("", key=f"p_{uid}", icon=":material/payments:", help="Baixar"):
                                popup_pagamento(row)
                        else:
                            if st.button("", key=f"d_{uid}", icon=":material/delete:", help="Excluir",
                                         type="secondary"):
                                tbl = "transacoes_bancarias";
                                col = "id_trans_bank";
                                val_id = row.get('id_trans_bank')
                                if row[
                                    'origem'] == 'Investimento': tbl = "investimento"; col = "id_invest"; val_id = row.get(
                                    'id_invest')
                                # Cartão removido daqui, então não precisa de lógica para ele
                                if excluir_item_generico(val_id, tbl, col): st.rerun()

                    st.markdown("<div style='height:1px; background-color:rgba(255,255,255,0.05); margin:6px 0'></div>",
                                unsafe_allow_html=True)

    else:
        st.info("Nenhuma movimentação registrada.")