from datetime import datetime

from config.logger import logger


def formatar_data(data):
    """
    Formata uma string de data em diferentes formatos para 'yyyy-mm-dd' ou 'yyyy-mm-dd hh:mm:ss'.

    Aceita:
    - 'dd/mm/yyyy'
    - 'dd/mm/yyyy - hh:mm:ss'

    Retorna:
    - Data no formato 'yyyy-mm-dd' ou 'yyyy-mm-dd hh:mm:ss'
    """
    try:
        if " - " in data:
            return datetime.strptime(data, "%d/%m/%Y - %H:%M:%S").strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        else:
            return datetime.strptime(data, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        logger.error(f"Erro ao converter a data: {data}. Formato inválido.")
        return None  # Retorna None caso a conversão falhe
