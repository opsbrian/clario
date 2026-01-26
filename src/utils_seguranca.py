import bcrypt


def gerar_hash(senha_plana):
    """
    Recebe '1234' e retorna o hash seguro (bytes).
    """
    senha_bytes = senha_plana.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha_bytes, salt)


def verificar_senha(senha_plana, senha_hash_banco):
    """
    Compara a senha digitada com o hash do banco.
    O Supabase pode retornar o hash como string, então tratamos isso.
    """
    senha_digitada_bytes = senha_plana.encode('utf-8')

    # Se vier do Supabase como string, converte para bytes
    if isinstance(senha_hash_banco, str):
        senha_hash_banco = senha_hash_banco.encode('utf-8')

    return bcrypt.checkpw(senha_digitada_bytes, senha_hash_banco)