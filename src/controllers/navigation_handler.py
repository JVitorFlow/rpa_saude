from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from src.browser.utils.frame_manager import mudar_para_iframe, voltar_para_frame_padrao
from src.config.logger import logger
import time


def fechar_janela_exame(driver):
    """Fecha a janela do exame anatomopatológico antes de continuar."""
    try:
        logger.info("Fechando a janela do exame anatomopatológico...")

        botao_fechar = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//tbody/tr/td/div[@class='cssGroup']/div[@class='cssGroup']/div[@class='zendiv']/div[6]/div[1]/a[1]",
                )
            )
        )
        botao_fechar.click()
        time.sleep(1)
        logger.info("Janela do exame anatomopatológico fechada com sucesso.")
    except Exception as e:
        logger.warning(f"Erro ao fechar a janela do exame: {str(e)}")


def acessar_informacoes_paciente(driver):
    """Acessa a aba de informações do paciente."""
    try:
        logger.info("Acessando informações do paciente...")

        botao_paciente = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[@id='imgEditarPaciente']//input[@title='Informações do paciente']",
                )
            )
        )
        botao_paciente.click()
        logger.info("Acesso às informações do paciente realizado com sucesso.")
        return True
    except Exception as e:
        logger.warning(f"Erro ao acessar informações do paciente: {str(e)}")


def esperar_tela_manutencao(driver):
    """Espera a tela 'Manutenção de indivíduo' carregar."""
    try:
        logger.info("⏳ Aguardando carregamento da tela 'Manutenção de indivíduo'...")

        voltar_para_frame_padrao(driver)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//div[@class='ng-star-inserted' and contains(.,'Manutenção de indivíduo')]",
                )
            )
        )
        logger.info("Tela 'Manutenção de indivíduo' carregada com sucesso.")

        if mudar_para_iframe(driver, "//iframe[contains(@src, 'ManutencaoPaciente')]"):
            logger.info(
                "Mudança para o iframe 'ManutencaoPaciente' realizada com sucesso."
            )
            return True
        else:
            logger.error("Erro ao mudar para o iframe 'ManutencaoPaciente'.")
            return False
    except Exception as e:
        logger.error(f"Erro ao carregar a tela de manutenção: {str(e)}")
        return False


def fechar_janela_manutencao(driver):
    """Fecha a janela 'Manutenção de indivíduo'."""
    try:
        logger.info("Fechando a janela de 'Manutenção de indivíduo'...")
        voltar_para_frame_padrao(driver)

        botao_fechar = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//span[@class='anticon ant-modal-close-icon anticon-close ng-star-inserted']",
                )
            )
        )
        botao_fechar.click()
        logger.info("Janela de 'Manutenção de indivíduo' fechada com sucesso.")

        voltar_para_frame_padrao(driver)
    except Exception as e:
        logger.warning(f"Erro ao fechar a janela de manutenção: {str(e)}")


def buscar_os_no_sistema(driver, api_client, task_id, item_id, os_numero):
    """Realiza a busca da O.S no sistema."""
    try:
        logger.info(f"🔍 Buscando OS {os_numero} no sistema SHIFT.")

        # Muda para o iframe correto ANTES de tentar buscar a OS
        if not mudar_para_iframe(driver, "//iframe[@id='frmContentZen']"):
            logger.error("Não foi possível acessar o frame da O.S.")
            return False

        # Aguarda o campo de busca estar visível e interagível
        campo_busca = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "(//div[@id='txtCodigoOS']//input[@type='text'])[1]")
            )
        )

        # 🔹 Garante que o campo está vazio ANTES de inserir a O.S
        campo_busca.send_keys(Keys.CONTROL, "a")  # Seleciona tudo
        campo_busca.send_keys(Keys.DELETE)  # Apaga o conteúdo existente
        
        if campo_busca.get_attribute("value") != "":
            driver.execute_script("arguments[0].value = '';", campo_busca)  # Força limpeza via JavaScript

        # 🔹 Insere a O.S no campo
        campo_busca.send_keys(os_numero, Keys.ENTER)

        try:
            WebDriverWait(driver, 5).until(EC.alert_is_present())
            alerta = driver.switch_to.alert
            mensagem_alerta = alerta.text.strip()

            logger.warning(f"⚠️ Alerta detectado: {mensagem_alerta}")

            # 🔹 Fecha o alerta
            alerta.accept()
            logger.info("✅ Alerta fechado com sucesso.")

            # 🔹 Atualiza a API informando erro na busca da O.S.
            api_client.update_task(
                task_id=task_id,
                shift_result=f"O.S. não encontrada: {os_numero}",
                status="ERROR",
            )
            api_client.update_item(
                item_id=item_id,
                status="ERROR",
                observation="O.S. não encontrada no SHIFT.",
            )

            return False  # ❌ Não segue com a extração, pois a OS não foi encontrada

        except TimeoutException:
            logger.info("✅ Nenhum alerta detectado. Continuando o fluxo.")

        logger.success(f"O.S {os_numero} buscada com sucesso.")
        return True

    except TimeoutException:
        logger.error(f"Campo de busca não carregou para OS {os_numero}.")
        return False

    except Exception as e:
        logger.error(f"Erro ao buscar OS {os_numero}: {str(e)}")
        return False
