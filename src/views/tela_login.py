import streamlit as st
import time
from datetime import date
from src.services.supabase_client import supabase

# --- 1. CONFIGURAÇÃO DAS IMAGENS ---
URL_PARA_FUNDO_CLARO = "https://eyyqaqtqylpmvhcfvtmn.supabase.co/storage/v1/object/public/logo/clario_escuro.png"
URL_PARA_FUNDO_ESCURO = "https://eyyqaqtqylpmvhcfvtmn.supabase.co/storage/v1/object/public/logo/clario_claro.png"


# --- 2. POPUP DE RECUPERAÇÃO DE SENHA ---
@st.dialog("Recuperar Senha")
def popup_reset_senha():
    st.markdown("""
        <p style='font-size: 0.9em; color: var(--text-color); opacity: 0.7;'>
        Por segurança, confirme seus dados pessoais. Enviaremos um link para criar uma nova senha.
        </p>
    """, unsafe_allow_html=True)

    with st.form("form_reset"):
        email_reset = st.text_input("E-mail cadastrado")
        nascimento_reset = st.date_input("Confirme sua Data de Nascimento", value=None, min_value=date(1920, 1, 1),
                                         max_value=date.today(), format="DD/MM/YYYY")

        submitted = st.form_submit_button("Enviar Link de Recuperação", use_container_width=True,
                                          icon=":material/lock_reset:")
        # ... (lógica mantida) ...
        if submitted:
            if not email_reset or not nascimento_reset:
                st.warning("Preencha todos os campos.")
            else:
                try:
                    check_user = supabase.table("usuarios").select("id_usuario").eq("email", email_reset).eq(
                        "data_nascimento", str(nascimento_reset)).execute()
                    if check_user.data:
                        supabase.auth.reset_password_for_email(email_reset,
                                                               {"redirect_to": "https://clario.streamlit.app/"})
                        st.success("Link enviado!")
                        time.sleep(3)
                        st.rerun()
                    else:
                        st.error("Dados incorretos.")
                except:
                    st.error("Erro ao processar.")


# --- 3. POPUP DE CADASTRO ---
@st.dialog("Criar uma conta no Clariô")
def popup_cadastro():
    st.markdown("<p style='color: var(--text-color); opacity: 0.8; font-size: 0.9em;'>Preencha os dados abaixo.</p>",
                unsafe_allow_html=True)
    with st.form("form_cadastro"):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome")
            sobrenome = st.text_input("Sobrenome")
            email_cad = st.text_input("E-mail")
        with c2:
            nascimento = st.date_input("Data Nascimento", value=date(2000, 1, 1), min_value=date(1920, 1, 1),
                                       max_value=date.today(), format="DD/MM/YYYY")
            pais = st.text_input("País", placeholder="Suíça")
            cidade = st.text_input("Cidade", placeholder="Genebra")

        senha_cad = st.text_input("Senha", type="password")
        confirmar_senha = st.text_input("Confirme a Senha", type="password")

        submitted = st.form_submit_button("Finalizar Cadastro", use_container_width=True, type="primary",
                                          icon=":material/person_add:")

        # ... (lógica mantida) ...
        if submitted:
            if senha_cad != confirmar_senha:
                st.error("Senhas não coincidem")
            else:
                try:
                    auth_response = supabase.auth.sign_up({
                        "email": email_cad, "password": senha_cad,
                        "options": {"data": {"nome": nome, "full_name": f"{nome} {sobrenome}"}}
                    })
                    if auth_response.user:
                        st.success("Cadastro realizado!")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.warning("Verifique o e-mail.")
                except Exception as e:
                    st.error(f"Erro: {e}")


# --- 4. TELA DE LOGIN ---
def renderizar_login():
    st.markdown(f"""
        <style>
        /* 1. Remove totalmente o espaço do container principal do Streamlit */
        .block-container {{
            padding-top: 0rem !important; 
            padding-bottom: 0rem !important;
            margin-top: 1rem !important;
        }}

        /* 2. Container da Logo com MARGEM NEGATIVA */
        /* Se quiser subir mais, aumente o número negativo (ex: -80px) */
        .login-logo-container {{
            width: 100%;
            display: flex;
            justify-content: center;
            margin-top: -60px;  /* <--- CONTROLE A ALTURA AQUI */
            margin-bottom: 10px;
            z-index: 1; /* Garante que fique acima de outros elementos se sobrepor */
        }}

        /* 3. Estilo dos Botões */
        div.stButton > button[kind="primary"], 
        div.stButton > button[kind="secondary"] {{
            background-color: #E73469 !important;
            border: 1px solid #E73469 !important;
            color: white !important;
            border-radius: 8px !important;
            height: 3em !important;
            font-weight: 600 !important;
        }}
        div.stButton > button[kind="primary"]:hover, 
        div.stButton > button[kind="secondary"]:hover {{
            background-color: #c92a5b !important;
            border-color: #c92a5b !important;
        }}
        div.stButton > button[kind="tertiary"] {{
            color: #E73469 !important;
            border: none !important;
            background: transparent !important;
            text-decoration: none !important;
            font-size: 0.9em !important;
        }}

        /* 4. A Logo em si */
        .login-logo-img {{
            width: 100%;         
            max-width: 500px;    
            height: 200px;       
            background-size: contain; 
            background-repeat: no-repeat;
            background-position: center;
            transition: background-image 0.3s ease-in-out;
        }}

        /* TEMA PADRÃO (Light) */
        .login-logo-img {{ background-image: url('{URL_PARA_FUNDO_CLARO}'); }}

        /* TEMA ESCURO (Dark) */
        [data-theme="dark"] .login-logo-img {{ background-image: url('{URL_PARA_FUNDO_ESCURO}') !important; }}
        </style>
    """, unsafe_allow_html=True)

    _, col_central, _ = st.columns([1, 3, 1])

    with col_central:
        # A DIV da imagem
        st.markdown('<div class="login-logo-container"><div class="login-logo-img"></div></div>',
                    unsafe_allow_html=True)

        st.markdown("<h3 style='text-align: center; margin-top: 0px;'>Acesse sua conta</h3>", unsafe_allow_html=True)

        email = st.text_input("E-mail", placeholder="seu@email.com")
        senha = st.text_input("Senha", type="password")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Entrar", use_container_width=True, type="primary", icon=":material/login:"):
            try:
                session = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                if session:
                    st.session_state.logado = True
                    st.session_state.user = session.user
                    st.rerun()
            except:
                st.error("E-mail ou senha incorretos.")

        if st.button("Esqueci minha senha", type="tertiary", use_container_width=True, icon=":material/key:"):
            popup_reset_senha()

        st.markdown("""<div style='text-align: center; margin: 15px 0; opacity: 0.5; font-size: 0.8em;'>— ou —</div>""",
                    unsafe_allow_html=True)

        if st.button("Criar nova conta", type="secondary", use_container_width=True, icon=":material/person_add:"):
            popup_cadastro()