from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.logger import logger


def esperar_elemento_visivel(driver, xpath, tempo_espera=10):
    """
    Aguarda até que o elemento especificado pelo XPath esteja visível na página.

    :param driver: Instância do Selenium WebDriver.
    :param xpath: XPath do elemento a ser esperado.
    :param tempo_espera: Tempo máximo de espera em segundos (padrão: 10).
    :return: O elemento encontrado ou None se não for encontrado.
    """
    try:
        return WebDriverWait(driver, tempo_espera).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
    except TimeoutException:
        logger.warning(f"Elemento com XPath '{xpath}' não ficou visível dentro do tempo limite de {tempo_espera} segundos.")
        return None


def esperar_elemento_clicavel(driver, xpath, tempo_espera=10):
    """
    Aguarda até que o elemento especificado pelo XPath esteja clicável.

    :param driver: Instância do Selenium WebDriver.
    :param xpath: XPath do elemento a ser esperado.
    :param tempo_espera: Tempo máximo de espera em segundos (padrão: 10).
    :return: O elemento encontrado ou None se não for encontrado.
    """
    try:
        return WebDriverWait(driver, tempo_espera).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
    except TimeoutException:
        logger.warning(f"Elemento com XPath '{xpath}' não ficou clicável dentro do tempo limite de {tempo_espera} segundos.")
        return None


def esperar_alerta(driver, tempo_espera=10):
    """
    Aguarda até que um alerta esteja presente.

    :param driver: Instância do Selenium WebDriver.
    :param tempo_espera: Tempo máximo de espera em segundos (padrão: 10).
    :return: O alerta encontrado ou None se não for encontrado.
    """
    try:
        return WebDriverWait(driver, tempo_espera).until(EC.alert_is_present())
    except TimeoutException:
        logger.warning(f"Alerta não apareceu dentro do tempo limite de {tempo_espera} segundos.")
        return None


def esperar_carregamento_sumir(driver, xpath, tempo_espera=30):
    """
    Aguarda até que o elemento da tela de carregamento desapareça.

    :param driver: Instância do Selenium WebDriver.
    :param xpath: XPath do elemento da tela de carregamento.
    :param tempo_espera: Tempo máximo de espera em segundos (padrão: 30).
    :return: True se o elemento desaparecer, False caso contrário.
    """
    try:
        WebDriverWait(driver, tempo_espera).until(
            EC.invisibility_of_element_located((By.XPATH, xpath))
        )
        logger.info("Tela de carregamento desapareceu.")
        return True
    except TimeoutException:
        logger.error(f"Tela de carregamento não desapareceu após {tempo_espera} segundos.")
        return False