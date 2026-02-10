import pandas as pd


def formatar_brl(valor):
    """
    Recebe um valor float/int e retorna string formatada: R$ 1.234,56
    Trata None e NaN como 0,00.
    """
    if valor is None or pd.isna(valor):
        valor = 0.0

    # Formata padrão americano com 2 decimais: 1,234.56
    texto = f"{valor:,.2f}"

    # Inverte caracteres para o padrão BR: 1.234,56
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")

    return f"R$ {texto}"