import requests
from .logger import logger
from src.config.config import Config


class AuthenticationService:
    """Serviço de autenticação para gerenciar login e tokens."""

    @staticmethod
    def authenticate(username, password):
        """Autentica o usuário e retorna os tokens."""
        auth_url = f"{Config.API_URL}login/token/"
        data = {"username": username, "password": password}
        try:
            response = requests.post(auth_url, json=data)
            response.raise_for_status()
            logger.info("Autenticação bem-sucedida.")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erro durante a autenticação: {str(e)}")
            return None
