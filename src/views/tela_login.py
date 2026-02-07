import streamlit as st
import time
import base64
from datetime import date
from src.services.supabase_client import supabase


# --- 1. FUNÇÕES VISUAIS ---
def carregar_svg_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        return ""


# --- 2. POPUP DE RECUPERAÇÃO DE SENHA ---
@st.dialog("Recuperar Senha 🔒")
def popup_reset_senha():
    st.markdown("""
        <p style='font-size: 0.9em; color: #666;'>
        Por segurança, confirme seus dados pessoais. Enviaremos um link para criar uma nova senha.
        </p>
    """, unsafe_allow_html=True)

    with st.form("form_reset"):
        email_reset = st.text_input("E-mail cadastrado")

        nascimento_reset = st.date_input(
            "Confirme sua Data de Nascimento",
            value=None,
            min_value=date(1920, 1, 1),
            max_value=date.today(),
            format="DD/MM/YYYY"
        )

        submitted = st.form_submit_button("Enviar Link de Recuperação", use_container_width=True)

        if submitted:
            if not email_reset or not nascimento_reset:
                st.warning("Preencha todos os campos.")
                return

            try:
                # 1. VERIFICAÇÃO DE SEGURANÇA
                check_user = supabase.table("usuarios") \
                    .select("id_usuario") \
                    .eq("email", email_reset) \
                    .eq("data_nascimento", str(nascimento_reset)) \
                    .execute()

                if check_user.data:
                    # 2. DISPARA O E-MAIL
                    supabase.auth.reset_password_for_email(
                        email_reset,
                        {"redirect_to": "http://localhost:8501/"}
                    )
                    st.success("✅ Tudo certo! Verifique seu e-mail.")
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("❌ Dados incorretos.")
                    st.caption("O e-mail ou a data de nascimento não conferem.")

            except Exception as e:
                st.error("Ocorreu um erro ao processar.")


# --- 3. POPUP DE CADASTRO ---
@st.dialog("Criar uma conta no Clariô")
def popup_cadastro():
    st.markdown("<p style='opacity: 0.8; font-size: 0.9em;'>Preencha os dados abaixo.</p>", unsafe_allow_html=True)

    with st.form("form_cadastro"):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome", placeholder="Seu nome")
            sobrenome = st.text_input("Sobrenome", placeholder="Sobrenome")
            email_cad = st.text_input("E-mail", placeholder="seu@email.com")
        with c2:
            nascimento = st.date_input(
                "Data Nascimento",
                value=date(2000, 1, 1),
                min_value=date(1920, 1, 1),
                max_value=date.today(),
                format="DD/MM/YYYY"
            )
            pais = st.text_input("País", placeholder="Suíça")
            cidade = st.text_input("Cidade", placeholder="Genebra")

        senha_cad = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres")
        confirmar_senha = st.text_input("Confirme a Senha", type="password", placeholder="Repita a senha")

        submitted = st.form_submit_button("Finalizar Cadastro", use_container_width=True, type="primary")

        if submitted:
            if senha_cad != confirmar_senha:
                st.error("As senhas não coincidem!")
                return
            if len(senha_cad) < 6:
                st.error("A senha precisa ter pelo menos 6 caracteres.")
                return

            try:
                # O Python envia os dados como "metadados"
                auth_response = supabase.auth.sign_up({
                    "email": email_cad,
                    "password": senha_cad,
                    "options": {
                        "data": {
                            "nome": nome,
                            "sobrenome": sobrenome,
                            "cidade": cidade,
                            "pais": pais,
                            # Importante: converte data para texto (YYYY-MM-DD)
                            "nascimento": str(nascimento),
                            "full_name": f"{nome} {sobrenome}"
                        }
                    }
                })

                if auth_response.user:
                    st.success("Cadastro realizado! 📩")
                    st.info("Verifique seu e-mail para confirmar a conta antes de entrar.")
                    time.sleep(4)
                    st.rerun()
                else:
                    st.warning("Verifique se você já tem cadastro ou cheque seu e-mail.")

            except Exception as e:
                st.error(f"Erro ao criar conta: {e}")


# --- 4. TELA DE LOGIN ---
def renderizar_login():
    logo_dark = carregar_svg_base64("img/clario_logo_dark.svg")
    logo_light = carregar_svg_base64("img/clario_logo_light.svg")

    st.markdown(f"""
        <style>
        .stApp {{ background-color: var(--background-color); }}

        /* 1. Botão Primário (ENTRAR) - Sólido Rosa */
        div.stButton > button[kind="primary"] {{
            background-color: #e73469 !important;
            border: 1px solid #e73469 !important;
            color: white !important;
            border-radius: 8px !important;
            height: 3em !important;
            font-weight: 600 !important;
        }}
        div.stButton > button[kind="primary"]:hover {{
            background-color: #c92a5b !important;
            border-color: #c92a5b !important;
        }}

        /* 2. Botão Secundário (CRIAR CONTA) - AGORA SÓLIDO ROSA IGUAL AO PRIMÁRIO */
        div.stButton > button[kind="secondary"] {{
            background-color: #e73469 !important; /* Rosa Sólido */
            border: 1px solid #e73469 !important;
            color: white !important; /* Texto Branco */
            border-radius: 8px !important;
            height: 3em !important;
            font-weight: 600 !important;
        }}
        div.stButton > button[kind="secondary"]:hover {{
            background-color: #c92a5b !important;
            border-color: #c92a5b !important;
            color: white !important;
        }}

        /* 3. Botão Terciário (ESQUECI A SENHA) - Link de Texto Rosa */
        div.stButton > button[kind="tertiary"] {{
            color: #E73469 !important;
            border: none !important;
            background: transparent !important;
            text-decoration: none !important;
            font-size: 0.9em !important;
            padding: 0 !important;
        }}
        div.stButton > button[kind="tertiary"]:hover {{
            color: #c92a5b !important;
            background: transparent !important;
            text-decoration: underline !important;
        }}

        .logo-light {{ display: block; margin: 0 auto; }}
        .logo-dark {{ display: none; margin: 0 auto; }}
        @media (prefers-color-scheme: dark) {{
            .logo-light {{ display: none !important; }}
            .logo-dark {{ display: block !important; }}
        }}
        </style>
    """, unsafe_allow_html=True)

    _, col_central, _ = st.columns([1, 1.5, 1])

    with col_central:
        if logo_dark and logo_light:
            st.markdown(f"""
                <div style="text-align: center; margin-bottom: 20px;">
                    <img class="logo-light" src="data:image/svg+xml;base64,{logo_dark}" width="200">
                    <img class="logo-dark" src="data:image/svg+xml;base64,{logo_light}" width="200">
                </div>
            """, unsafe_allow_html=True)
        else:
            st.title("Clariô Finance")

        st.markdown("<h3 style='text-align: center;'>Acesse sua conta</h3>", unsafe_allow_html=True)

        email = st.text_input("E-mail", placeholder="seu@email.com")
        senha = st.text_input("Senha", type="password")

        st.markdown("<br>", unsafe_allow_html=True)

        # Botão Principal (Entrar)
        if st.button("Entrar", use_container_width=True, type="primary"):
            try:
                session = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": senha
                })
                if session:
                    st.session_state.logado = True
                    st.session_state.user = session.user
                    st.rerun()
            except Exception as e:
                st.error("E-mail ou senha incorretos (ou e-mail não confirmado).")

        # Link "Esqueci minha senha"
        if st.button("Esqueci minha senha", type="tertiary", use_container_width=True):
            popup_reset_senha()

        st.markdown(
            "<div style='text-align: center; margin-top: 15px; margin-bottom: 15px; opacity: 0.6;'>— ou —</div>",
            unsafe_allow_html=True)

        # Botão Criar Conta (Agora VISUALMENTE IDÊNTICO ao Entrar)
        if st.button("Criar nova conta", type="secondary", use_container_width=True):
            popup_cadastro()