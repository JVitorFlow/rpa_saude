import logging
from datetime import datetime

from src.config.logger import logger

logger = logging.getLogger(__name__)


def formatar_data_iso(valor: str) -> str:
    """
    Tenta converter uma data no formato 'dd/mm/yyyy' ou 'dd/mm/yyyy HH:MM:SS'
    para o formato ISO 'yyyy-mm-dd' ou 'yyyy-mm-ddTHH:MM:SS'.

    Retorna None se não conseguir converter.
    """
    if not valor:
        return None

    valor = valor.strip()
    valor = valor.replace('//', '/')

    try:
        dt = datetime.strptime(valor, '%d/%m/%Y')
        return dt.date().isoformat()
    except ValueError:
        pass

    formatos_possiveis = ['%d/%m/%Y %H:%M:%S', '%d/%m/%Y - %H:%M:%S']
    for formato in formatos_possiveis:
        try:
            dt = datetime.strptime(valor, formato)
            return dt.isoformat()
        except ValueError:
            continue

    logger.error(f"Erro ao converter data '{valor}': formato não suportado.")
    return None
