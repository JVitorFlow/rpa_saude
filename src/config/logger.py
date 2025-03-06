from loguru import logger
from .config import Config
import os

# Certificar-se de que o diretório de logs existe
os.makedirs(Config.LOG_DIR, exist_ok=True)


# Configuração do logger
logger.add(
    sink=Config.LOG_FILE,  # Caminho do arquivo de log
    rotation="1 MB",  # Roda o arquivo ao atingir 1 MB
    retention="7 days",  # Retém arquivos de log por 7 dias
    compression="zip",  # Compacta arquivos antigos
    level="INFO",  # Nível mínimo de log
    format="{time:YYYY-MM-DD HH:mm:ss} | <level>{level: <8}</level> | {message}",
)

# Logger configurado para ser usado diretamente em outros módulos
__all__ = ["logger"]
