from selenium.webdriver.common.by import By

from src.browser.utils.element_utils import capturar_valor_input_por_xpath
from src.config.logger import logger


def extrair_dados_endereco(driver):
    """Extrai os dados de endereço do paciente."""
    try:
        driver.find_element(
            By.XPATH, "//td[contains(text(), 'Endereço')]"
        ).click()

        dados = {
            'codigo_postal': capturar_valor_input_por_xpath(
                driver,
                "//div[@id='compositeEndereco.txtCodigoPostalEstrangeiro']//input",
            ),
            'logradouro': capturar_valor_input_por_xpath(
                driver,
                "//div[@id='compositeEndereco.txtLogradouroEstrangeiro']//input",
            ),
            'numero_residencial': capturar_valor_input_por_xpath(
                driver,
                "//div[@id='compositeEndereco.txtNumeroEstrangeiro']//input",
            ),
            'cidade': capturar_valor_input_por_xpath(
                driver,
                "//div[@id='compositeEndereco.txtCidadeEstrageiro']//input",
            ),
            'estado': capturar_valor_input_por_xpath(
                driver,
                "//div[@id='compositeEndereco.txtEstadoEstrangeiro']//input",
            ),
        }

        logger.info(f'Endereço extraído: {dados}')
        return dados

    except Exception as e:
        logger.error(f'Erro ao extrair endereço do paciente: {str(e)}')
        return {}
