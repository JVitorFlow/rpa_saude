from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from src.browser.utils.fallback_utils import tentar_captura_com_fallback

from src.browser.utils.element_utils import (
    capturar_innerText_por_xpath,
    capturar_localizacao_lesao,
    capturar_texto_visivel_com_regex,
    verificar_opcoes_radiobutton,
)
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
            data_coleta = tentar_captura_com_fallback(
                funcao_primaria=lambda: capturar_innerText_por_xpath(
                    driver,
                    "(//span[@class='estiloSpan estiloColuna']/div[contains(text(), ' - ')])[1]",
                ),
                fallback_js="""
                    return Array.from(document.querySelectorAll('span'))
                        .map(el => el.textContent.trim())
                        .find(text => 
                            text.toLowerCase().includes('coleta') && /\\d{2}\\/\\d{2}\\/\\d{4}/.test(text)
                        ) || "";
                """,
                driver=driver,
                campo='data_coleta',
            )

        except:
            data_coleta = ''
            logger.warning("Campo 'data_coleta' ausente.")

        try:
            data_liberacao = tentar_captura_com_fallback(
                funcao_primaria=lambda: capturar_innerText_por_xpath(
                    driver,
                    "(//span[@class='estiloSpan estiloColuna']/div[contains(text(), ' - ')])[2]",
                ),
                fallback_js="""
                    return Array.from(document.querySelectorAll('span'))
                        .map(el => el.textContent.trim())
                        .find(text => 
                            text.toLowerCase().includes('liberação') && /\\d{2}\\/\\d{2}\\/\\d{4}/.test(text)
                        ) || "";
                """,
                driver=driver,
                campo='data_liberacao',
            )

        except:
            data_liberacao = ''
            logger.warning("Campo 'data_liberacao' ausente.")

        try:
            tamanho_lesao = tentar_captura_com_fallback(
                funcao_primaria=lambda: capturar_texto_visivel_com_regex(
                    driver,
                    "//span[contains(text(), 'Dimensão') and contains(text(), 'fragmento')]",
                    r'(\d+,\d+\s?cm)',
                ),
                fallback_js="""
                    const spanTextos = Array.from(document.querySelectorAll('span'))
                        .map(el => el.textContent.trim());
                    
                    for (const texto of spanTextos) {
                        const match = texto.match(/(\\d+,\\d+\\s?cm)/);
                        if (match) return match[1];
                    }
                    return "";
                """,
                driver=driver,
                campo='tamanho_lesao',
            )
            
        except:
            tamanho_lesao = ''
            logger.warning("Campo 'tamanho_lesao' ausente.")

        try:
            caracteristica_lesao = tentar_captura_com_fallback(
                funcao_primaria=lambda: capturar_localizacao_lesao(driver),
                fallback_js="""
                    return Array.from(document.querySelectorAll('span'))
                        .map(el => el.textContent.trim())
                        .find(text => 
                            text.toLowerCase().includes('caracter') || text.toLowerCase().includes('lesão')
                        ) || "";
                """,
                driver=driver,
                campo='caracteristica_lesao',
            )

        except:
            caracteristica_lesao = ''
            logger.warning("Campo 'caracteristica_lesao' ausente.")

        try:
            localizacao_lesao = tentar_captura_com_fallback(
                funcao_primaria=lambda: verificar_opcoes_radiobutton(driver),
                fallback_js="""
                    const text = document.body.innerText.toLowerCase();
                    if (text.includes('mama esquerda')) return 'Mama esquerda';
                    if (text.includes('mama direita')) return 'Mama direita';
                    return 'Localizacao nao especificada (NI)';
                """,
                driver=driver,
                campo='localizacao_lesao',
            )

        except:
            localizacao_lesao = ''
            logger.warning("Campo 'localizacao_lesao' ausente.")

        dados = {
            'data_coleta': (
                data_coleta
                if data_coleta
                else "Campo 'data_coleta' nao especificada (NI)"
            ),
            'data_liberacao': (
                data_liberacao
                if data_liberacao
                else "Campo 'data_liberacao' nao especificada (NI)"
            ),
            'tamanho_lesao': (
                tamanho_lesao
                if tamanho_lesao
                else "Campo 'tamanho_lesao' nao especificada (NI)"
            ),
            'caracteristica_lesao': (
                caracteristica_lesao
                if caracteristica_lesao
                else "Campo 'caracteristica_lesao' nao especificada (NI)"
            ),
            'localizacao_lesao': (
                localizacao_lesao
                if localizacao_lesao
                else "Campo 'localizacao_lesao' nao especificada (NI)"
            ),
        }

        logger.info(f'Dados do exame anatomopatológico extraídos: {dados}')
        return dados

    except Exception as e:
        logger.error(f'Erro ao extrair exame anatomopatológico: {str(e)}')
        return {}
