from datetime import datetime
from src.config.logger import logger

from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def formatar_data_iso(valor: str) -> str:
    """
    Tenta converter uma data no formato 'dd/mm/yyyy' ou 'dd/mm/yyyy HH:MM:SS'
    para o formato ISO 'yyyy-mm-dd' ou 'yyyy-mm-ddTHH:MM:SS'.

    Retorna None se não conseguir converter.
    """
    if not valor:
        return None
    
    # Remove espaços extras e possíveis duplicações
    valor = valor.strip()
    # Caso existam dois "//", remove duplicações
    valor = valor.replace("//", "/")

    # 1. Tenta parsear como dd/mm/yyyy
    try:
        dt = datetime.strptime(valor, "%d/%m/%Y")
        # Se quiser só data sem horário, use dt.date().isoformat()
        # Se preferir 'yyyy-mm-ddTHH:MM:SS', mantenha dt.isoformat().
        return dt.date().isoformat()
    except ValueError:
        pass  # Se falhar, tenta outro formato

    # 2. Tenta parsear como dd/mm/yyyy HH:MM:SS
    formatos_possiveis = ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y - %H:%M:%S"]
    for formato in formatos_possiveis:
        try:
            dt = datetime.strptime(valor, formato)
            return dt.isoformat()
        except ValueError:
            continue
    
    logger.error(f"Erro ao converter data '{valor}': formato não suportado.")
    return None

