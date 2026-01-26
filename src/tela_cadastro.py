import streamlit as st
import time
from src.database import client  # Importamos o cliente que configuramos
from src.utils_seguranca import gerar_hash


def renderizar_cadastro():
    st.title("📝 Criar Conta no Clariô")
    st.markdown("Preencha os campos abaixo para começar sua jornada financeira.")

    # Criando o formulário com os campos que você definiu no SQL
    with st.form("form_cadastro"):
        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("Nome")
            email = st.text_input("E-mail")
            pais = st.text_input("País")

        with col2:
            sobrenome = st.text_input("Sobrenome")
            telefone = st.text_input("Telefone")
            cidade = st.text_input("Cidade")

        senha = st.text_input("Crie uma Senha", type="password")
        confirmar_senha = st.text_input("Confirme a Senha", type="password")

        submit = st.form_submit_button("Finalizar Cadastro")

        if submit:
            if senha != confirmar_senha:
                st.error("As senhas não coincidem!")
            elif not nome or not email or not senha:
                st.error("Por favor, preencha os campos obrigatórios (Nome, E-mail e Senha).")
            else:
                try:
                    # 1. Criptografa a senha antes de enviar
                    senha_hash = gerar_hash(senha).decode('utf-8')

                    # 2. Prepara o dicionário para o Supabase
                    novo_usuario = {
                        "nome": nome,
                        "sobrenome": sobrenome,
                        "email": email,
                        "senha": senha_hash,
                        "telefone": telefone,
                        "pais": pais,
                        "cidade": cidade
                    }

                    # 3. Faz o INSERT no banco
                    client.table("usuarios").insert(novo_usuario).execute()

                    st.success("Conta criada com sucesso!")
                    time.sleep(2)
                    st.session_state['tela_atual'] = 'login'  # Muda para tela de login
                    st.rerun()

                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")

    if st.button("Já tenho conta? Voltar para Login"):
        st.session_state['tela_atual'] = 'login'
        st.rerun()