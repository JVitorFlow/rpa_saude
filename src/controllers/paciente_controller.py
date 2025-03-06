import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from src.browser.utils.element_utils import (
    capturar_texto_por_xpath,
    capturar_valor_input_por_xpath,
)
from src.config.logger import logger


def extrair_dados_paciente(driver):
    """Extrai informações do paciente na tela do SHIFT."""
    try:
        idade_texto = capturar_texto_por_xpath(
            driver, "//div[@id='lblDataNascimento']//span"
        )
        match_idade = re.search(r"\((\d+)\s+anos", idade_texto)
        idade_paciente = int(match_idade.group(1)) if match_idade else None

        raca_etinia = capturar_valor_input_por_xpath(
            driver,
            "//span[contains(text(), 'Raça/Cor do paciente')]/ancestor::td/following-sibling::td//input[@type='text']",
        )
        cns = capturar_valor_input_por_xpath(
            driver, "//div[@id='formularioCadastro.CNS']//input"
        )

        dados = {
            "idade_paciente": idade_paciente,
            "raca_etinia": raca_etinia,
            "cartao_sus": cns,
        }

        logger.info(f"Dados do paciente extraídos: {dados}")
        return dados

    except Exception as e:
        logger.error(f"Erro ao extrair dados do paciente: {str(e)}")
        return {}


def obter_nome_paciente(driver):
    """Obtém o nome do paciente na tela do SHIFT."""
    try:
        campo_nome_paciente = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@id='lblPaciente']//input")
            )
        )
        nome_paciente = campo_nome_paciente.get_attribute("value").strip()

        logger.info(f"Nome do paciente extraído: {nome_paciente}")
        return nome_paciente

    except TimeoutException:
        logger.error("Erro: Nome do paciente não encontrado na tela.")
        return None
