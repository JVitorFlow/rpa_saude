from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
from src.config.logger import logger


def capturar_valor_input_por_xpath(driver, xpath):
    """
    Captura o valor de um input no Selenium via XPath.
    """
    try:
        valor = driver.find_element(By.XPATH, xpath).get_attribute("value")
        return valor if valor else "Não especificado (NI)"
    except NoSuchElementException:
        return "Não especificado (NI)"


def verificar_opcoes_radiobutton(driver):
    """
    Verifica se o texto do laudo contém alguma das opções do radiobutton do SISMAMA.
    """
    opcoes_radiobutton = {
        "QSL": "Quadrante Superior Lateral",
        "QSM": "Quadrante Superior Medial",
        "QIL": "Quadrante Inferior Lateral",
        "QIM": "Quadrante Inferior Medial",
        "UQLat": "União dos Quadrantes Laterais",
        "UQSup": "União dos Quadrantes Superiores",
        "UQMed": "União dos Quadrantes Mediais",
        "UQInf": "União dos Quadrantes Inferiores",
        "RRA": "Região Retroareolar",
    }

    try:
        texto_laudo = (
            WebDriverWait(driver, 10)
            .until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[33]//span[1]//div[1]//div[1]")
                )
            )
            .text.upper()
        )

        for codigo, descricao in opcoes_radiobutton.items():
            if codigo.upper() in texto_laudo or descricao.upper() in texto_laudo:
                return codigo  # Retorna o código da opção encontrada

        return "Localizacao não especificada (NI)"
    except TimeoutException:
        logger.warning("Não foi possível capturar o radiobutton.")
        return "Localizacao não especificada (NI)"


def capturar_localizacao_lesao(driver):
    """
    Captura a localização da lesão (Mama Direita ou Mama Esquerda).
    """
    try:
        elemento_localizacao = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//div[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'mama direita') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'mama esquerda')]",
                )
            )
        )
        texto_localizacao = elemento_localizacao.text.lower()

        if "mama esquerda" in texto_localizacao:
            return "Mama esquerda"
        elif "mama direita" in texto_localizacao:
            return "Mama direita"
        else:
            return "Localizacao nao especificada (NI)"
    except TimeoutException:
        logger.info("Não foi possível encontrar a localização da lesão.")
        return "Localizacao nao especificada (NI)"


def capturar_innerText_por_xpath(driver, xpath, regex=None):
    """
    Captura o texto interno de um elemento, podendo filtrar com regex.
    """
    try:
        elemento = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        texto_completo = elemento.get_attribute("innerText")

        if regex:
            resultado_regex = re.search(regex, texto_completo)
            if resultado_regex:
                return resultado_regex.group(1)  # Retorna apenas o grupo capturado
            else:
                return "Informação especificada pela regex não encontrada"

        return texto_completo
    except TimeoutException:
        logger.warning(f"Elemento com XPath '{xpath}' não está visível.")
        return ""
    except NoSuchElementException:
        logger.warning(f"Elemento com XPath '{xpath}' não foi encontrado.")
        return ""


def capturar_texto_visivel_com_regex(driver, xpath, regex=None, tempo_espera=10):
    """
    Captura o texto de um elemento no Selenium garantindo que esteja visível, 
    e aplica um regex para extrair um padrão específico.

    Args:
        driver (webdriver): Instância do Selenium WebDriver.
        xpath (str): XPath do elemento a ser capturado.
        regex (str): Expressão regular para extrair um padrão específico (opcional).
        tempo_espera (int): Tempo máximo de espera para o elemento (padrão: 10s).

    Returns:
        str: Texto do elemento ou "Não especificado (NI)" caso não encontrado.
    """
    try:
        elemento = WebDriverWait(driver, tempo_espera).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )

        # Rola a página até o elemento para garantir que ele esteja visível
        driver.execute_script("arguments[0].scrollIntoView();", elemento)

        # Espera o elemento estar visível
        WebDriverWait(driver, tempo_espera).until(
            EC.visibility_of(elemento)
        )

        texto = elemento.text.strip()

        if regex:
            match = re.search(regex, texto)
            if match:
                return match.group(1)

        return texto if texto else "Não especificado (NI)"

    except TimeoutException:
        logger.warning(f"Timeout ao localizar elemento com XPath: {xpath}")
        return "Não especificado (NI)"
    
    except NoSuchElementException:
        logger.warning(f"Elemento não encontrado: {xpath}")
        return "Não especificado (NI)"
    
    except Exception as e:
        logger.error(f"Erro inesperado ao capturar texto: {str(e)}")
        return "Não especificado (NI)"


def encontrar_elemento(driver, by, valor, tempo_espera=20):
    """
    Localiza um elemento na página e retorna-o.
    """
    try:
        return WebDriverWait(driver, tempo_espera).until(
            EC.presence_of_element_located((by, valor))
        )
    except TimeoutException:
        logger.warning(f"Elemento não encontrado após {tempo_espera} segundos: {valor}")
        return None

    
def capturar_texto_por_xpath(driver, xpath, tempo_espera=10):
    """
    Captura o texto de um elemento via XPath, aguardando até que esteja visível.

    Args:
        driver (webdriver): Instância do Selenium WebDriver.
        xpath (str): XPath do elemento a ser capturado.
        tempo_espera (int): Tempo máximo de espera para o elemento (padrão: 10s).

    Returns:
        str: O texto do elemento ou "Não especificado (NI)" caso não encontrado.
    """
    try:
        elemento = WebDriverWait(driver, tempo_espera).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        texto = elemento.text.strip()

        if texto:
            return texto
        else:
            logger.warning(f"Elemento encontrado, mas sem texto visível: {xpath}")
            return "Não especificado (NI)"

    except TimeoutException:
        logger.warning(f"Timeout ao localizar elemento com XPath: {xpath}")
        return "Não especificado (NI)"

    except NoSuchElementException:
        logger.warning(f"Elemento não encontrado: {xpath}")
        return "Não especificado (NI)"

    except Exception as e:
        logger.error(f"Erro inesperado ao capturar texto: {str(e)}")
        return "Não especificado (NI)"
