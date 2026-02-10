import streamlit as st
import time
from datetime import date
from src.services.supabase_client import supabase
from src.services.cookie_service import salvar_token_no_cookie
from src.services.auth_service import login_user, enviar_email_recuperacao

# --- CONFIGURAÇÃO DAS IMAGENS ---
URL_PARA_FUNDO_CLARO = "https://eyyqaqtqylpmvhcfvtmn.supabase.co/storage/v1/object/public/logo/clario_escuro.png"
URL_PARA_FUNDO_ESCURO = "https://eyyqaqtqylpmvhcfvtmn.supabase.co/storage/v1/object/public/logo/clario_claro.png"


# --- POPUP DE CADASTRO ---
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

        if submitted:
            if senha_cad != confirmar_senha:
                st.error("Senhas não coincidem")
            else:
                try:
                    auth_response = supabase.auth.sign_up({
                        "email": email_cad, "password": senha_cad,
                        "options": {"data": {"nome": nome, "full_name": f"{nome} {sobrenome}"}}
                    })
                    # O Trigger do banco vai salvar a data de nascimento na tabela usuarios
                    # Mas precisamos garantir que o formato esteja certo
                    if auth_response.user:
                        # Força atualização da data no perfil público (caso o trigger falhe ou demore)
                        supabase.table("usuarios").insert({
                            "id_usuario": auth_response.user.id,
                            "email": email_cad,
                            "data_nascimento": str(nascimento),
                            "nome": nome
                        }, upsert=True).execute()

                        st.success("Cadastro realizado! Verifique seu e-mail.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.warning("Verifique o e-mail.")
                except Exception as e:
                    st.error(f"Erro: {e}")


# --- TELA PRINCIPAL ---
def renderizar_login():
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    st.markdown(f"""
        <style>
        .block-container {{ padding-top: 0rem !important; padding-bottom: 0rem !important; margin-top: 0rem !important; }}
        .login-logo-container {{ width: 100%; display: flex; justify-content: center; margin-top: -60px; margin-bottom: 10px; z-index: 1; }}
        div.stButton > button[kind="primary"], div.stButton > button[kind="secondary"] {{
            background-color: #E73469 !important; border: 1px solid #E73469 !important; color: white !important;
            border-radius: 8px !important; height: 3em !important; font-weight: 600 !important;
        }}
        div.stButton > button[kind="tertiary"] {{
            color: #E73469 !important; border: none !important; background: transparent !important;
            text-decoration: none !important; font-size: 0.9em !important;
        }}
        .login-logo-img {{
            width: 100%; max-width: 500px; height: 200px; background-size: contain; 
            background-repeat: no-repeat; background-position: center; transition: background-image 0.3s ease-in-out;
        }}
        .login-logo-img {{ background-image: url('{URL_PARA_FUNDO_CLARO}'); }}
        [data-theme="dark"] .login-logo-img {{ background-image: url('{URL_PARA_FUNDO_ESCURO}') !important; }}
        </style>
    """, unsafe_allow_html=True)

    _, col_central, _ = st.columns([1, 3, 1])

    with col_central:
        st.markdown('<div class="login-logo-container"><div class="login-logo-img"></div></div>',
                    unsafe_allow_html=True)

        # ESTADO A: LOGIN
        if st.session_state.auth_mode == "login":
            st.markdown("<h3 style='text-align: center; margin-top: 0px;'>Acesse sua conta</h3>",
                        unsafe_allow_html=True)

            email = st.text_input("E-mail", placeholder="seu@email.com", key="login_email")
            senha = st.text_input("Senha", type="password", key="login_pass")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Entrar", use_container_width=True, type="primary", icon=":material/login:"):
                user, erro = login_user(email, senha)

                if user:
                    # --- NOVO: SALVA O TOKEN NA MÁQUINA DO USUÁRIO ---
                    # Precisamos pegar o token da sessão atual
                    session = supabase.auth.get_session()
                    if session:
                        salvar_token_no_cookie(session.access_token)

                    st.session_state.user = user
                    st.session_state.logado = True
                    st.rerun()
                else:
                    st.error(erro)

            if st.button("Esqueci minha senha", type="tertiary", use_container_width=True, icon=":material/key:"):
                st.session_state.auth_mode = "recovery"
                st.rerun()

            st.markdown(
                """<div style='text-align: center; margin: 15px 0; opacity: 0.5; font-size: 0.8em;'>— ou —</div>""",
                unsafe_allow_html=True)

            if st.button("Criar nova conta", type="secondary", use_container_width=True, icon=":material/person_add:"):
                popup_cadastro()

        # ESTADO B: RECUPERAÇÃO (ATUALIZADO)
        elif st.session_state.auth_mode == "recovery":
            st.markdown("<h3 style='text-align: center; margin-top: 0px;'>Recuperar Senha</h3>", unsafe_allow_html=True)
            st.info("Para sua segurança, confirme seus dados.")

            email_rec = st.text_input("E-mail Cadastrado", key="rec_email")

            # --- CAMPO DE DATA ADICIONADO ---
            nascimento_rec = st.date_input("Data de Nascimento", value=None,
                                           min_value=date(1920, 1, 1), max_value=date.today(), format="DD/MM/YYYY")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Validar e Enviar Link", use_container_width=True, type="primary", icon=":material/send:"):
                if not email_rec or not nascimento_rec:
                    st.warning("Preencha todos os campos.")
                else:
                    # Passa os DOIS valores para o serviço
                    ok, msg = enviar_email_recuperacao(email_rec, nascimento_rec)
                    if ok:
                        st.success(msg)
                        time.sleep(3)
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    else:
                        st.error(msg)

            if st.button("Voltar para Login", type="tertiary", use_container_width=True, icon=":material/arrow_back:"):
                st.session_state.auth_mode = "login"
                st.rerun()