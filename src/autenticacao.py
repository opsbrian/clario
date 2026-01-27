# src/autenticacao.py
from src.database import buscar_usuario_por_email
from src.utils_seguranca import verificar_hash  # Alterado de verificar_senha para verificar_hash

def verificar_login(email, senha):
    usuario = buscar_usuario_por_email(email)
    if usuario:
        # Aqui também deve usar o nome correto
        if verificar_hash(senha, usuario['senha']):
            return True
    return False