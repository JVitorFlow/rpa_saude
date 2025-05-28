import re

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.browser.utils.element_utils import (capturar_texto_por_xpath,
                                             capturar_valor_input_por_xpath)
from src.browser.utils.frame_manager import (mudar_para_iframe,
                                             voltar_para_frame_padrao)
from src.config.logger import logger


def extrair_dados_paciente(driver):
    """Extrai informações do paciente na tela do SHIFT."""
    try:
        idade_texto = capturar_texto_por_xpath(
            driver, "//div[@id='lblDataNascimento']//span"
        )
        match_idade = re.search(r'\((\d+)\s+anos', idade_texto)
        idade_paciente = int(match_idade.group(1)) if match_idade else None

        # Clica em 'Fontes pagadoras' e aguarda a exibição da seção "Dados cadastrais"
        fonte_pagadoras = driver.find_element(
            By.XPATH, "//span[contains(text(),'Fontes pagadoras')]"
        )
        fonte_pagadoras.click()
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//span[normalize-space()='Dados cadastrais']")
            )
        )
        logger.info("Tela 'Dados cadastrais' carregada com sucesso.")

        # Extrai a raça/etnia
        raca_etinia = capturar_valor_input_por_xpath(
            driver,
            "//span[contains(text(), 'Raça/Cor do paciente')]/ancestor::td/following-sibling::td//input[@type='text']",
        )

        raca_etinia = capturar_valor_input_por_xpath(
            driver,
            "//span[contains(text(), 'Raça/Cor do paciente')]/ancestor::td/following-sibling::td//input[@type='text']",
        )

        dados = {
            'idade_paciente': idade_paciente,
            'raca_etinia': raca_etinia,
        }

        logger.info(f'Dados do paciente extraídos: {dados}')
        return dados

    except Exception as e:
        logger.error(f'Erro ao extrair dados do paciente: {str(e)}')
        return {}


def extrair_informacoes_paciente(driver) -> dict:
    """
    Aguarda a tela 'Manutenção de indivíduo' carregar e extrai as informações
    de Data de Nascimento, Sexo e CNS.

    Retorna um dicionário com as chaves:
      - "Data de nascimento"
      - "Sexo"
      - "CNS"
    """

    voltar_para_frame_padrao(driver)

    logger.info("Aguardando a tela 'Manutenção de indivíduo' carregar...")

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//div[@class='ng-star-inserted' and contains(.,'Manutenção de indivíduo')]",
            )
        )
    )
    logger.info("Tela 'Manutenção de indivíduo' carregada com sucesso.")

    if not mudar_para_iframe(
        driver, "//sn-modal-frame[@class='ng-star-inserted']//iframe"
    ):
        logger.error(
            "Não foi possível acessar o frame //sn-modal-frame[@class='ng-star-inserted']//iframe"
        )
        return False

    # 3. Extrai valores do formulário
    informacoes_paciente = {
        'data_nascimento': capturar_valor_input_por_xpath(
            driver, "//input[@name='$V_DataNascimento']"
        ),
        'Sexo': capturar_valor_input_por_xpath(
            driver, "(//div[@id='formularioCadastro.Sexo']//input)[2]"
        ),
        'CNS': capturar_valor_input_por_xpath(
            driver, "//div[@id='formularioCadastro.CNS']//input"
        ),
    }

    return informacoes_paciente


def obter_nome_paciente(driver):
    """Obtém o nome do paciente na tela do SHIFT."""
    try:
        campo_nome_paciente = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@id='lblPaciente']//input")
            )
        )
        nome_paciente = campo_nome_paciente.get_attribute('value').strip()

        logger.info(f'Nome do paciente extraído: {nome_paciente}')
        return nome_paciente

    except TimeoutException:
        logger.error('Erro: Nome do paciente não encontrado na tela.')
        return None
