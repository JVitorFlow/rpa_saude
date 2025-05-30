import os
import sys
import ctypes
from datetime import datetime
from typing import Any, List, Optional, Type


from src.config.api_client import APIClient
from src.config.auth_service import AuthenticationService
from src.config.config import Config
from src.config.logger import logger
from src.controllers.shift_controller import ShiftController
from src.neural_vision.image_processor import AutomacaoImageProcess
from src.desktop.sismama_runner import SismamaRunner
from src.controllers.api_handler import tratar_erro_admin_sismama


def is_admin() -> bool:
    """
    Verifica se o processo atual está rodando com privilégios de administrador.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


class OrquestradorRPA:
    """
    Orquestra o fluxo completo de automação:
      1. Autentica na API
      2. Processa SHIFT
      3. Processa IMAGE_PROCESS
      4. Processa SISMAMA
    """

    def __init__(self, config: Type[Config] = Config) -> None:
        self.config = config
        self.api_client: Optional[APIClient] = None
        self.auth_token: Optional[str] = None

    def autenticar_api(self) -> bool:
        logger.info("Autenticando na API...")
        username = os.getenv("API_USERNAME")
        password = os.getenv("API_PASSWORD")
        response = AuthenticationService.authenticate(username, password)
        if not response or "access" not in response:
            logger.error("Falha na autenticação. Verifique suas credenciais.")
            return False
        self.auth_token = response["access"]
        self.api_client = APIClient(auth_token=self.auth_token)
        logger.success("Autenticação bem-sucedida.")
        return True

    def processar_estagio(
        self, stage: str, processor_class: Optional[Type[Any]] = None
    ) -> None:
        try:
            logger.info(f"Verificando itens pendentes no estágio: {stage}")
            data = self.api_client.get_pending_items(stage=stage)
            if isinstance(data, dict) and data.get("detail"):
                logger.warning(
                    f"Nenhuma tarefa pendente para {stage}: {data['detail']}"
                )
                return
            if not data:
                logger.info(f"Nenhuma tarefa pendente para {stage}.")
                return

            logger.info(f"{len(data)} item(s) pendente(s) em {stage}.")
            if stage == "SHIFT":
                self._processar_shift(data)
            elif stage == "IMAGE_PROCESS" and processor_class:
                self._processar_image(data, processor_class)
            elif stage == "SISMAMA":
                self._processar_sismama()
            else:
                logger.warning(f"Estágio desconhecido: {stage}")
        except Exception as e:
            logger.error(f"Erro ao processar estágio {stage}: {e}")

    def _processar_shift(self, data: List[dict]) -> None:
        logger.info("Iniciando processamento do SHIFT.")
        controller = ShiftController(
            url=self.config.URL,
            usuario=self.config.USUARIO,
            senha=self.config.SENHA,
            screenshot_path=self.config.LOG_DIR,
            api_client=self.api_client,
            robot_id=self.config.ROBOT_ID,
        )
        for task in data:
            task_id = task.get("id")
            orders = [
                {
                    "os": item.get("os_number"),
                    "os_name": item.get("os_name"),
                    "task_id": task_id,
                    "item_id": item.get("id"),
                }
                for item in task.get("items", [])
                if item.get("os_number")
            ]
            if orders:
                self.api_client.update_task(
                    task_id=task_id,
                    status="STARTED",
                    started_at=datetime.now().isoformat(),
                    stage="SHIFT",
                )
                logger.info(f"Tarefa {task_id} iniciada.")
                controller.processar_dados(orders)
            else:
                logger.warning(f"Sem OS válida para tarefa {task_id}.")
        controller.finalizar()

    def _processar_image(self, data: List[dict], processor_class: Type[Any]) -> None:
        logger.info("Iniciando processamento de imagens.")
        try:
            processor = processor_class(
                robot_id=self.config.ROBOT_ID,
                auth_token=self.auth_token,
                api_client=self.api_client,
            )
            processor.processar_pendentes()
        except Exception as e:
            logger.error(f"Erro no processamento de imagens: {e}")

    def _processar_sismama(self) -> None:
        logger.info("Iniciando automação SIS MAMA.")
        runner = SismamaRunner(api_client=self.api_client)  # type: ignore
        try:
            runner.executar()
        except Exception as e:
            logger.error(str(e))
            tratar_erro_admin_sismama(self.api_client)

    def executar(self) -> None:
        if not self.autenticar_api():
            return
        for stage, cls in [
            ("SHIFT", None),
            ("IMAGE_PROCESS", AutomacaoImageProcess),
            ("SISMAMA", None),
        ]:
            self.processar_estagio(stage, cls)


if __name__ == "__main__":

    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    )
    try:
        orchestrator = OrquestradorRPA()
        orchestrator.executar()
    except Exception as e:
        logger.error(f"Erro ao executar main: {e}")
