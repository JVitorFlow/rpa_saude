import os
import re
import time
import traceback
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pyautogui
from pywinauto import Application

from src.config.logger import logger
from src.controllers.api_handler import (atualizar_item_erro_sismama,
                                         atualizar_item_sismama)

from .services.popup_services import (tratar_pop_up_informacao,
                                      validar_popup_data_realizacao)


def is_valid_size(size_value: Any) -> bool:
    """
    Verifica se o valor informado (tamanho de lesão) é válido (float > 0).
    Aceita float direto ou string que contenha número.
    """
    if size_value is None:
        return False

    if isinstance(size_value, float):
        return size_value > 0

    if isinstance(size_value, str):
        match = re.search(r"\d+([,\.]\d+)?", size_value.replace(",", "."))
        if match:
            return float(match.group()) > 0

    return False


def carregar_variaveis_ambiente() -> tuple:
    """
    Carrega configurações necessárias a partir de variáveis de ambiente.
    Certifique-se de definir estas variáveis no seu arquivo .env ou ambiente:
      - CAMINHO_PROJETO
      - CAMINHO_SISTEMA_SISMAMA
      - URL_SHIFT
      - USUARIO_SHIFT
      - SENHA_SHIFT
      - SCREENSHOT_PATH
      - CADASTRO01_IMAGE
      - SALVAR01_IMAGE
    Retorna uma tupla com os valores.
    """
    return (
        os.getenv("CAMINHO_PROJETO", str(Path(__file__).resolve().parent)),
        os.getenv("CAMINHO_SISTEMA_SISMAMA", r"C:\Caminho\SIS_MAMA.exe"),
        os.getenv("URL_SHIFT", "http://urlshift"),
        os.getenv("USUARIO_SHIFT", "usuario_shift"),
        os.getenv("SENHA_SHIFT", "senha_shift"),
        os.getenv("SCREENSHOT_PATH", r"C:\Caminho\Screenshots"),
        os.getenv("CADASTRO01_IMAGE", r"C:\Caminho\cadastro01.png"),
        os.getenv("SALVAR01_IMAGE", r"C:\Caminho\salvar01.png"),
    )


class SismamaDigitador:
    """
    Classe responsável por inserir dados no SIS MAMA utilizando automação.
    Divide o fluxo de cadastro em etapas menores para facilitar manutenção e escalabilidade.
    """

    def __init__(self, api_client):
        self.api_client = api_client
        # Carrega as configurações a partir de variáveis de ambiente
        (
            self.caminho_projeto,
            self.caminho_sistema_sismama,
            self.url_shift,
            self.usuario_shift,
            self.senha_shift,
            self.screenshot_path,
            self.cadastro01_image,
            self.salvar01_image,
        ) = carregar_variaveis_ambiente()

    def inserir_dados_sismama(self, dados_sismama: List[Dict[str, Any]]) -> None:
        """
        Processa a lista de dados do estágio SISMAMA, inserindo-os no sistema.

        :param dados_sismama: Lista de dicionários com os dados obtidos via API.
        """
        try:
            app = Application(backend="uia").connect(title_re=".*Prestador de Servi.*")
            total_registros = len(dados_sismama)
            logger.info(
                f"Iniciando o processamento de {total_registros} registros no SIS MAMA."
            )

            for item in dados_sismama:
                try:
                    self._processar_item(item, app)
                except Exception as item_e:
                    logger.error(
                        f"Erro ao processar o item {item.get('item_id')}: {item_e}"
                    )
                    logger.error(
                        f"Erro no item {item.get('item_id')}: {item_e}\n{traceback.format_exc()}"
                    )

            logger.info(
                f"Processamento concluído. Total de {total_registros} registros verificados."
            )
        except Exception as e:
            logger.error(
                f"Erro durante o processamento do SIS MAMA: {e}\n{traceback.format_exc()}"
            )

    def _processar_item(self, item: Dict[str, Any], app: Application) -> None:
        """
        Processa um item individual:
          - Valida se os dados de SHIFT são suficientes.
          - Inicia o cadastro, preenche os campos e trata pop-ups.

        :param item: Dicionário contendo 'item_id', 'os_number' e 'shift_data'.
        :param app: Instância da aplicação conectada via pywinauto.
        """
        item_id = item.get("item_id")
        os_number = item.get("os_number")
        shift_data = item.get("shift_data", {})

        logger.info(
            f"Iniciando inserção dos dados do paciente ID {item_id} (OS {os_number})."
        )

        if not shift_data:
            logger.info(f"Item {item_id} não possui dados de SHIFT. Ignorando...")
            return

        if not self._dados_suficientes(shift_data) or not is_valid_size(
            shift_data.get("tamanho_lesao")
        ):
            mensagem_erro = f"Dados insuficientes para o item {item_id}. Pulando."
            logger.info(mensagem_erro)
            atualizar_item_erro_sismama(self.api_client, item_id, mensagem_erro)
            return

        # Executa o fluxo de cadastro
        pyautogui.press(["f2"])  # Inicia cadastro
        self._preencher_campos_iniciais(shift_data)
        self._preencher_endereco(shift_data, app)
        self._preencher_caracteristicas_lesao(shift_data, app)
        coleta_ok = self._preencher_coleta(os_number, shift_data, app, item_id)
        if not coleta_ok:
            logger.info(f"Cadastro cancelado para o item {item_id} devido ao pop-up.")
            return

        # Salva e trata pop-up
        pyautogui.press(["F5"])
        time.sleep(1)
        popup_encontrado = tratar_pop_up_informacao(app, self.api_client, item_id)
        if not popup_encontrado:
            logger.info(f"Nenhum popup detectado. Atualizando item {item_id} como COMPLETED")
            atualizar_item_sismama(self.api_client, item_id)

    def _dados_suficientes(self, shift_data: Dict[str, Any]) -> bool:
        """
        Verifica se os dados críticos estão presentes.

        :param shift_data: Dicionário com os dados de SHIFT.
        :return: True se os campos críticos estiverem preenchidos, False caso contrário.
        """
        campos_criticos = ["cartao_sus", "localizacao_lesao", "estado"]
        return all(
            shift_data.get(campo) not in [None, "", "Não especificado (NI)"]
            for campo in campos_criticos
        )

    def _preencher_campos_iniciais(self, shift_data: Dict[str, Any]) -> None:
        """
        Preenche campos iniciais como CNES, Cartão SUS, sexo, nome, data de nascimento, idade, etc.
        """
        cnes = 2078287
        # pyautogui.write(shift_data.get("cnes", "NI"))
        pyautogui.write(str(cnes))
        pyautogui.press(["tab"] * 2)

        cartao_sus = shift_data.get("cartao_sus")
        if cartao_sus:
            pyautogui.write(cartao_sus + chr(9))
        else:
            logger.info("Cartão SUS não especificado. Pulando inserção.")

        sexo = shift_data.get("sexo", "").strip().lower()
        if sexo in ["feminino", "f"]:
            pyautogui.press(["right"])
        elif sexo in ["masculino", "m"]:
            pyautogui.press([" "])
        pyautogui.press(["tab"])

        pyautogui.write(shift_data.get("nome_paciente", "NI").strip())
        pyautogui.press(["tab"] * 2)

        pyautogui.write("NI")  # Campo da mãe
        pyautogui.press(["tab"] * 5)

        data_nascimento = shift_data.get("data_nascimento", "").strip()
        if data_nascimento:
            try:
                dt = datetime.strptime(data_nascimento, "%Y-%m-%d")
                pyautogui.write(dt.strftime("%d%m%Y"))
            except ValueError:
                logger.error("Data de nascimento inválida.")
        else:
            logger.info("Data de nascimento não especificada.")
        pyautogui.press(["tab"])

        pyautogui.write(str(shift_data.get("idade_paciente", "0")))
        pyautogui.press(["tab"])

        raca_etinia = shift_data.get("raca_etinia", "Não especificado (NI)").strip()
        if raca_etinia.lower() == "não especificado (ni)":
            pyautogui.press(["tab"])  # Pula os campos relacionados
        else:
            pyautogui.write(raca_etinia)
            print("OK")

    def _preencher_endereco(self, shift_data: Dict[str, Any], app: Application) -> None:
        """
        Preenche os dados de endereço, UF, município, etc.
        """
        nacionalidade = "BRASIL"
        pyautogui.write(nacionalidade)
        pyautogui.press(["tab"])

        logradouro = shift_data.get("logradouro", "NI").strip()
        if logradouro == "Não especificado (NI)":
            logradouro = "NI"
        pyautogui.write(logradouro)
        pyautogui.press(["tab"])

        numero = shift_data.get("numero_residencial", "NI")
        if numero == "Não especificado (NI)":
            numero = "NI"
        pyautogui.write(numero)
        pyautogui.press(["tab"] * 3)

        uf = str(shift_data.get("estado", "NI")).strip()
        pyautogui.write(uf)
        pyautogui.press(["tab"])

        municipio = str(shift_data.get("cidade", "NI")).strip().upper()
        if municipio == "NÃO ESPECIFICADO (NI)":
            municipio = "NI"
        else:
            municipio = "".join(
                ch
                for ch in unicodedata.normalize("NFD", municipio)
                if unicodedata.category(ch) != "Mn"
            )

        pyautogui.write(municipio)
        pyautogui.press(["tab"] * 6)
        pyautogui.press(["right"] * 2)  # Seleciona "biópsia/peça"
        pyautogui.press(["tab"])
        pyautogui.press(["right"] * 2)  # Risco elevado? (Não sabe)
        pyautogui.press(["tab"])
        pyautogui.press(["right"] * 2)  # Está grávida ou amamenta? (Não sabe)

        janela_principal = app.window(
            title="Requisição de Exame Histopatológico - MAMA"
        )
        painel_tratamento = janela_principal.child_window(
            title="4. Tratamento anterior para câncer de mama?", control_type="Pane"
        )
        painel_tratamento.child_window(title="Não", control_type="RadioButton").click()

    def _preencher_caracteristicas_lesao(
        self, shift_data: Dict[str, Any], app: Application
    ) -> None:
        """
        Preenche os dados relativos às características da lesão.
        """
        pyautogui.press(["tab"])
        pyautogui.press([" "])
        pyautogui.press(["tab"])

        caracteristica = str(shift_data.get("caracteristica_lesao", "NI")).strip()
        janela_principal = app.window(
            title="Requisição de Exame Histopatológico - MAMA"
        )
        painel_caracteristica = janela_principal.child_window(
            title="6. Características da lesão", control_type="Pane"
        )
        if caracteristica.lower() == "mama direita":
            painel_caracteristica.child_window(
                title="MAMA DIREITA", control_type="RadioButton"
            ).click()
        else:
            painel_caracteristica.child_window(
                title="MAMA ESQUERDA", control_type="RadioButton"
            ).click()
        pyautogui.press(["tab"])

        painel_localizacao = janela_principal.child_window(
            title="Localização", control_type="Pane"
        )
        localizacao = str(shift_data.get("localizacao_lesao", "NI")).upper()
        mapeamento = {
            "QSL": "QSL",
            "QIL": "QIL",
            "QSM": "QSM",
            "QIM": "QIM",
            "UQLAT": "UQLat",
            "UQSUP": "UQsup",
            "UQMED": "UQmed",
            "UQINF": "UQinf",
            "RRA": "RRA",
            "PA": "PA",
        }
        if localizacao in mapeamento:
            painel_localizacao.child_window(
                title=mapeamento[localizacao], control_type="RadioButton"
            ).click()
        else:
            logger.info(f"Localização '{localizacao}' não reconhecida.")
        pyautogui.press(["tab"])

        tamanho_str = str(shift_data.get("tamanho_lesao", "")).strip()
        match = re.search(r"\d+(,\d+)?", tamanho_str)
        tamanho: Optional[float] = None
        if match:
            tamanho = float(match.group().replace(",", "."))
        else:
            logger.info("Nenhuma correspondência para 'Tamanho'.")

        if tamanho is not None:
            if tamanho < 2:
                pyautogui.press([" "])
            elif 2 <= tamanho <= 5:
                pyautogui.press(["down"])
            elif 5 < tamanho <= 10:
                pyautogui.press(["down"] * 2)
            elif tamanho > 10:
                pyautogui.press(["down"] * 3)
            else:
                pyautogui.press(["down"] * 4)
        pyautogui.press(["tab"])
        pyautogui.press(["down"])  # Linfonodo axilar palpável: "Não"
        pyautogui.press(["tab"])
        pyautogui.press(["down"] * 2)  # Biópsia por agulha grossa

    def _preencher_coleta(
        self, os_number: str, shift_data: Dict[str, Any], app: Application, item_id: int
    ) -> bool:
        """
        Preenche os dados de coleta, número do exame e data de liberação.
        """
        pyautogui.press(["tab"])
        data_coleta = shift_data.get("data_coleta", "").strip()
        if data_coleta:
            self._digitar_data_coleta(data_coleta)
        else:
            logger.info("Data de coleta não especificada.")

        pyautogui.press(["tab"])
        time.sleep(1)

        if validar_popup_data_realizacao(app, self.api_client, item_id):
            logger.info("Cadastro cancelado devido ao pop-up de data de realização.")
            return False

        pyautogui.press(["tab"] * 2)
        numero_exame = os_number.replace("-", "")
        pyautogui.write(numero_exame)


        pyautogui.press(["tab"])
        recebido_em = shift_data.get("data_coleta", "").strip()
        if recebido_em:
            self._digitar_data_coleta(recebido_em)
        else:
            logger.info("Data de coleta (recebido_em) não especificada.")

        pyautogui.press(["tab"])
        pyautogui.press(["down"] * 2)  # Seleciona Biópsia por agulha grossa
        pyautogui.press(["tab"])
        pyautogui.press([" "])  # Seleciona "Satisfatório"
        pyautogui.press(["tab"] * 2)
        pyautogui.press(["right"])  # Microcalcificações: "Não"
        pyautogui.press(["tab"])
        pyautogui.press(["down"] * 10)
        pyautogui.press(["space"])
        pyautogui.press(["tab"] * 2)
        pyautogui.press(["right"])
        pyautogui.press(["enter"])  # Seleciona aba Cont.III
        pyautogui.press(["tab"])

        data_liberacao = shift_data.get("data_liberacao", "").strip()
        if data_liberacao:
            self._digitar_data_coleta(data_liberacao)
        else:
            logger.info("Data de liberação não especificada.")

        pyautogui.press(["tab"])
        med_responsavel = "10304501883"
        pyautogui.write(med_responsavel)
        return True

    def _digitar_data_coleta(self, data_str: str) -> None:
        """
        Converte data ISO (ex: 2023-05-01T12:00:00Z) para 'ddMMyyyy' e a digita via pyautogui.
        """
        try:
            dt = datetime.strptime(data_str, "%Y-%m-%dT%H:%M:%SZ")
            pyautogui.write(dt.strftime("%d%m%Y"))
        except ValueError:
            logger.info(f"Formato inválido para data: {data_str}")


# Exemplo de uso direto
if __name__ == "__main__":
    from src.config.api_client import APIClient
    from src.config.auth_service import AuthenticationService

    USERNAME = os.getenv("API_USERNAME")
    PASSWORD = os.getenv("API_PASSWORD")

    auth_response = AuthenticationService.authenticate(USERNAME, PASSWORD)
    if not auth_response:
        logger.warning("Falha na autenticação da API. Verifique as credenciais.")
    else:
        auth_token = auth_response.get("access")
        api_client = APIClient(auth_token)
        digitador = SismamaDigitador(
            salvar01_image="caminho/para/salvar01.png",
            screenshot_path="caminho/para/screenshots",
        )
        # Supondo que os dados do SISMAMA são obtidos via API:
        dados_sismama = api_client.get_sismama_data()
        if dados_sismama:
            digitador.inserir_dados_sismama(dados_sismama)
        else:
            logger.info("Nenhum dado pendente para SISMAMA.")
