import streamlit as st
import time
from src.autenticacao import verificar_credenciais


def renderizar_login():
    # 1. CSS Customizado: Central de Estilo do seu app
    st.markdown(f"""
        <style>   
        /* 1. AJUSTE PARA ELIMINAR SCROLL E SUBIR O CONTEÚDO */
        .block-container {{
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
        }}

        /* SOBE A LOGO E O TÍTULO PARA ECONOMIZAR ESPAÇO VERTICAL */
        .stImage {{
            margin-top: -20px !important;
        }}

        h2 {{
            margin-top: -10px !important;
            margin-bottom: 10px !important;
        }}
         
        /* COR DE FUNDO DO APP INTEIRO */
        .stApp {{
            background-color: #f6f6f6; /* Atualmente Branco */
        }}

        /* BOTÃO PRINCIPAL (Entrar/Continuar) */
        div.stButton > button:first-child {{
            background-color: #e73469; /* Cor de fundo: Rosa Principal */
            color: #ffffff;           /* Cor do texto: Branco */
            border: none;
            border-radius: 25px; 
            font-weight: 600;
            height: 3.5em;
            width: 100%;
            transition: all 0.3s ease;
            /* SOMBRA DO BOTÃO: Altere os valores RGBA para combinar com sua cor principal */
            box-shadow: 0 4px 6px rgba(231, 52, 105, 0.2);
        }}

        /* ESTADO DE HOVER (Quando passa o mouse no botão principal) */
        div.stButton > button:first-child:hover {{
            background-color: transparent;
            color: #e73469  ; /* Rosa um pouco mais escuro para o efeito */
            box-shadow: 0 6px 12px rgba(231, 52, 105, 0.3);
            transform: translateY(-1px);
        }}

        /* ÍCONES (Material Icons) */
        .pink-icon {{
            color: #e73469; /* Rosa Principal aplicado aos ícones */
            vertical-align: middle;
            margin-right: 8px;
        }}

        /* CAMPOS DE INPUT (E-mail e Senha) */
            .stTextInput>div>div>input
                background-color: #ffffff !important; /* Branco puro para saltar aos olhos sobre o form cinza */
                color: #373643 !important;           /* Texto em cinza escuro para legibilidade profissional */
                border-radius: 12px !important;      /* Cantos mais orgânicos */
                border: 2px solid transparent !important; /* Borda invisível por padrão para evitar 'pulos' no foco */
                padding: 12px 15px !important;        /* Mais respiro interno */
                height: 3.5em !important;
                font-size: 1rem !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important; /* Transição suave de fintech */
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important; /* Sombra interna quase imperceptível */
        }}

        /* FOCO NO INPUT (Quando o usuário clica para digitar) */
        .stTextInput>div>div>input:focus {{
            border-color: #e73469;      /* Borda muda para Rosa */
            
        }}

        /* BOTÃO SECUNDÁRIO (Link de Cadastro) */
        div.stButton > button:last-child {{
            background-color: #e73469;
            color: #f6f6f6; /* Cor do texto: Rosa */
            border: none;
            font-weight: 600;
        }}
        </style>

        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    """, unsafe_allow_html=True)

    _, col_central, _ = st.columns([1, 1.5, 1])

    with col_central:
        st.markdown("<br><br>", unsafe_allow_html=True)

        # 2. LOGO: Caso a imagem falhe, a cor do texto fallback é definida aqui
        try:
            st.image("img/clario_logo_dark.svg", width=500)
        except:
            st.markdown("<h1 style='color: #e73469;'>Clariô</h1>", unsafe_allow_html=True)

        # TÍTULO: Cor do texto principal (#373643) e ícone
        st.markdown("""
            <h2 style='color: #373643; font-size: 1.3em;'>
            Olá! Acesse sua conta
                <span class="material-icons pink-icon" style="font-size: 40px;">fingerprint</span>
            </h2>
        """, unsafe_allow_html=True)

        # Inputs (Streamlit herda as cores do CSS acima)
        email = st.text_input("E-mail", placeholder="exemplo@clario.com", label_visibility="collapsed")
        senha = st.text_input("Senha", type="password", placeholder="Sua senha", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)

        # Botão de Entrada (Cor definida no seletor :first-child)
        if st.button("Continuar", use_container_width=True):
            if verificar_credenciais(email, senha):
                st.toast("Bem-vindo de volta!", icon="🚀")
                st.session_state['logado'] = True
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Credenciais inválidas.")

        # TEXTO DIVISOR: Cor cinza neutra (#767676)
        st.markdown("<p style='text-align: center; color: #373643; margin: 20px 0;'>— ou —</p>", unsafe_allow_html=True)

        # Botão de Cadastro (Cor definida no seletor :last-child)
        if st.button("Criar uma conta agora", use_container_width=True):
            st.session_state['tela_atual'] = 'cadastro'
            st.rerun()

        # FOOTER: Texto em cinza escuro #373643 e ícone em rosa
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.caption(f"""
            <div style='text-align: center; color: #373643; font-weight: 400;'>
                <span class="material-icons pink-icon" style="font-size: 14px; vertical-align: middle;">location_on</span>
                Genebra, Suíça
            </div>
        """, unsafe_allow_html=True)