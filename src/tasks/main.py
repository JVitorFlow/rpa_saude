import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from datetime import datetime

from src.config.config import Config
from src.config.logger import logger
from src.config.api_client import APIClient
from src.config.auth_service import AuthenticationService
from src.controllers.shift_controller import ShiftController
from src.neural_vision.image_processor import AutomacaoImageProcess


ROBOT_ID = Config.ROBOT_ID


def autenticar_api():
    """Autentica na API e retorna um cliente autenticado."""
    logger.info("Autenticando na API...")

    username = os.getenv("API_USERNAME")
    password = os.getenv("API_PASSWORD")

    auth_response = AuthenticationService.authenticate(username, password)

    if not auth_response:
        logger.error("Falha na autenticação. Verifique suas credenciais.")
        return None

    auth_token = auth_response.get("access")
    if not auth_token:
        logger.error("Token de acesso não recebido.")
        return None

    logger.success("Autenticação bem-sucedida.")
    return APIClient(auth_token=auth_token), auth_token



def processar_estagio(api_client, stage, controller=None, processador_class=None, auth_token=None):
    """
    Processa os dados de um estágio específico utilizando a automação apropriada.
    """
    try:
        logger.info(f"Verificando itens pendentes no estágio: {stage}")
        dados = api_client.get_pending_items(stage=stage)

        if isinstance(dados, dict) and "detail" in dados:
            logger.warning(f"Nenhuma tarefa pendente para {stage}. Resposta da API: {dados['detail']}")
            return

        if not isinstance(dados, list) or not dados:
            logger.info(f"Nenhuma tarefa pendente para {stage}.")
            return

        logger.info(f"{len(dados)} tarefas encontradas no estágio {stage}. Iniciando processamento...")

        if stage == "SHIFT" and controller:
            processar_shift(api_client, controller, dados)

        elif stage == "IMAGE_PROCESS" and processador_class:
            processar_image_process(api_client, processador_class, auth_token)

        elif stage == "SISMAMA":
            processar_sismama(api_client)

        else:
            logger.warning(f"Estágio {stage} não reconhecido.")

    except Exception as e:
        logger.error(f"Erro ao processar estágio {stage}: {str(e)}")



def processar_shift(api_client, controller, dados):
    """Processa as tarefas do estágio SHIFT."""
    for item in dados:
        logger.info(f"🛠️ Processando item: {item}")
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
            started_at = datetime.now().isoformat()
            api_client.update_task(
                task_id=task_id, status="STARTED", started_at=started_at, stage="SHIFT"
            )
            logger.info(f"Tarefa {task_id} atualizada para 'STARTED'.")

            controller.processar_dados(ordens_servico)
        else:
            logger.warning(
                f"Nenhuma ordem de serviço válida encontrada para a tarefa {task_id}."
            )


def processar_image_process(api_client, processador_class, auth_token):
    """Processa as tarefas do estágio IMAGE_PROCESS."""
    logger.info("Iniciando processamento de imagens.")

    try:
        processador = processador_class(
            robot_id=ROBOT_ID,
            auth_token=auth_token,
            api_client=api_client,
        )

        processador.processar_pendentes()

    except Exception as e:
        logger.error(f"❌ Erro no processamento de imagens: {str(e)}")



def processar_sismama(api_client):
    """Processa as tarefas do estágio SISMAMA utilizando o SismamaDigitador."""
    logger.info("Iniciando automação do SIS MAMA.")
    try:
        from desktop.sismama_digitador import SismamaDigitador

        dados_sismama = api_client.get_sismama_data()
        if not dados_sismama:
            logger.info("Nenhum dado pendente para SIS MAMA.")
            return
        digitador = SismamaDigitador()
        # Processa os dados obtidos
        digitador.inserir_dados_sismama(dados_sismama)
    except Exception as e:
        logger.error(f"Erro ao processar SIS MAMA: {str(e)}")



def main():
    """Função principal do RPA, responsável por gerenciar o fluxo da automação."""
    start_time = datetime.now()
    erro_ocorrido = False
    controller = None  # Inicializa controller para evitar erro no `finally`

    try:
        api_client, auth_token = autenticar_api()
        if not api_client:
            return

        controller = ShiftController(
            url=Config.URL,
            usuario=Config.USUARIO,
            senha=Config.SENHA,
            screenshot_path=Config.LOG_DIR,
            api_client=api_client,
            robot_id=ROBOT_ID,
        )

        processar_estagio(api_client, "SHIFT", controller=controller)
        processar_estagio(
            api_client, "IMAGE_PROCESS", processador_class=AutomacaoImageProcess
        )
        processar_estagio(api_client, "SISMAMA")

    except Exception as e:
        erro_ocorrido = True
        logger.error(f"Erro durante a execução do script: {str(e)}")

    finally:
        if controller:
            controller.finalizar()

        tempo_execucao = (datetime.now() - start_time).total_seconds()
        status_execucao = (
            "concluído com sucesso" if not erro_ocorrido else "finalizado com erros"
        )
        logger.info(
            f"✅ Automação {status_execucao}. Tempo total: {tempo_execucao:.2f} segundos"
        )


if __name__ == "__main__":
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        main()
    except Exception as e:
        logger.error(f"❌ Erro ao executar main: {str(e)}")
