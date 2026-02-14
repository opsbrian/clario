import streamlit as st
import time
from datetime import date
from src.services.supabase_client import supabase
from src.services.cookie_service import salvar_token_no_cookie
from src.services.auth_service import login_user, enviar_email_recuperacao

# --- CONFIGURAÇÃO DAS IMAGENS ---
# Logo Escura (Texto Preto/Cinza) -> Para usar no Fundo Claro
URL_LOGO_ESCURA = "https://eyyqaqtqylpmvhcfvtmn.supabase.co/storage/v1/object/public/logo/clario_escuro.png"

# Logo Clara (Texto Branco) -> Para usar no Fundo Escuro
URL_LOGO_CLARA = "https://eyyqaqtqylpmvhcfvtmn.supabase.co/storage/v1/object/public/logo/clario_claro.png"


# --- POPUP DE CADASTRO (Modal) ---
@st.dialog("Criar uma conta no Clariô")
def popup_cadastro():
    st.markdown(
        "<p style='color: var(--text-color); opacity: 0.8; font-size: 0.9em; margin-bottom: 15px;'>Preencha os dados abaixo para começar.</p>",
        unsafe_allow_html=True)

    with st.form("form_cadastro", clear_on_submit=False):
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

        st.markdown("<br>", unsafe_allow_html=True)

        submitted = st.form_submit_button("Finalizar Cadastro", use_container_width=True, type="primary")

        if submitted:
            if senha_cad != confirmar_senha:
                st.error("As senhas não coincidem.")
            elif len(senha_cad) < 6:
                st.error("A senha deve ter no mínimo 6 caracteres.")
            else:
                try:
                    auth_response = supabase.auth.sign_up({
                        "email": email_cad,
                        "password": senha_cad,
                        "options": {"data": {"full_name": f"{nome} {sobrenome}"}}
                    })

                    if auth_response.user:
                        user_id = auth_response.user.id
                        try:
                            supabase.table("usuarios").insert({
                                "id_usuario": user_id,
                                "nome": f"{nome} {sobrenome}",
                                "email": email_cad,
                                "data_nascimento": str(nascimento),
                                "pais": pais,
                                "cidade": cidade
                            }).execute()
                        except Exception:
                            pass

                        st.success("Cadastro realizado com sucesso!")
                        time.sleep(1.5)
                        st.session_state.abrir_modal_cadastro = False  # Fecha o modal via estado
                        st.rerun()
                    else:
                        st.warning("Verifique se o e-mail já está cadastrado.")
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")


# --- TELA PRINCIPAL ---
def renderizar_login():
    # 1. Gerenciamento de Estado (Para evitar bugs de piscada)
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    # Estado para controlar o modal manualmente (Bulletproof)
    if "abrir_modal_cadastro" not in st.session_state:
        st.session_state.abrir_modal_cadastro = False

    # 2. CSS Corrigido (Logo e Tema)
    st.markdown(f"""
        <style>
        .block-container {{ padding-top: 3rem !important; padding-bottom: 2rem !important; }}

        .login-logo-container {{ 
            width: 100%; display: flex; justify-content: center; margin-bottom: 25px; 
        }}

        /* LOGO PADRÃO (TEMA CLARO) -> Usa a logo ESCURA */
        .login-logo-img {{
            width: 260px; height: 90px; 
            background-size: contain; background-repeat: no-repeat; background-position: center;
            background-image: url('{URL_LOGO_ESCURA}'); 
            transition: background-image 0.3s ease-in-out;
        }}

        /* LOGO TEMA ESCURO -> Usa a logo CLARA (Branca) */
        [data-theme="dark"] .login-logo-img {{
            background-image: url('{URL_LOGO_CLARA}') !important;
        }}

        div.stButton > button[kind="primary"] {{
            background-color: #E73469 !important; border-color: #E73469 !important; color: white !important; font-weight: 600 !important;
        }}
        div.stButton > button[kind="secondary"] {{
            border-color: #E73469 !important; color: #E73469 !important; background: transparent !important;
        }}
        div.stButton > button[kind="tertiary"] {{
            color: gray !important; text-decoration: none !important; margin-top: -10px;
        }}
        </style>
    """, unsafe_allow_html=True)

    # 3. Layout
    col1, col_central, col3 = st.columns([1, 4, 1])

    with col_central:
        # Logo
        st.markdown('<div class="login-logo-container"><div class="login-logo-img"></div></div>',
                    unsafe_allow_html=True)

        # --- MODO: LOGIN ---
        if st.session_state.auth_mode == "login":
            st.markdown("<h3 style='text-align: center; font-weight: 700; margin-bottom: 20px;'>Acesse sua conta</h3>",
                        unsafe_allow_html=True)

            email = st.text_input("E-mail", placeholder="seu@email.com", key="login_email")
            senha = st.text_input("Senha", type="password", key="login_pass")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Entrar", use_container_width=True, type="primary"):
                user, erro = login_user(email, senha)
                if user:
                    session = supabase.auth.get_session()
                    if session:
                        salvar_token_no_cookie(session.access_token)
                    st.session_state.user = user
                    st.session_state.logado = True
                    st.rerun()
                else:
                    st.error(erro)

            # Botão que ativa o estado do modal
            if st.button("Criar nova conta", type="secondary", use_container_width=True):
                st.session_state.abrir_modal_cadastro = True
                st.rerun()

            # Lógica Blindada: Verifica o estado para abrir o modal
            if st.session_state.abrir_modal_cadastro:
                popup_cadastro()

            if st.button("Esqueci minha senha", type="tertiary", use_container_width=True):
                st.session_state.auth_mode = "recovery"
                st.rerun()

        # --- MODO: RECUPERAÇÃO ---
        elif st.session_state.auth_mode == "recovery":
            st.markdown("<h3 style='text-align: center; font-weight: 700;'>Recuperar Senha</h3>",
                        unsafe_allow_html=True)
            st.info("Informe seus dados para receber o link de redefinição.")

            email_rec = st.text_input("E-mail Cadastrado", key="rec_email")
            nascimento_rec = st.date_input("Data de Nascimento", value=None, min_value=date(1920, 1, 1),
                                           max_value=date.today(), format="DD/MM/YYYY")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Enviar Link", use_container_width=True, type="primary"):
                if not email_rec or not nascimento_rec:
                    st.warning("Preencha todos os campos.")
                else:
                    ok, msg = enviar_email_recuperacao(email_rec, nascimento_rec)
                    if ok:
                        st.success(msg)
                        time.sleep(3)
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    else:
                        st.error(msg)

            if st.button("Voltar ao Login", type="tertiary", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()