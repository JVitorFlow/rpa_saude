import os
from datetime import datetime
from pathlib import Path

from src.config.api_client import APIClient
from src.config.auth_service import AuthenticationService
from src.config.logger import logger

from .agent import ImageAnalyzer


BASE_IMAGE_PATH = Path(os.getenv('BASE_IMAGE_PATH', 'images/afip'))


class AutomacaoImageProcess:
    """
    Classe responsável pelo processamento automático de imagens do SISMAMA.
    Utiliza OpenAI para analisar formulários médicos.
    """

    def __init__(self, robot_id, auth_token, api_client):
        self.robot_id = robot_id
        self.auth_token = auth_token
        self.api_client = api_client
        self.sucesso = False

    def processar_item(self, item):
        """
        Processa um item individual, analisa a imagem e atualiza o status via API.
        """
        item_id = item.get('id')
        os_number = item.get('os_number')

        logger.info(f'Processando item {item_id}, OS: {os_number}')

        # Atualiza o item para indicar início do processamento
        if not self._atualizar_status_item(
            item_id, 'STARTED', 'IMAGE_PROCESS'
        ):
            return

        # Busca a imagem associada ao OS
        image_path = self._encontrar_caminho_imagem(os_number)
        if not image_path:
            error_msg = f'Imagem não encontrada para OS: {os_number}'
            logger.warning(error_msg)
            # Atualiza o item com status ERROR e a mensagem do bot
            self._atualizar_status_item(
                item_id, 'ERROR', 'IMAGE_PROCESS', bot_error_message=error_msg
            )
            return

        try:
            logger.info(f'Imagem encontrada para OS {os_number}: {image_path}')
            image_analyzer = ImageAnalyzer()
            result_data = image_analyzer.analyze_image(str(image_path))

            if result_data:
                logger.info(
                    f'Análise concluída para OS {os_number}: {result_data}'
                )

                # Atualizar item na API com resultado da imagem
                self._atualizar_status_item(
                    item_id, 'COMPLETED', 'SISMAMA', result_data=result_data
                )
                self.sucesso = True
            else:
                error_msg = f'Falha na análise da imagem para OS {os_number}'
                logger.warning(error_msg)
                self._atualizar_status_item(
                    item_id,
                    'ERROR',
                    'IMAGE_PROCESS',
                    bot_error_message=error_msg,
                )

        except Exception as e:
            error_msg = f'Erro ao processar imagem para item {item_id}: {e}'
            logger.error(error_msg)
            self._atualizar_status_item(
                item_id, 'ERROR', 'IMAGE_PROCESS', bot_error_message=error_msg
            )

    def _encontrar_caminho_imagem(self, os_number):
        """
        Retorna o caminho completo da imagem baseado no número OS, verificando múltiplas extensões.
        """
        for ext in ['.png', '.jpg', '.jpeg']:
            image_path = BASE_IMAGE_PATH / f'{os_number}{ext}'
            if image_path.exists():
                return image_path
        return None

    def _atualizar_status_item(
        self, item_id, status, stage, result_data=None, bot_error_message=None
    ):
        """
        Atualiza o status do item na API.
        Se bot_error_message for fornecida, ela será enviada como parte do payload.
        """
        payload = {
            'item_id': item_id,
            'status': status,
            'stage': stage,
            'ended_at': datetime.now().isoformat(),
        }

        if result_data:

            if isinstance(result_data, dict):
                payload['image_result'] = str(result_data.get('response', ''))
            else:
                payload['image_result'] = result_data

        if bot_error_message:
            payload['bot_error_message'] = bot_error_message

        response = self.api_client.update_item(**payload)
        if response:
            logger.info(
                f'Item {item_id} atualizado para {status} na etapa {stage}.'
            )
            return True
        else:
            logger.error(f'Falha ao atualizar item {item_id} para {status}.')
            return False

    def processar_pendentes(self):
        """
        Obtém itens pendentes da API e processa-os.
        """
        logger.info(
            'Verificando itens pendentes para processamento de imagens...'
        )

        items_pendentes = self.api_client.get_pending_items(
            stage='IMAGE_PROCESS'
        )
        if not items_pendentes:
            logger.info('Nenhum item pendente para processamento de imagens.')
            return

        for task in items_pendentes:
            task_id = task.get('id')
            items = task.get('items', [])

            logger.info(
                f'Processando tarefa ID: {task_id} com {len(items)} itens.'
            )

            for item in items:
                self.processar_item(item)


if __name__ == '__main__':
    """
    Inicializa o processamento de imagens caso o script seja executado diretamente.
    """
    USERNAME = os.getenv('API_USERNAME')
    PASSWORD = os.getenv('API_PASSWORD')

    auth_response = AuthenticationService.authenticate(USERNAME, PASSWORD)
    if not auth_response:
        logger.error('Falha na autenticação da API. Verifique as credenciais.')
    else:
        auth_token = auth_response.get('access')
        api_client = APIClient(auth_token)

        automacao_imagens = AutomacaoImageProcess(
            robot_id=1, auth_token=auth_token, api_client=api_client
        )
        automacao_imagens.processar_pendentes()
