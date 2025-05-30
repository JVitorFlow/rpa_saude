import os
import time
import subprocess
from typing import Any, List
import ctypes
import pygetwindow as gw

from src.config.logger import logger
from src.utils.imagens import espera_imagem_aparecer


def is_admin() -> bool:
    """
    Verifica se o processo atual está rodando com privilégios de administrador.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


class SismamaRunner:
    """
    Responsável pelo fluxo de abertura, preenchimento e finalização do SIS MAMA.
    """

    def __init__(self, api_client: Any) -> None:
        self.api_client = api_client
        self._load_config()

    def _load_config(self) -> None:
        env = os.getenv
        self.sismama_path = env('CAMINHO_SISTEMA_SISMAMA', '')
        self.cadastro_img = env('CADASTRO01_IMAGE', '')
        self.window_title = 'Requisição de Exame Histopatológico - MAMA'

    def executar(self) -> None:
        start = time.time()
        try:
            self._processar_sismama()
        finally:
            elapsed = time.time() - start
            logger.info(f'Tempo total SIS MAMA: {elapsed:.2f}s')

    def _processar_sismama(self) -> None:
        pending = self.api_client.get_sismama_data()
        if not pending or (
            isinstance(pending, dict) and pending.get('detail')
        ):
            logger.info('Nenhum dado pendente para SIS MAMA.')
            return

        logger.info(f'{len(pending)} registro(s) autorizado(s).')
        self._abrir_sismama()
        self._preencher_sismama(pending)
        self._finalizar_sismama()

    def _abrir_sismama(self) -> None:
        logger.info('Abrindo SIS MAMA')
        if not is_admin():
            raise PermissionError(
                'Privilégios de administrador são necessários.'
            )

        result = subprocess.run(
            [self.sismama_path],
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            error_msg = result.stderr.decode().strip()
            logger.error(f'Falha ao abrir SIS MAMA: {error_msg}')
            raise RuntimeError('Não foi possível iniciar SIS MAMA')

        espera_imagem_aparecer(self.cadastro_img, None, 0.9)
        self._maximize_window()

    def _maximize_window(self) -> None:
        time.sleep(1)
        windows = gw.getWindowsWithTitle(self.window_title)
        if not windows:
            logger.warning(f"Janela '{self.window_title}' não encontrada.")
            return
        windows[0].maximize()
        logger.info('Janela maximizada.')

    def _preencher_sismama(self, data: List[dict]) -> None:
        from .sismama_digitador import SismamaDigitador

        logger.info('Preenchendo SIS MAMA')
        digitador = SismamaDigitador(api_client=self.api_client)
        digitador.inserir_dados_sismama(data)

    def _finalizar_sismama(self) -> None:
        logger.info('Finalizando SIS MAMA')
        result = subprocess.run(
            ['taskkill', '/IM', 'SisMamaFB.exe', '/F'],
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            error_msg = result.stderr.decode().strip()
            logger.error(f'Falha ao encerrar SisMamaFB.exe: {error_msg}')
            raise RuntimeError('Não foi possível finalizar SIS MAMA')
