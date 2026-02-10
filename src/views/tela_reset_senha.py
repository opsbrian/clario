import streamlit as st
import time
from src.services.auth_service import atualizar_senha_usuario


def renderizar_reset_senha():
    # CSS para centralizar o card
    st.markdown("""
        <style>
        .reset-card {
            max_width: 500px;
            margin: 50px auto;
            padding: 30px;
            background-color: var(--secondary-background-color);
            border-radius: 12px;
            border: 1px solid rgba(128,128,128, 0.2);
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    # Container Centralizado
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
            <div class="reset-card">
                <h2 style="color: #E73469;">Redefinir Senha</h2>
                <p>Crie uma nova senha segura para sua conta.</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("form_nova_senha_reset"):
            nova_senha = st.text_input("Nova Senha", type="password")
            confirmar = st.text_input("Confirme a Senha", type="password")

            submit = st.form_submit_button("Salvar Nova Senha", type="primary", use_container_width=True)

            if submit:
                if nova_senha != confirmar:
                    st.error("As senhas não coincidem.")
                elif len(nova_senha) < 6:
                    st.warning("A senha deve ter no mínimo 6 caracteres.")
                else:
                    sucesso, msg = atualizar_senha_usuario(nova_senha)
                    if sucesso:
                        st.success("Senha alterada com sucesso! Redirecionando...")
                        time.sleep(2)

                        # Limpa o parâmetro da URL para sair do modo reset
                        st.query_params.clear()

                        # Recarrega para ir ao Dashboard
                        st.rerun()
                    else:
                        st.error(f"Erro: {msg}")