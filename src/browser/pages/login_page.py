from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.config.logger import logger


class ShiftLoginPage:
    """
    Classe que representa a página de login do sistema SHIFT.
    """

    def __init__(self, driver):
        self.driver = driver
        self.input_usuario = (By.XPATH, "//input[@placeholder='Escreva seu usuário']")
        self.input_senha = (By.XPATH, "//input[@placeholder='Escreva sua senha']")
        self.btn_login = (By.XPATH, "//button[@type='submit']")
        self.alerta_usuario_autenticado = (
            By.XPATH,
            "//p[contains(text(), 'Já existe um usuário autenticado')]",
        )
        self.alerta_erro_login = (
            By.CSS_SELECTOR,
            ".ant-notification-notice-description"
        )


    def acessar_pagina(self, url):
        logger.info(f"Acessando a URL: {url}")
        self.driver.get(url)

    def preencher_usuario(self, usuario):
        logger.info("Preenchendo usuário.")
        self.driver.find_element(*self.input_usuario).send_keys(usuario)

    def preencher_senha(self, senha):
        logger.info("Preenchendo senha.")
        self.driver.find_element(*self.input_senha).send_keys(senha)

    def clicar_login(self):
        logger.info("Clicando no botão de login.")
        self.driver.find_element(*self.btn_login).click()


    def verificar_erro_login(self):
        """
        Valida se o alerta de 'Usuário e/ou senha inválido(s)' do Ant Design Notification aparece.
        Retorna True se encontrado, False caso contrário.
        """
        try:
            elemento = WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(self.alerta_erro_login)
            )
            texto = elemento.text.strip().lower()
            if "usuário e/ou senha inválido" in texto:
                logger.warning("Alerta de erro de login detectado: Usuário e/ou senha inválido(s)")
                return True
            else:
                logger.warning(f"Notificação diferente encontrada: '{texto}'")
                return False
        except TimeoutException:
            logger.info("Nenhum alerta de erro de login encontrado.")
            return False

