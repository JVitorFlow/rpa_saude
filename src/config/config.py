import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()


class BaseConfig:
    """Classe base para configurações globais."""

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    os.makedirs(LOG_DIR, exist_ok=True)

    LOG_FILE = os.path.join(LOG_DIR, "main.log")


class ShiftConfig:
    """Configurações específicas para o sistema SHIFT."""

    URL = os.getenv("URL_SHIFT")
    USUARIO = os.getenv("USUARIO_SHIFT")
    SENHA = os.getenv("SENHA_SHIFT")
    NUMERO_CNES = os.getenv("NUMERO_CNES")

    # Garantir que as variáveis essenciais estão definidas
    if not URL or not USUARIO or not SENHA:
        raise ValueError(
            "Variáveis de ambiente do SHIFT não estão configuradas corretamente!"
        )


class APIConfig:
    """Configurações para a API."""

    API_URL = os.getenv("API_URL", "http://localhost:8000")


class ScreenshotConfig:
    """Configuração para capturas de tela da automação."""

    SCREENSHOT_PATH = os.path.join(BaseConfig.LOG_DIR, "screenshots")
    os.makedirs(SCREENSHOT_PATH, exist_ok=True)  # Criar diretório se não existir


class OpenAIConfig:
    """Configurações para integração com a OpenAI."""

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    if not OPENAI_API_KEY:
        raise ValueError(
            "A variável de ambiente OPENAI_API_KEY não está configurada! Verifique seu .env."
        )


class Config(BaseConfig, ShiftConfig, APIConfig, ScreenshotConfig, OpenAIConfig):
    """
    Classe que combina todas as configurações em um único ponto de acesso.
    Herda de BaseConfig, ShiftConfig, APIConfig e ScreenshotConfig e OpenAIConfig.
    """

    ROBOT_ID = os.getenv("ROBOT_ID", 1)
