import streamlit as st
import pandas as pd
from datetime import date, timedelta
from src.services.credit_card_service import (
    listar_cartoes,
    buscar_fatura_detalhada,
    salvar_compra_cartao
)
from src.services.transaction_service import (
    listar_categorias_selecao,
    excluir_item_generico
)
# IMPORTAÇÃO DO FORMATADOR CENTRALIZADO
from src.utils.formatters import formatar_brl


# --- HELPERS ---
def get_mes_nome(mes):
    nomes = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out",
             11: "Nov", 12: "Dez"}
    return nomes.get(mes, "")


# --- CSS E ESTILIZAÇÃO (THEME AWARE) ---
def carregar_css():
    st.markdown("""
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            .block-container { padding-top: 2rem; }

            /* CARD DA FATURA - ADAPTATIVO */
            .bill-card {
                background: linear-gradient(135deg, var(--secondary-background-color) 0%, rgba(128,128,128,0.1) 100%);
                border-radius: 20px;
                padding: 24px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                border: 1px solid rgba(128,128,128,0.1);
                position: relative; overflow: hidden;
            }
            .bill-border { position: absolute; left: 0; top: 0; bottom: 0; width: 6px; }

            .bill-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }

            .bill-title { 
                font-family: 'Inter'; font-size: 14px; font-weight: 600; 
                text-transform: uppercase; color: var(--text-color); opacity: 0.7; 
            }

            .bill-status { 
                font-family: 'Inter'; font-size: 11px; font-weight: 700; 
                text-transform: uppercase; padding: 4px 10px; border-radius: 10px; 
            }

            .bill-value { 
                font-family: 'Inter'; font-size: 32px; font-weight: 700; 
                color: var(--text-color); 
                margin: 10px 0; 
            }

            .bill-info { 
                display: flex; justify-content: space-between; 
                font-family: 'Inter'; font-size: 12px; 
                color: var(--text-color); opacity: 0.6; 
                margin-top: 15px; 
            }

            .bill-limit { color: #18CB96; font-weight: 600; opacity: 1; }

            /* BARRA DE PROGRESSO */
            .prog-container { width: 100%; height: 6px; background: rgba(128,128,128,0.2); border-radius: 3px; overflow: hidden; }
            .prog-bar { height: 100%; border-radius: 3px; }

            /* LISTA DE COMPRAS */
            .item-row { 
                display: flex; align-items: center; justify-content: space-between; 
                padding: 12px 0; border-bottom: 1px solid rgba(128,128,128,0.1); 
            }

            .item-icon { 
                width: 38px; height: 38px; 
                background: rgba(128,128,128,0.1); 
                border-radius: 10px; 
                display: flex; align-items: center; justify-content: center; 
                color: var(--text-color); margin-right: 12px; 
            }

            .item-desc { font-family: 'Inter'; font-weight: 500; font-size: 14px; color: var(--text-color); }
            .item-date { font-family: 'Inter'; font-size: 11px; color: var(--text-color); opacity: 0.6; }
            .item-val { font-family: 'Inter'; font-weight: 600; font-size: 14px; color: var(--text-color); }

            /* BOTÃO DELETAR DISCRETO */
            /* Removemos bordas e fundo para ficar apenas o ícone limpo */
            button[kind="secondary"] { 
                border: none !important; 
                background: transparent !important; 
                color: var(--text-color) !important; opacity: 0.5;
            }
            button[kind="secondary"]:hover { 
                color: #FF4B4B !important; opacity: 1; 
                background: rgba(255, 75, 75, 0.1) !important; 
            }
        </style>
    """, unsafe_allow_html=True)


# --- POPUP: NOVA COMPRA / ESTORNO ---
@st.dialog("Novo Lançamento")
def popup_nova_compra(user_id, cartoes, card_padrao_idx=0):
    cats_despesa = listar_categorias_selecao("despesa")

    def f_nome(o):
        return o.get('nome_cartao')

    def f_cat(o):
        return o['descricao']

    tipo_op = st.radio("Tipo", ["Compra", "Estorno"], horizontal=True, label_visibility="collapsed")

    if tipo_op == "Estorno":
        st.info("O valor será lançado como crédito, abatendo o total da fatura.")

    with st.form("form_compra_cc", clear_on_submit=True):
        c1, c2 = st.columns(2)
        card_sel = c1.selectbox("Cartão", cartoes, index=card_padrao_idx, format_func=f_nome)
        cat_sel = c2.selectbox("Categoria", cats_despesa, format_func=f_cat)

        desc_label = "Estabelecimento" if tipo_op == "Compra" else "Origem do Reembolso"
        desc = st.text_input(desc_label)

        c3, c4 = st.columns(2)
        val_total = c3.number_input("Valor (R$)", min_value=0.01, step=10.0)
        parcelas = c4.number_input("Parcelas", min_value=1, value=1, step=1)

        c5, c6 = st.columns(2)
        dt_compra = c5.date_input("Data", value=date.today())
        devedor = c6.text_input("Devedor (Opcional)")

        btn_label = "Lançar Compra" if tipo_op == "Compra" else "Lançar Estorno"

        if st.form_submit_button(btn_label, type="primary", use_container_width=True):
            if not desc:
                st.warning("Informe a descrição.")
            else:
                valor_final = val_total
                if tipo_op == "Estorno":
                    valor_final = val_total * -1

                ok, msg = salvar_compra_cartao(
                    user_id,
                    card_sel['id'],
                    cat_sel['id_categoria'],
                    dt_compra,
                    desc,
                    valor_final,
                    parcelas,
                    devedor
                )
                if ok:
                    st.toast(f"{tipo_op} registrado!", icon="✅")
                    st.rerun()
                else:
                    st.error(msg)


# --- COMPONENTES VISUAIS ---
def render_fatura_card(dados):
    val = dados['fatura_total']
    lim = dados['limite_total']

    pct = (val / lim * 100) if lim > 0 else 0
    pct = max(0, min(pct, 100))

    status = dados['status']
    color = "#18CB96"
    if status == 'Fechada': color = "#2196F3"
    if status == 'Atrasada': color = "#FF4B4B"

    val_fmt = formatar_brl(val)
    lim_disp_fmt = formatar_brl(dados['limite_disponivel'])

    st.markdown(f"""
    <div class="bill-card">
        <div class="bill-border" style="background-color: {color};"></div>
        <div class="bill-header">
            <span class="bill-title">Fatura Atual</span>
            <span class="bill-status" style="background: {color}20; color: {color};">{status}</span>
        </div>
        <div class="bill-value">{val_fmt}</div>
        <div class="prog-container">
            <div class="prog-bar" style="width: {pct}%; background-color: {color};"></div>
        </div>
        <div class="bill-info">
            <span class="bill-limit">Limite disp. {lim_disp_fmt}</span>
            <span>Vence {dados['vencimento'].strftime('%d %b')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_lista_compras(itens):
    if not itens:
        st.info("Sem compras neste período.")
        return

    st.markdown("<br><h4 style='color:var(--text-color); opacity:0.7; margin-bottom:10px'>Lançamentos</h4>",
                unsafe_allow_html=True)

    for item in itens:
        is_estorno = item['valor'] < 0

        if is_estorno:
            icon = "keyboard_return"
            color_val = "#18CB96"
            icon_color = "#18CB96"
            sinal = "+"
            valor_abs = abs(item['valor'])
        else:
            icon = "shopping_bag"
            color_val = "var(--text-color)"
            icon_color = "var(--text-color)"
            sinal = ""
            valor_abs = item['valor']

        data_fmt = item['data'].strftime('%d %b')
        parc = f"({item['parcela_atual']}/{item['parcelas']})" if item['parcelas'] > 1 else ""

        valor_final = f"{sinal} {formatar_brl(valor_abs)}"

        c_row, c_del = st.columns([6, 1], vertical_alignment="center")

        with c_row:
            st.markdown(f"""
            <div class="item-row" style="border-bottom:none; padding:0;"> 
                <div style="display:flex; align-items:center;">
                    <div class="item-icon" style="color:{icon_color}; opacity:0.7;">
                        <span class="material-symbols-rounded" style="font-size:20px">{icon}</span>
                    </div>
                    <div>
                        <div class="item-desc">{item['descricao']} <span style="font-size:10px; opacity:0.6">{parc}</span></div>
                        <div class="item-date">{data_fmt}</div>
                    </div>
                </div>
                <div class="item-val" style="color:{color_val}">{valor_final}</div>
            </div>
            """, unsafe_allow_html=True)

        with c_del:
            # AQUI ESTÁ A CORREÇÃO:
            # Label vazia "" e apenas o ícone definido.
            if st.button("", key=f"del_cc_{item['id_trans_cartao']}", icon=":material/delete:",
                         help="Excluir Lançamento", type="secondary"):
                if excluir_item_generico(item['id_trans_cartao'], "transacoes_cartao_credito", "id_trans_cartao"):
                    st.rerun()

        st.markdown("<div style='height:1px; background-color:rgba(128,128,128,0.1); margin-bottom:12px;'></div>",
                    unsafe_allow_html=True)


# --- TELA PRINCIPAL ---
def renderizar_tela_cartao():
    carregar_css()
    user_id = st.session_state.user.id

    c_title, c_sel, c_btn = st.columns([2, 1, 0.8], vertical_alignment="center")

    with c_title:
        st.markdown("## Meus Cartões")

    cartoes = listar_cartoes(user_id)
    if not cartoes:
        st.warning("Nenhum cartão cadastrado.")
        return

    map_cartoes = {c['nome_cartao']: c for c in cartoes}

    with c_sel:
        nome_sel = st.selectbox("Selecione o Cartão", list(map_cartoes.keys()), label_visibility="collapsed")
        card_ativo = map_cartoes[nome_sel]

    with c_btn:
        idx_ativo = list(map_cartoes.keys()).index(nome_sel)
        if st.button("Lançar", icon=":material/add_card:", type="primary", use_container_width=True):
            popup_nova_compra(user_id, cartoes, idx_ativo)

    hoje = date.today()
    abas = []
    datas = []

    indices_meses = [0, -1, 1, 2, 3]

    for i in indices_meses:
        m = (hoje.month + i - 1) % 12 + 1
        y = hoje.year + (hoje.month + i - 1) // 12

        nome_mes = get_mes_nome(m)
        ano_curto = str(y)[2:]

        if i == 0:
            label = f":material/credit_card: {nome_mes} {ano_curto} (Atual)"
        elif i == -1:
            label = f":material/history: {nome_mes} {ano_curto}"
        else:
            label = f":material/schedule: {nome_mes} {ano_curto}"

        abas.append(label)
        datas.append((m, y))

    tabs = st.tabs(abas)

    for i, tab in enumerate(tabs):
        with tab:
            m_ref, y_ref = datas[i]
            dados_fatura = buscar_fatura_detalhada(user_id, card_ativo['id'], m_ref, y_ref)

            if dados_fatura:
                st.markdown("<br>", unsafe_allow_html=True)
                render_fatura_card(dados_fatura)
                render_lista_compras(dados_fatura['itens'])
            else:
                st.info(f"Sem movimentações para {nome_mes} {ano_curto}.")