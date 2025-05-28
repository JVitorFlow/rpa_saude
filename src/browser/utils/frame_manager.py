from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.config.logger import logger


def mudar_para_iframe(driver, xpath_iframe, tempo_espera=30):
    """Muda o foco do Selenium para um iframe específico."""
    try:
        iframe = WebDriverWait(driver, tempo_espera).until(
            EC.presence_of_element_located((By.XPATH, xpath_iframe))
        )
        driver.switch_to.frame(iframe)
        logger.info(f"Mudança para iframe '{xpath_iframe}' realizada com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Erro ao mudar para iframe '{xpath_iframe}': {str(e)}")
        return False

def voltar_para_frame_padrao(driver):
    """Volta para o frame principal do documento."""
    driver.switch_to.default_content()
    logger.info("Voltando para o frame principal.")
