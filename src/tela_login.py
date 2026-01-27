import streamlit as st
import time
import base64
from src.database import db as client
from src.utils_seguranca import gerar_hash
from src import verificar_login


# --- FUNÇÃO AUXILIAR PARA CARREGAR AS LOGOS SEM ERRO DE CACHE ---
def carregar_svg_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""


# --- 1. FUNÇÃO DO POPUP DE CADASTRO ---
@st.dialog("Criar uma conta no Clariô")
def popup_cadastro():
    # Usamos variáveis CSS (var) para que o popup também mude de cor sozinho
    st.markdown("""
        <p style='color: var(--text-color); opacity: 0.8; font-size: 0.9em; margin-bottom: 20px;'>
        Preencha os dados abaixo para começar sua jornada financeira.
        </p>
    """, unsafe_allow_html=True)

    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome", placeholder="Nome", label_visibility="collapsed")
            sobrenome = st.text_input("Sobrenome", placeholder="Sobrenome", label_visibility="collapsed")
            email = st.text_input("E-mail", placeholder="seu@email.com", label_visibility="collapsed")
        with c2:
            telefone = st.text_input("Telefone", placeholder="+41 ...", label_visibility="collapsed")
            pais = st.text_input("País", placeholder="Suíça", label_visibility="collapsed")
            cidade = st.text_input("Cidade", placeholder="Genebra", label_visibility="collapsed")

        senha = st.text_input("Senha", type="password", placeholder="Nova senha", label_visibility="collapsed")
        confirmar_senha = st.text_input("Confirme a Senha", type="password", placeholder="Repita a senha",
                                        label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Finalizar e Entrar", use_container_width=True, key="btn_cadastro"):
            if senha != confirmar_senha:
                st.error("Senhas diferentes!")
            else:
                try:
                    senha_hash = gerar_hash(senha).decode('utf-8')
                    novo_usuario = {
                        "nome": nome, "sobrenome": sobrenome, "email": email,
                        "pais": pais, "cidade": cidade,
                        "senha": senha_hash, "telefone": telefone
                    }
                    client.table("usuarios").insert(novo_usuario).execute()
                    st.success("Bem-vindo!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")


# --- 2. TELA DE LOGIN COM INTELIGÊNCIA DE TEMA ---
def renderizar_login():
    # Carregamos os dados das imagens
    logo_dark_data = carregar_svg_base64("img/clario_logo_light.svg")
    logo_light_data = carregar_svg_base64("img/clario_logo_dark.svg")

    # Injeção de CSS com Variáveis Dinâmicas e Media Queries
    st.markdown(f"""
        <style>
        /* 1. RESET E FUNDO ADAPTÁVEL */
        .block-container {{ padding-top: 0rem !important; }}
        .stApp {{ background-color: var(--background-color) !important; }}

        /* 2. LÓGICA DE TROCA DE LOGO AUTOMÁTICA */
        .logo-light-mode {{ display: block; }}
        .logo-dark-mode {{ display: none; }}

        @media (prefers-color-scheme: dark) {{
            .logo-light-mode {{ display: none !important; }}
            .logo-dark-mode {{ display: block !important; }}
        }}

        /* 3. ESTILIZAÇÃO DOS INPUTS (Seguindo o Tema) */
        .stTextInput>div>div>input {{
            background-color: var(--secondary-background-color) !important;
            color: var(--text-color) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            height: 3.5em !important;
        }}

        /* 4. BOTÃO ROSA CLARIÔ (IMUTÁVEL) */
        div.stButton > button {{
            background-color: #e73469 !important;
            color: white !important;
            border-radius: 25px !important;
            height: 3.5em !important;
            border: none !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 12px rgba(231, 52, 105, 0.2) !important;
        }}

        /* 5. TEXTOS E CAPTIONS */
        h2, p, .stCaption {{ color: var(--text-color) !important; }}
        </style>

        <div style="display: flex; justify-content: center; margin-top: 40px; margin-bottom: 20px;">
            <img class="logo-light-mode" src="data:image/svg+xml;base64,{logo_dark_data}" width="300">
            <img class="logo-dark-mode" src="data:image/svg+xml;base64,{logo_light_data}" width="300">
        </div>
    """, unsafe_allow_html=True)

    _, col_central, _ = st.columns([1, 1.5, 1])

    with col_central:
        st.markdown("<h2 style='text-align: center; font-size: 1.3em;'>Olá! Acesse sua conta</h2>",
                    unsafe_allow_html=True)

        email = st.text_input("E-mail", placeholder="seu@email.com", label_visibility="collapsed", key="login_email")
        senha = st.text_input("Senha", type="password", placeholder="Sua senha", label_visibility="collapsed",
                              key="login_pass")

        if st.button("Continuar", use_container_width=True):
            if not email or not senha:
                st.warning("Preencha todos os campos.")
            else:
                # Chama a lógica que criamos no pacote 'src'
                if verificar_login(email, senha):
                    st.session_state.logado = True
                    st.session_state.usuario_email = email

                    st.toast("Autenticado com sucesso!", icon="🚀")
                    time.sleep(1)  # Delay para o usuário ler o toast
                    st.rerun()  # FAZ O APP VOLTAR AO TOPO E ENTRAR NO DASHBOARD
                else:
                    st.error("E-mail ou senha incorretos.")

        st.markdown("<p style='text-align: center; margin: 20px 0;'>— ou —</p>", unsafe_allow_html=True)

        if st.button("Criar uma conta agora", use_container_width=True):
            popup_cadastro()

        st.caption(f"<div style='text-align: center; margin-top: 30px; opacity: 0.6;'>Genebra, Suíça</div>",
                   unsafe_allow_html=True)