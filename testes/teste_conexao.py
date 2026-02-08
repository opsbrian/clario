# --- DEBUG SUPABASE (Remover depois) ---
st.write("--- DEBUG INFO ---")
st.write(f"User ID Session: {st.session_state.user.id}")
# Tenta buscar SEM FILTRO DE USUÁRIO para ver se o banco bloqueia
teste_geral = supabase.table("transacoes_bancarias").select("id_trans_bank", "valor").limit(5).execute()
st.write(f"Teste Geral (Sem Filtro): {len(teste_geral.data)} registros encontrados")
if not teste_geral.data:
    st.error("ERRO: O banco retornou vazio mesmo sem filtro. Verifique o RLS no Supabase!")
else:
    st.success("Conexão OK! O problema é o ID do usuário.")
st.write("------------------")