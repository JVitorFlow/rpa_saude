import time
import pyautogui
from src.config.logger import logger

def espera_imagem_aparecer(
    imagem: str,
    regiao: tuple = None,
    tolerancia: float = 0.8,
    max_tentativas: int = 50,
    intervalo: float = 0.2
) -> tuple | None:
    """
    Aguarda até que a imagem especificada apareça na tela (ou em uma região),
    movendo o cursor para o local quando encontrada.

    :param imagem: Caminho para o arquivo de imagem que será localizado.
    :param regiao: Tupla (left, top, width, height) definindo a região da tela para busca.
    :param tolerancia: Valor de confiança (0 a 1) para a correspondência da imagem.
    :param max_tentativas: Número máximo de tentativas de localização.
    :param intervalo: Tempo (em segundos) de espera entre as tentativas.
    :return: (x, y) se a imagem for encontrada, ou None se não for encontrada após max_tentativas.
    """
    tentativas = 0

    while tentativas < max_tentativas:
        try:
            # Localiza o centro da imagem na tela/na região
            location = pyautogui.locateCenterOnScreen(imagem, confidence=tolerancia, region=regiao)
            if location:
                x, y = location
                pyautogui.moveTo(x, y)
                logger.info(f"Imagem '{imagem}' encontrada e cursor movido para ({x}, {y}).")
                return (x, y)
            else:
                # Logar apenas a cada 5 tentativas para evitar excesso de logs
                if tentativas % 5 == 0:
                    logger.info(f"Imagem '{imagem}' não encontrada. Tentativa {tentativas+1}/{max_tentativas}...")
            
            tentativas += 1
            time.sleep(intervalo)

        except Exception as e:
            # Em caso de exceções do PyAutoGUI ou algo similar
            if tentativas % 5 == 0:
                logger.error(f"Erro ao procurar imagem '{imagem}': {e} (tentativa {tentativas+1}/{max_tentativas})")
            tentativas += 1
            time.sleep(intervalo)

    logger.warning(f"Número máximo de tentativas ({max_tentativas}) atingido para localizar '{imagem}'.")
    return None
