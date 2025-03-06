import requests
import json
from .logger import logger
from .config import Config


class APIClient:
    """Cliente para interagir com a API."""

    def __init__(self, auth_token):
        """Inicializa o cliente da API com o token JWT."""
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

    def _make_request(self, method, endpoint, params=None, data=None):
        """Realiza requisições HTTP genéricas."""
        url = f"{Config.API_URL}{endpoint}"
        try:
            response = requests.request(
                method, url, headers=self.headers, params=params, json=data
            )
            response.raise_for_status()
            logger.info(f"Requisição {method} para {url} bem-sucedida.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição {method} para {url}: {str(e)}")
        return None

    def get_pending_items(self, stage):
        """Obtém todos os itens pendentes do painel, filtrados por robô e estágio."""
        endpoint = "items/by-stage/"
        params = {"stage": stage}
        response = self._make_request("GET", endpoint, params=params)
    
        if response is None:
            logger.error(f"Falha ao buscar itens no estágio {stage}.")
            return None

        logger.info(f"{len(response)} itens encontrados no estágio {stage}.")
        return response


    def get_shift_data(self, item_id):
        """Obtém os dados de Shift para um item específico usando o ID do item."""
        endpoint = f"shift-data/{item_id}/"
        return self._make_request("GET", endpoint)

    def get_sismama_data(self):
        """Obtém os dados do SISMAMA do endpoint `/items/sismama-data/`."""
        endpoint = "items/sismama-data/"
        return self._make_request("GET", endpoint)

    def create_shift_data(self, shift_data):
        """Envia os dados do shift para o backend."""
        endpoint = "shift-data/"
        try:
            logger.info(
                f"Enviando dados do Shift: {json.dumps(shift_data, indent=4, ensure_ascii=False)}"
            )
            response = self._make_request("POST", endpoint, data=shift_data)
            if response:
                logger.info(
                    f"Dados do Shift enviados com sucesso: {json.dumps(response, indent=4, ensure_ascii=False)}"
                )
            return response
        except Exception as e:
            logger.error(f"Erro ao enviar os dados do Shift: {str(e)}")
        return None

    def update_task(self, task_id, **kwargs):
        """Atualiza uma tarefa específica."""
        endpoint = f"tasks/{task_id}/update-task/"
        data = {k: v for k, v in kwargs.items() if v is not None}
        return self._make_request("PATCH", endpoint, data=data)

    def update_item(self, item_id, **kwargs):
        """Atualiza um item específico."""
        endpoint = f"items/{item_id}/"
        data = {k: v for k, v in kwargs.items() if v is not None}
        try:
            logger.info(
                f"Atualizando item {item_id} com os dados: {json.dumps(data, indent=4, ensure_ascii=False)}"
            )
            response = self._make_request("PATCH", endpoint, data=data)
            if response:
                logger.info(f"Item {item_id} atualizado com sucesso.")
            return response
        except Exception as e:
            logger.error(f"Erro ao atualizar o item {item_id}: {str(e)}")
        return None

    def refresh_token(self, refresh_token):
        """Atualiza o token JWT usando o token de refresh."""
        endpoint = "login/token/refresh/"
        data = {"refresh": refresh_token}
        return self._make_request("POST", endpoint, data=data)
