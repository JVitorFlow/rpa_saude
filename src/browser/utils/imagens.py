import os
import socket
from datetime import datetime
from src.config.logger import logger


def capturar_screenshot(driver, screenshot_name, screenshot_path):
    """
    Captura um screenshot da tela atual do navegador e salva com um nome padronizado.

    :param driver: Instância do WebDriver (Selenium).
    :param screenshot_name: Nome do screenshot a ser salvo.
    :param screenshot_path: Diretório base onde o screenshot será armazenado.
    :return: Caminho completo do arquivo salvo.
    """
    agora = datetime.now()
    hostname = socket.gethostname()

    # Criando a estrutura de diretórios: /ano/mês/dia/máquina
    caminho_diretorio = os.path.join(
        screenshot_path, agora.strftime("%Y"), agora.strftime("%m"), agora.strftime("%d"), hostname
    )

    # Criar diretório se não existir
    os.makedirs(caminho_diretorio, exist_ok=True)

    # Nome do arquivo com timestamp
    nome_arquivo = f"{agora.strftime('%y-%m-%d_%H-%M-%S-%f')}_{screenshot_name}.png"
    caminho_completo = os.path.join(caminho_diretorio, nome_arquivo)

    # Capturar a tela e salvar
    driver.get_screenshot_as_file(caminho_completo)
    logger.info(f"Screenshot salvo em: {caminho_completo}")

    return caminho_completo
