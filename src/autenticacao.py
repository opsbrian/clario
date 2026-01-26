from src.database import buscar_usuario_por_email
from src.utils_seguranca import verificar_senha


def verificar_credenciais(email, senha_digitada):
    """
    1. Busca o usuário no Supabase através do e-mail.
    2. Compara a senha digitada com o hash seguro do banco.
    """
    # Busca os dados do usuário no banco (SQL via Supabase)
    usuario_encontrado = buscar_usuario_por_email(email)

    if usuario_encontrado:
        # Recupera o hash da senha que está no banco
        hash_no_banco = usuario_encontrado['senha']

        # Usa a função de segurança para comparar (Criptografia)
        if verificar_senha(senha_digitada, hash_no_banco):
            return True

    # Se não encontrar o usuário ou a senha não bater
    return False