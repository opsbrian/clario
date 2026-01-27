import streamlit as st

st.title("Teste de Conexão com a Nuvem 🐘")

try:
    conn = st.connection("postgresql", type="sql")
    df = conn.query("SELECT 1 as teste;", ttl="0")

    if df.iloc[0]['teste'] == 1:
        st.success("Conexão estabelecida com sucesso! 🎉")
        st.balloons()
except Exception as e:
    st.error("Ops, algo deu errado...")
    st.code(e)