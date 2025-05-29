import os
import glob
from datetime import datetime
from pathlib import Path

from src.config.api_client import APIClient
from src.config.auth_service import AuthenticationService
from src.config.logger import logger
from .utils import converter_tif_para_jpg

from .agent import ImageAnalyzer


IMAGES_DIR = Path(os.getenv('BASE_IMAGE_PATH'))

if not IMAGES_DIR.exists():
    logger.warning(f"Diretório base de imagens não encontrado: {IMAGES_DIR}")

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
        logger.info(f'→ Entrada em processar_item: {item!r}')
        item_id = item.get('id')
        os_number = item.get('os_number')
        recipiente = item.get('shift_data', {}).get('recipiente')

        logger.info(f'Processando item {item_id}, OS: {os_number}, Recipiente: {recipiente}' )

        # Atualiza o item para indicar início do processamento
        if not self._atualizar_status_item(
            item_id, 'STARTED', 'IMAGE_PROCESS'
        ):
            return

        # Busca a imagem associada ao OS
        image_path = self._encontrar_caminho_imagem(recipiente)
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

            if image_path.suffix.lower() in [".tif", ".tiff"]:
                image_path_convertida = converter_tif_para_jpg(image_path)
                deve_excluir = True
            else:
                image_path_convertida = image_path
                deve_excluir = False

            logger.info(f'Imagem final usada para análise: {image_path_convertida}')
            image_analyzer = ImageAnalyzer()
            result_data = image_analyzer.analyze_image(str(image_path_convertida))
            logger.debug(f'Result_data do analyze_image: {result_data!r}')

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
        finally:
            if 'deve_excluir' in locals() and deve_excluir and image_path_convertida.exists():
                os.remove(image_path_convertida)
                logger.debug(f'Arquivo temporário removido: {image_path_convertida}')

    def _encontrar_caminho_imagem(self, recipiente):
        """
        Busca o caminho de imagem que começa com o número do recipiente.
        Exemplo: 2303667634_20250522112305.TIF
        """
        extensoes = ['.tif', '.tiff', '.png', '.jpg', '.jpeg']
        
        for ext in extensoes:
            padrao = os.path.join(str(IMAGES_DIR), f"{recipiente}_*{ext}")
            logger.info(f"Procurando por imagem com padrão: {padrao}")
            arquivos = glob.glob(padrao)
            if arquivos:
                logger.info(f"[DEBUG] Imagem encontrada: {arquivos[0]}")
                return Path(arquivos[0])  # retorna o primeiro encontrado
            
        logger.error(f"[DEBUG] Nenhuma imagem encontrada para recipiente: {recipiente}")
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

        logger.debug(f'Payload update_item: {payload}')

        if result_data:

            if isinstance(result_data, dict):
                payload['image_result'] = str(result_data.get('response', ''))
            else:
                payload['image_result'] = result_data

        if bot_error_message:
            payload['bot_error_message'] = bot_error_message

        response = self.api_client.update_item(**payload)
        logger.debug(f'Resposta update_item: {response!r}')
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
        logger.info(f'RESP do get_pending_items: {items_pendentes!r} (type={type(items_pendentes)})')
        if not items_pendentes:
            logger.info('Nenhum item pendente para processamento de imagens.')
            return

        for task in items_pendentes:
            logger.debug(f'→ Tarefa RAW: {task!r}')
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
