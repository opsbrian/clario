import bcrypt


def gerar_hash(senha: str) -> bytes:
    """
    Cria um hash seguro usando bcrypt com salt aleatório.
    """
    # Transforma a string em bytes
    senha_bytes = senha.encode('utf-8')
    # Gera o salt e o hash
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha_bytes, salt)


def verificar_hash(senha_digitada: str, senha_hash_db: str) -> bool:
    """
    Compara uma senha digitada com o hash salvo no banco.
    Aceita o hash do banco tanto em string quanto em bytes.
    """
    try:
        # Garante que ambos estão em bytes para a comparação do bcrypt
        senha_digitada_bytes = senha_digitada.encode('utf-8')

        if isinstance(senha_hash_db, str):
            senha_hash_db_bytes = senha_hash_db.encode('utf-8')
        else:
            senha_hash_db_bytes = senha_hash_db

        return bcrypt.checkpw(senha_digitada_bytes, senha_hash_db_bytes)
    except Exception as e:
        print(f"Erro na verificação de segurança: {e}")
        return False