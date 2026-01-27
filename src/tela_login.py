import streamlit as st
import time
import base64
# Importe as funções do SEU projeto conforme sua estrutura de pastas
from src.database import db as client
from src.utils_seguranca import gerar_hash
from src import verificar_login # Assumindo que verificar_login está no __init__.py ou similar

def carregar_svg_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

@st.dialog("Criar uma conta no Clariô")
def popup_cadastro():
    st.markdown("<p style='opacity: 0.8; font-size: 0.9em;'>Preencha os dados abaixo.</p>", unsafe_allow_html=True)
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome", placeholder="Nome")
            sobrenome = st.text_input("Sobrenome", placeholder="Sobrenome")
            email_cad = st.text_input("E-mail", placeholder="seu@email.com")
        with c2:
            telefone = st.text_input("Telefone", placeholder="+41 ...")
            pais = st.text_input("País", placeholder="Suíça")
            cidade = st.text_input("Cidade", placeholder="Genebra")

        senha_cad = st.text_input("Senha", type="password", placeholder="Nova senha")
        confirmar_senha = st.text_input("Confirme a Senha", type="password", placeholder="Repita a senha")

        if st.button("Finalizar e Entrar", use_container_width=True):
            if senha_cad != confirmar_senha:
                st.error("Senhas diferentes!")
            else:
                try:
                    senha_hash = gerar_hash(senha_cad).decode('utf-8')
                    novo_usuario = {
                        "nome": nome, "sobrenome": sobrenome, "email": email_cad,
                        "pais": pais, "cidade": cidade, "senha": senha_hash, "telefone": telefone
                    }
                    client.table("usuarios").insert(novo_usuario).execute()
                    st.success("Bem-vindo!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro no cadastro: {e}")

def renderizar_login():
    """Apenas a lógica visual e de validação do Login"""
    logo_dark_data = carregar_svg_base64("img/clario_logo_dark.svg")
    logo_light_data = carregar_svg_base64("img/clario_logo_light.svg")

    st.markdown(f"""
        <style>
        .stApp {{ background-color: var(--background-color) !important; }}
        .logo-light-mode {{ display: block; }}
        .logo-dark-mode {{ display: none; }}
        @media (prefers-color-scheme: dark) {{
            .logo-light-mode {{ display: none !important; }}
            .logo-dark-mode {{ display: block !important; }}
        }}
        div.stButton > button {{
            background-color: #e73469 !important;
            color: white !important;
            border-radius: 25px !important;
            height: 3.5em !important;
            font-weight: 600 !important;
        }}
        </style>
        <div style="display: flex; justify-content: center; margin-top: 40px; margin-bottom: 20px;">
            <img class="logo-light-mode" src="data:image/svg+xml;base64,{logo_dark_data}" width="300">
            <img class="logo-dark-mode" src="data:image/svg+xml;base64,{logo_light_data}" width="300">
        </div>
    """, unsafe_allow_html=True)

    _, col_central, _ = st.columns([1, 1.5, 1])

    with col_central:
        st.markdown("<h2 style='text-align: center; font-size: 1.3em;'>Olá! Acesse sua conta</h2>", unsafe_allow_html=True)
        email = st.text_input("E-mail", placeholder="seu@email.com", key="login_email")
        senha = st.text_input("Senha", type="password", placeholder="Sua senha", key="login_pass")

        if st.button("Continuar", use_container_width=True):
            if verificar_login(email, senha):
                st.session_state.logado = True
                st.session_state.usuario_email = email
                st.toast("Autenticado!", icon="🚀")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("E-mail ou senha incorretos.")

        st.markdown("<p style='text-align: center; margin: 20px 0;'>— ou —</p>", unsafe_allow_html=True)
        if st.button("Criar uma conta agora", use_container_width=True):
            popup_cadastro()