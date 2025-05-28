import ctypes
import os
import sys
import time
import traceback
from typing import Any, List

import pyautogui
import pygetwindow as gw

from src.config.logger import logger
from utils.imagens import espera_imagem_aparecer

from .sismama_digitador import SismamaDigitador


class SismamaRunner:
    """
    Classe responsável por inicializar e executar o fluxo de processamento do SIS MAMA.
    Pode ser usada para:
      - Carregar configurações do SIS MAMA (caminhos, imagens etc.)
      - Obter dados pendentes via API
      - Abrir o SIS MAMA, maximizar janela, preencher dados, salvar e encerrar.
    """

    def __init__(self, api_client: Any):
        """
        Construtor do SismamaRunner.

        :param api_client: Instância de cliente que se comunicará com a API
                          (ex.: para obter dados pendentes e atualizar status).
        """
        self.api_client = api_client
        self._carregar_configuracoes()

    def _carregar_configuracoes(self) -> None:
        """
        Carrega variáveis globais necessárias a partir de variáveis de ambiente.
        """
        self.caminho_projeto       = os.getenv("CAMINHO_PROJETO")
        self.caminho_sistema_sismama = os.getenv("CAMINHO_SISTEMA_SISMAMA")
        self.url_shift             = os.getenv("URL_SHIFT")
        self.usuario_shift         = os.getenv("USUARIO_SHIFT")
        self.senha_shift           = os.getenv("SENHA_SHIFT")
        self.screenshot_path       = os.getenv("SCREENSHOT_PATH")
        self.cadastro01_image      = os.getenv("CADASTRO01_IMAGE")
        self.salvar01_image        = os.getenv("SALVAR01_IMAGE")

    def maximizar_janela(self, titulo_janela: str) -> bool:
        """
        Tenta maximizar a janela cujo título contenha 'titulo_janela'.

        :param titulo_janela: Título (ou parte) da janela a maximizar.
        :return: True se a janela foi encontrada e maximizada, False caso contrário.
        """
        time.sleep(2)
        janelas = gw.getWindowsWithTitle(titulo_janela)
        if janelas:
            for janela in janelas:
                logger.info(f"Maximizando janela com título '{titulo_janela}' encontrada.")
                janela.maximize()
                return True

        logger.warning(f"Janela com título '{titulo_janela}' não encontrada.")
        return False

    def executar(self) -> None:
        """
        Executa todo o fluxo de processamento do SIS MAMA:
          - Obtém dados pendentes via API
          - Abre o SIS MAMA
          - Preenche dados
          - Salva
          - Finaliza o SIS MAMA
        """
        start = time.time()
        try:
            self._processar_sismama()
            end = time.time()
            tempo_decorrido = end - start
            logger.info(f"Script completo. Tempo decorrido: {tempo_decorrido:.2f} segundos")
        except Exception as exc:
            logger.error(f"Erro durante a execução do script: {str(exc)}")
            trace_info = traceback.format_exc()
            logger.error(f"Erro durante o processamento do registro: {exc}\nDetalhes:\n{trace_info}")

    def _processar_sismama(self) -> None:
        """
        Lógica interna para:
          1. Obter dados pendentes do SIS MAMA via API
          2. Abrir SIS MAMA
          3. Esperar tela principal e realizar fluxo de cadastro
          4. Finalizar SIS MAMA
        """
        logger.info("Obtendo dados pendentes do estágio SISMAMA via API.")
        dados_sismama = self.api_client.get_sismama_data()

        if isinstance(dados_sismama, dict) and "detail" in dados_sismama:
            logger.info(f"Nenhum dado pendente para SIS MAMA. Resposta da API: {dados_sismama['detail']}")
            return
        
        if not dados_sismama:
            logger.info("Nenhum dado pendente para SIS MAMA.")
            return
        
        logger.info(f"Processando {len(dados_sismama)} itens autorizados para o SISMAMA.")
        self._abrir_sismama()
        self._preencher_sismama(dados_sismama)
        self._finalizar_sismama()

    def _abrir_sismama(self) -> None:
        """
        Tenta abrir o SIS MAMA via ShellExecute e espera a tela principal aparecer.
        """
        logger.info("Abrindo o SIS MAMA")
        resultado = ctypes.windll.shell32.ShellExecuteW(None, "runas", self.caminho_sistema_sismama, None, None, 1)
        if resultado <= 32:
            raise RuntimeError(f"ShellExecuteW falhou com o código de erro: {resultado}")

        logger.info("Verificando se a tela do sistema abriu")
        espera_imagem_aparecer(self.cadastro01_image, None, 0.9)

        logger.info("Clicando em cadastro > exames > histopatológico")
        pyautogui.click()
        pyautogui.typewrite(['x', 'h'])

        # Tenta maximizar a janela principal
        self.maximizar_janela("Requisição de Exame Histopatológico - MAMA")

    def _preencher_sismama(self, dados_sismama: List[dict]) -> None:
        """
        Preenche o SIS MAMA com os dados obtidos da API utilizando a classe SismamaDigitador.
        
        :param dados_sismama: Lista de dicionários contendo dados para cadastro no SIS MAMA.
        """
        logger.info("Iniciando preenchimento de dados no SIS MAMA.")
        
        digitador = SismamaDigitador(api_client=self.api_client)
        digitador.inserir_dados_sismama(dados_sismama)


    def _finalizar_sismama(self) -> None:
        """
        Finaliza o SIS MAMA via taskkill.
        """
        logger.info("Encerrando o processo do SIS MAMA.")
        command = "taskkill /IM SisMamaFB.exe /F"
        ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd", "/c " + command, None, 1)


if __name__ == "__main__":
    """
    Exemplo de uso direto (caso queira rodar standalone).
    Se estiver usando containers ou outro orchestrator, você pode chamar SismamaRunner em outro lugar.
    """
    from src.config.api_client import APIClient
    from src.config.auth_service import AuthenticationService


    USERNAME = os.getenv("API_USERNAME")
    PASSWORD = os.getenv("API_PASSWORD")

    auth_response = AuthenticationService.authenticate(USERNAME, PASSWORD)
    if not auth_response:
        logger.info("Falha na autenticação da API. Verifique as credenciais.")
        sys.exit(1)

    auth_token = auth_response.get("access")
    api_client = APIClient(auth_token)

    sismama_runner = SismamaRunner(api_client=api_client)
    sismama_runner.executar()
