import streamlit as st

# 1. Configuração da Página
st.set_page_config(
    page_title="Clariô Finance",
    page_icon="img/clario_logo_dark.svg",  # Ícone da aba (favicon)
    layout="centered",
    initial_sidebar_state="expanded"
)


# 2. Injeção de CSS Global (Crucial para o tema Híbrido)
# Isso permite que os elementos mudem de cor sozinhos
def carregar_estilos_globais():
    st.markdown("""
        <style>
        /* Classe para cards (usado na função de 'construção') */
        .clario-card {
            /* Usa a cor de fundo secundária do tema atual (cinza claro ou escuro) */
            background-color: var(--secondary-background-color);
            /* Borda sutil com transparência para funcionar no branco e no preto */
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 10px;
            padding: 20px;
            margin-top: 10px;
        }

        /* Ajuste fino para textos dentro dos cards */
        .clario-card p {
            color: var(--text-color);
            opacity: 0.8;
        }

        /* Lógica para logo na Sidebar (se usar PNGs) */
        /* [data-theme="light"] .logo-img { background-image: url('https://eyyqaqtqylpmvhcfvtmn.supabase.co/storage/v1/object/public/logo/clario_escuro.png'); } */
        /* [data-theme="dark"] .logo-img { background-image: url('https://eyyqaqtqylpmvhcfvtmn.supabase.co/storage/v1/object/public/logo/clario_claro.png'); } */
        </style>
    """, unsafe_allow_html=True)


carregar_estilos_globais()

# Importações (Mantidas conforme seu original)
from src.views.tela_login import renderizar_login
from src.views.tela_dashboard import renderizar_dashboard
from src.views.tela_transacao import renderizar_nova_transacao
from src.views.sidebar import renderizar_sidebar
from src.views.tela_configuracao import renderizar_configuracoes
from src.views.tela_cartao_credito import renderizar_tela_cartao
from src.views.tela_investimento import renderizar_investimentos


# Função auxiliar para telas em construção (Refatorada para CSS Dinâmico)
def renderizar_construcao(titulo):
    # Agora usamos a classe CSS .clario-card definida acima
    # e removemos os estilos 'chumbados' (hardcoded)
    st.markdown(f"""
        <div class="clario-card">
            <h2 style="color: #E73469; margin:0;">{titulo}</h2>
            <p>Módulo em desenvolvimento.</p>
        </div>
    """, unsafe_allow_html=True)


# Lógica Principal
if "logado" not in st.session_state or not st.session_state.logado:
    renderizar_login()

else:
    # Renderiza Sidebar e captura a página selecionada
    page = renderizar_sidebar()

    # Roteamento
    if page == "Dashboard":
        renderizar_dashboard()

    elif page == "Transações":
        renderizar_nova_transacao()

    elif page == "Cartão de Crédito":
        renderizar_tela_cartao()

    elif page == "Investimentos":
        renderizar_investimentos()

    elif page == "Configurações":
        renderizar_configuracoes()