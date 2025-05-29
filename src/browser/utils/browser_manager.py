from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def iniciar_driver(headless=True):
    """
    Inicializa o driver Selenium garantindo a compatibilidade com a versão do Chrome instalada.
    """
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")  # usar o modo moderno
        chrome_options.add_argument("--window-size=1920,1080")

    # Estabilidade e compatibilidade
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Impede que o site detecte que é automação
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Instalação automática e compatível do driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver

def finalizar_driver(driver):
    """
    Finaliza o driver Selenium.
    """
    if driver:
        driver.quit()
