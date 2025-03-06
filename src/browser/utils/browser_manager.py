from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def iniciar_driver():
    """
    Inicializa o driver Selenium garantindo a compatibilidade com a versão do Chrome instalada.
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Força a instalação do ChromeDriver mais recente compatível
    service = Service(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def finalizar_driver(driver):
    """
    Finaliza o driver Selenium.
    """
    if driver:
        driver.quit()
