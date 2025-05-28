from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.config.logger import logger


class OSConsultaPage:
    """
    Classe que representa a página para acessar "O.S Consulta" no sistema SHIFT.
    """

    def __init__(self, driver):
        self.driver = driver
        self.menu_button = (By.XPATH, "//button[contains(@class, 'ant-btn-circle')]")
        self.acesso_rapido_input = (By.XPATH, "//input[@placeholder='Acesso Rápido']")
        self.os_consulta_option = (By.XPATH, "//div[contains(@class, 'ant-select-item-option-content') and text()='O.S. Consulta']")

    def clicar_menu(self):
        """
        Clica no botão do menu lateral.
        """
        try:
            logger.info("Clicando no botão do menu lateral.")
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.menu_button)
            ).click()
            logger.info("Botão do menu clicado com sucesso.")
        except TimeoutException:
            logger.error("Falha ao clicar no botão do menu lateral.")
            raise Exception("Erro ao acessar o menu.")

    def pesquisar_os_consulta(self, texto):
        """
        Digita no campo de "Acesso Rápido" e seleciona a opção "O.S. Consulta".
        """
        try:
            logger.info(f"Digitando '{texto}' no campo 'Acesso Rápido'.")
            input_acesso_rapido = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(self.acesso_rapido_input)
            )
            input_acesso_rapido.clear()
            input_acesso_rapido.send_keys(texto)

            logger.info("Aguardando a opção 'O.S. Consulta' ficar disponível.")
            opcao_os_consulta = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'ant-select-item-option-content') and normalize-space(text())='O.S. Consulta']"))
            )

            opcao_os_consulta.click()
            logger.info("Opção 'O.S. Consulta' selecionada com sucesso.")
        except TimeoutException:
            logger.error("Falha ao pesquisar ou selecionar 'O.S. Consulta'.")
            raise Exception("Erro ao acessar a opção O.S. Consulta.")
