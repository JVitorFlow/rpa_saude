from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.config.logger import logger


def buscar_prefixo_numero_recipiente(driver):
    """
    Acessa a aba 'Recipientes' no SHIFT e retorna o prefixo de 10 dígitos
    do primeiro código de barras encontrado (removendo os dois últimos dígitos).
    """
    try:
        logger.info("Buscando e clicando na aba 'Recipientes'...")

        aba_recipientes = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//td[contains(@id, 'btn_4_') and contains(.,'Recipientes')]",
                )
            )
        )
        aba_recipientes.click()
        logger.success("Aba 'Recipientes' clicada com sucesso.")

        logger.info('Coletando os números de recipiente...')
        elementos = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//abbr[starts-with(@id, 'abbrCodBarras_')]")
            )
        )
        lista_recipientes = [e.get_attribute('title') for e in elementos]

        if not lista_recipientes:
            logger.warning('Nenhum recipiente encontrado.')
            return None

        # Remove os 2 últimos dígitos do primeiro recipiente
        prefixo = lista_recipientes[0][:10]
        logger.success(f'Prefixo de recipiente identificado: {prefixo}')
        return prefixo

    except TimeoutException:
        logger.error(
            "Erro ao acessar a aba 'Recipientes' ou localizar os recipientes."
        )
        return None
    except Exception as e:
        logger.error(f'Erro inesperado ao buscar recipiente: {e}')
        return None
