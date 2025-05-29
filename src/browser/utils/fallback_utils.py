from src.config.logger import logger

def tentar_captura_com_fallback(funcao_primaria, fallback_js=None, driver=None, campo="campo"):
    """
    Tenta executar a função principal e, se falhar, tenta executar um fallback com JavaScript.

    Args:
        funcao_primaria (callable): Função Python principal para tentar primeiro.
        fallback_js (str): Código JavaScript como fallback.
        driver (webdriver): Instância do Selenium WebDriver.
        campo (str): Nome descritivo do campo para logs.

    Returns:
        str: Valor extraído ou string vazia em caso de falha.
    """
    try:
        return funcao_primaria()
    except Exception as e:
        logger.warning(f"[{campo}] Falha na extração principal: {e}")

        if fallback_js and driver:
            try:
                resultado = driver.execute_script(fallback_js)
                if resultado:
                    logger.info(f"[{campo}] Extraído via fallback JS.")
                    return resultado
            except Exception as js_e:
                logger.error(f"[{campo}] Falha ao executar fallback JS: {js_e}")

        logger.warning(f"[{campo}] não encontrado.")
        return ""
