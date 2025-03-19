import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.config.config import Config
from src.config.logger import logger
from src.config.api_client import APIClient
from src.config.auth_service import AuthenticationService
from src.controllers.shift_controller import ShiftController
from src.neural_vision.image_processor import AutomacaoImageProcess

ROBOT_ID = Config.ROBOT_ID


class OrquestradorRPA:
    """Classe responsável por orquestrar os estágios da automação."""

    def __init__(self):
        self.api_client = None
        self.auth_token = None

    def autenticar_api(self):
        """Autentica na API e inicializa o cliente."""
        logger.info("Autenticando na API...")

        username = os.getenv("API_USERNAME")
        password = os.getenv("API_PASSWORD")

        auth_response = AuthenticationService.authenticate(username, password)

        if not auth_response:
            logger.error("Falha na autenticação. Verifique suas credenciais.")
            return False

        self.auth_token = auth_response.get("access")
        if not self.auth_token:
            logger.error("Token de acesso não recebido.")
            return False

        self.api_client = APIClient(auth_token=self.auth_token)
        logger.success("Autenticação bem-sucedida.")
        return True

    def processar_estagio(self, stage, processador_class=None):
        """
        Processa os dados de um estágio específico utilizando a automação apropriada.
        """
        try:
            logger.info(f"Verificando itens pendentes no estágio: {stage}")
            dados = self.api_client.get_pending_items(stage=stage)

            if isinstance(dados, dict) and "detail" in dados:
                logger.warning(
                    f"Nenhuma tarefa pendente para {stage}. Resposta da API: {dados['detail']}"
                )
                return

            if not isinstance(dados, list) or not dados:
                logger.info(f"Nenhuma tarefa pendente para {stage}.")
                return

            logger.info(
                f"{len(dados)} tarefas encontradas no estágio {stage}. Iniciando processamento..."
            )

            if stage == "SHIFT":
                self.processar_shift(dados)

            elif stage == "IMAGE_PROCESS" and processador_class:
                self.processar_image_process(processador_class)

            elif stage == "SISMAMA":
                self.processar_sismama()

            else:
                logger.warning(f"Estágio {stage} não reconhecido.")

        except Exception as e:
            logger.error(f"Erro ao processar estágio {stage}: {str(e)}")

    def processar_shift(self, dados):
        """Processa as tarefas do estágio SHIFT."""
        logger.info("Iniciando processamento do SHIFT.")

        controller = ShiftController(
            url=Config.URL,
            usuario=Config.USUARIO,
            senha=Config.SENHA,
            screenshot_path=Config.LOG_DIR,
            api_client=self.api_client,
            robot_id=ROBOT_ID,
        )

        for item in dados:
            task_id = item.get("id")

            ordens_servico = [
                {
                    "os": sub_item.get("os_number"),
                    "os_name": sub_item.get("os_name"),
                    "task_id": task_id,
                    "item_id": sub_item.get("id"),
                }
                for sub_item in item.get("items", [])
                if sub_item.get("os_number")
            ]

            if ordens_servico:
                self.api_client.update_task(
                    task_id=task_id,
                    status="STARTED",
                    started_at=datetime.now().isoformat(),
                    stage="SHIFT",
                )
                logger.info(f"Tarefa {task_id} atualizada para 'STARTED'.")
                controller.processar_dados(ordens_servico)
            else:
                logger.warning(
                    f"Nenhuma ordem de serviço válida encontrada para a tarefa {task_id}."
                )

        controller.finalizar()

    def processar_image_process(self, processador_class):
        """Processa as tarefas do estágio IMAGE_PROCESS."""
        logger.info("Iniciando processamento de imagens.")

        try:
            processador = processador_class(
                robot_id=ROBOT_ID,
                auth_token=self.auth_token,
                api_client=self.api_client,
            )

            processador.processar_pendentes()

        except Exception as e:
            logger.error(f"Erro no processamento de imagens: {str(e)}")


    def processar_sismama(self):
        """Processa as tarefas do estágio SISMAMA."""
        logger.info("Iniciando automação do SIS MAMA.")
        try:
            from src.desktop.sismama_runner import SismamaRunner

            dados_sismama = self.api_client.get_sismama_data()

            if isinstance(dados_sismama, dict) and "detail" in dados_sismama:
                logger.info(f"Nenhum dado pendente para SIS MAMA. Resposta da API: {dados_sismama['detail']}")
                return

            if not dados_sismama:
                logger.info("Nenhum dado pendente para SIS MAMA.")
                return

            logger.info(f"{len(dados_sismama)} registros encontrados para SIS MAMA.")

            runner = SismamaRunner(api_client=self.api_client)
            runner._abrir_sismama()
            import time
            time.sleep(3)
            runner._preencher_sismama(dados_sismama)
            runner._finalizar_sismama()

        except Exception as e:
            logger.error(f"Erro ao processar SISMAMA: {str(e)}")


    def executar(self):
        """Executa o fluxo de automação."""
        if not self.autenticar_api():
            return

        self.processar_estagio("SHIFT")
        self.processar_estagio("IMAGE_PROCESS", processador_class=AutomacaoImageProcess)
        self.processar_estagio("SISMAMA")


if __name__ == "__main__":
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        orquestrador = OrquestradorRPA()
        orquestrador.executar()
    except Exception as e:
        logger.error(f"Erro ao executar main: {str(e)}")
