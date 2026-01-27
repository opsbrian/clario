import streamlit as st
import time
from src.database import client
from src.utils_seguranca import gerar_hash


# --- 1. FUNÇÃO DO POPUP DE CADASTRO ---
@st.dialog("Criar uma conta no Clariô")
def popup_cadastro():
    st.markdown("""
        <p style='color: #767676; font-size: 0.9em; margin-bottom: 20px;'>
        Preencha os dados abaixo para começar.
        </p>
    """, unsafe_allow_html=True)

    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome", placeholder="Nome")
            email = st.text_input("E-mail", placeholder="seu@email.com")
        with c2:
            sobrenome = st.text_input("Sobrenome", placeholder="Sobrenome")
            telefone = st.text_input("Telefone", placeholder="+41")

        senha = st.text_input("Senha", type="password", placeholder="Nova senha")
        confirmar_senha = st.text_input("Confirme a Senha", type="password")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Finalizar e Entrar", use_container_width=True):
            if senha != confirmar_senha:
                st.error("Senhas diferentes!")
            elif not nome or not email or not senha:
                st.error("Preencha os campos obrigatórios.")
            else:
                try:
                    senha_hash = gerar_hash(senha).decode('utf-8')
                    novo_usuario = {
                        "nome": nome, "sobrenome": sobrenome, "email": email,
                        "senha": senha_hash, "telefone": telefone
                    }
                    client.table("usuarios").insert(novo_usuario).execute()
                    st.success("Conta criada!")
                    time.sleep(1)
                    st.rerun()  # Recarrega para logar
                except Exception as e:
                    st.error(f"Erro: {e}")


# --- 2. TELA DE LOGIN ATUALIZADA ---
def renderizar_login():
    # CSS Unificado (com a correção de chaves duplas para o PyCharm)
    st.markdown(f"""
        <style>
        .block-container {{ padding-top: 0rem !important; }}
        .stApp {{ background-color: #f6f6f6 !important; }}

        /* Estilo do Botão Principal */
        div.stButton > button:first-child {{
            background-color: #e73469 !important;
            color: white !important;
            border-radius: 25px !important;
            height: 3.5em !important;
            border: none !important;
        }}

        /* Inputs brancos e nítidos */
        .stTextInput>div>div>input {{
            background-color: white !important;
            color: #373643 !important;
            border-radius: 12px !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    _, col_central, _ = st.columns([1, 1.5, 1])

    with col_central:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("img/clario_logo_dark.svg", use_container_width=True)

        st.markdown("<h2 style='color: #373643; font-size: 1.3em;'>Olá! Acesse sua conta</h2>", unsafe_allow_html=True)

        email = st.text_input("E-mail", placeholder="seu@email.com", label_visibility="collapsed")
        senha = st.text_input("Senha", type="password", placeholder="Sua senha", label_visibility="collapsed")

        if st.button("Continuar", use_container_width=True):
            # Lógica de login aqui...
            pass

        st.markdown("<p style='text-align: center; color: #373643; margin: 20px 0;'>— ou —</p>", unsafe_allow_html=True)

        # TRIGGER DO POPUP
        if st.button("Criar uma conta agora", use_container_width=True):
            popup_cadastro()

        st.caption("<div style='text-align: center;'>Genebra, Suíça</div>", unsafe_allow_html=True)