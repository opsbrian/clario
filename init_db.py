from src.database import criar_usuario_admin

print("🚀 Conectando ao Supabase para criar o usuário inicial...")

try:
    criar_usuario_admin()
    print("✨ Processo finalizado!")
except Exception as e:
    print(f"❌ Ocorreu um erro: {e}")