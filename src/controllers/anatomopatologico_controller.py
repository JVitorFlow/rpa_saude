import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.browser.utils.element_utils import (capturar_innerText_por_xpath,
                                             capturar_localizacao_lesao,
                                             capturar_texto_visivel_com_regex,
                                             verificar_opcoes_radiobutton)
from src.config.logger import logger


def extrair_dados_anatomopatologico(driver):
    """Extrai informações do exame anatomopatológico no SHIFT."""
    try:
        aba_procedimentos = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//a[@name='abaConsulta']//span[contains(text(),'Procedimentos')]",
                )
            )
        )
        aba_procedimentos.click()
        logger.info('Aba Procedimentos clicada com sucesso.')

        elemento_procedimento = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//abbr[contains(text(), 'ANATOMO PATOLOGICO DE MAMA')]",
                )
            )
        )

        actions = ActionChains(driver)
        actions.double_click(elemento_procedimento).perform()

        try:
            data_coleta = capturar_innerText_por_xpath(
                driver,
                "(//span[@class='estiloSpan estiloColuna']/div[contains(text(), ' - ')])[1]",
            )
        except:
            data_coleta = ''
            logger.warning("Campo 'data_coleta' ausente.")

        try:
            data_liberacao = capturar_innerText_por_xpath(
                driver,
                "(//span[@class='estiloSpan estiloColuna']/div[contains(text(), ' - ')])[2]",
            )
        except:
            data_liberacao = ''
            logger.warning("Campo 'data_liberacao' ausente.")

        try:
            tamanho_lesao = capturar_texto_visivel_com_regex(
                driver,
                "//span[contains(text(), 'Dimensão') and contains(text(), 'fragmento')]",
                r'(\d+,\d+ cm)',
            )
        except:
            tamanho_lesao = ''
            logger.warning("Campo 'tamanho_lesao' ausente.")

        try:
            caracteristica_lesao = capturar_localizacao_lesao(driver)
        except:
            caracteristica_lesao = ''
            logger.warning("Campo 'caracteristica_lesao' ausente.")

        try:
            localizacao_lesao = verificar_opcoes_radiobutton(driver)
        except:
            localizacao_lesao = ''
            logger.warning("Campo 'localizacao_lesao' ausente.")

        dados = {
            'data_coleta': data_coleta
            if data_coleta
            else "Campo 'data_coleta' nao especificada (NI)",
            'data_liberacao': data_liberacao
            if data_liberacao
            else "Campo 'data_liberacao' nao especificada (NI)",
            'tamanho_lesao': tamanho_lesao
            if tamanho_lesao
            else "Campo 'tamanho_lesao' nao especificada (NI)",
            'caracteristica_lesao': caracteristica_lesao
            if caracteristica_lesao
            else "Campo 'caracteristica_lesao' nao especificada (NI)",
            'localizacao_lesao': localizacao_lesao
            if localizacao_lesao
            else "Campo 'localizacao_lesao' nao especificada (NI)",
        }

        logger.info(f'Dados do exame anatomopatológico extraídos: {dados}')
        return dados

    except Exception as e:
        logger.error(f'Erro ao extrair exame anatomopatológico: {str(e)}')
        return {}
