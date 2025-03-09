from pywinauto import Application
from pywinauto.timings import TimeoutError
from src.config.logger import logger
from .image_services import preparar_imagem_para_ocr
import pytesseract


import pyautogui
import re


def validar_popup_data_realizacao(app: Application) -> bool:
    """
    Verifica se um pop-up de 'Data de realização' (ou com título 'Confirma') aparece.
    Se aparecer, extrai o texto, loga, clica em 'Não' (ou 'OK'), pressiona F6 e clica na aba "Requisição".
    Retorna True se o pop-up for encontrado e tratado; caso contrário, retorna False.
    """
    try:
        dialog = app.window(class_name="TMessageForm", title="Confirma")
        dialog.wait("exists visible", timeout=4)
        if dialog.exists(timeout=4):

            dialog.draw_outline()

            rect = dialog.rectangle()
            left = rect.left
            top = rect.top
            width = rect.width()
            height = rect.height()

            texto_capturado = captura_texto_pop_up(left, top, width, height)
            logger.info(f"Pop-up de data de realização detectado: {texto_capturado}")

            try:
                botao_nao = dialog.child_window(title="Não", control_type="Button")
                botao_nao.click_input()
                logger.info("Clicou em 'Não' para o pop-up de data.")
            except Exception:
                botao_ok = dialog.child_window(title="OK", control_type="Button")
                botao_ok.click_input()
                logger.info("Clicou em 'OK' para o pop-up de data.")

            # Pressiona F6 para cancelar o cadastro atual
            pyautogui.press("F6")
            # Acessa a janela principal e clica na aba "Requisição"
            janela_principal = app.window(
                title="Requisição de Exame Histopatológico - MAMA"
            )
            aba_requisicao = janela_principal.child_window(
                title="Requisição", control_type="TabItem"
            )
            aba_requisicao.click_input()
            return True

    except TimeoutError:
        logger.info("Nenhum pop-up de 'Data de realização' encontrado.")
        return False
    except Exception as e:
        logger.error(f"Erro ao validar pop-up de data: {e}")
        return False


def tratar_pop_up_informacao(app: Application) -> None:
    """
    Aguarda e trata o pop-up de 'Informação' após salvar os dados.
    Se o pop-up for encontrado, extrai o texto via OCR e clica em OK.
    """
    try:
        dialog = app.window(class_name="#32770", title="Informação")
        dialog.wait("exists visible", timeout=4)
        if dialog.exists(timeout=4):
            partes = [
                child.window_text()
                for child in dialog.children()
                if child.friendly_class_name() == "Static"
            ]
            mensagem = " ".join(partes).replace("\r", " ").replace("\n", " ").strip()
            logger.info(f"Pop-up 'Informação': {mensagem}")
            dialog.child_window(title="OK", control_type="Button").click()
        else:
            logger.info("Pop-up 'Informação' não encontrado.")
    except TimeoutError:
        logger.warning("O pop-up 'Informação' não apareceu dentro do tempo esperado.")


def captura_texto_pop_up(left: int, top: int, width: int, height: int) -> str:
    """
    Captura uma região da tela e extrai texto via OCR.
    Retorna o texto extraído, aplicando correções pontuais.
    """
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    imagem_preparada = preparar_imagem_para_ocr(screenshot)
    custom_config = r"--oem 3 --psm 11"
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    texto_bruto = pytesseract.image_to_string(imagem_preparada, config=custom_config)

    # Correções simples de OCR
    correcoes = {
        "Data de realizagdo": "Data de realização",
        "informagdo": "informação",
    }
    texto_corrigido = texto_bruto
    for errado, correto in correcoes.items():
        texto_corrigido = texto_corrigido.replace(errado, correto)

    padrao = re.compile(
        r"Data de realização (\d{2}/\d{2}/\d{4}) superior a (\d+) meses"
    )
    match = padrao.search(texto_corrigido)
    if match:
        data = match.group(1)
        meses = match.group(2)
        return f"Data de realização: {data}, Superior a {meses} meses ou fora do ano corrente."
    else:
        return texto_corrigido
