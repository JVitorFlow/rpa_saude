from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from src.browser.utils.element_utils import (
    capturar_innerText_por_xpath,
    capturar_texto_visivel_com_regex,
    capturar_localizacao_lesao,
    verificar_opcoes_radiobutton,
)
from src.config.logger import logger


def extrair_dados_anatomopatologico(driver):
    """Extrai informações do exame anatomopatológico no SHIFT."""
    try:
        driver.find_element(
            By.XPATH, "//a[@name='abaConsulta']//span[contains(text(),'Procedimentos')]"
        ).click()

        elemento_procedimento = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//abbr[contains(text(), 'ANATOMO PATOLOGICO DE MAMA')]")
            )
        )

        # Duplo clique para abrir o exame
        from selenium.webdriver.common.action_chains import ActionChains

        actions = ActionChains(driver)
        actions.double_click(elemento_procedimento).perform()

        # Rolar até o elemento
        elemento_tamanho_lesao = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//span[contains(text(), 'Dimensão') and contains(text(), 'fragmento')]",
                )
            )
        )
        driver.execute_script("arguments[0].scrollIntoView();", elemento_tamanho_lesao)
        time.sleep(1)

        # Extrai os dados
        dados = {
            "data_coleta": capturar_innerText_por_xpath(
                driver,
                "(//span[@class='estiloSpan estiloColuna']/div[contains(text(), ' - ')])[1]",
            ),
            "data_liberacao": capturar_innerText_por_xpath(
                driver,
                "(//span[@class='estiloSpan estiloColuna']/div[contains(text(), ' - ')])[2]",
            ),
            "tamanho_lesao": capturar_texto_visivel_com_regex(
                driver,
                "//span[contains(text(), 'Dimensão') and contains(text(), 'fragmento')]",
                r"(\d+,\d+ cm)",
            ),
            "caracteristica_lesao": capturar_localizacao_lesao(driver),
            "localizacao_lesao": verificar_opcoes_radiobutton(driver),
        }

        logger.info(f"📌 Dados do exame anatomopatológico extraídos: {dados}")
        return dados

    except Exception as e:
        logger.error(f"Erro ao extrair exame anatomopatológico: {str(e)}")
        return {}
