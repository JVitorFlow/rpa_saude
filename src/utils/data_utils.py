from datetime import datetime
from src.config.logger import logger

def formatar_data_iso(data):
    """
    Converte uma data do formato 'DD/MM/YYYY - HH:MM:SS' para 'YYYY-MM-DDTHH:MM:SSZ'.

    Args:
        data (str): Data no formato 'DD/MM/YYYY - HH:MM:SS'.

    Returns:
        str: Data formatada no padrão ISO 8601 ou None se inválida.
    """
    try:
        if not data:
            return None

        # Converter '01/03/2024 - 18:34:36' -> '2024-03-01T18:34:36Z'
        data_formatada = datetime.strptime(data, "%d/%m/%Y - %H:%M:%S").strftime("%Y-%m-%dT%H:%M:%SZ")
        return data_formatada

    except ValueError as e:
        logger.error(f"⚠️ Erro ao converter data '{data}': {str(e)}")
        return None
