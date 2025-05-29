from src.browser.pages.login_page import ShiftLoginPage
from src.browser.pages.os_consulta_page import OSConsultaPage
from src.browser.utils.browser_manager import finalizar_driver, iniciar_driver
from src.config.logger import logger
from src.controllers.anatomopatologico_controller import extrair_dados_anatomopatologico
from src.controllers.api_handler import (
    atualizar_item_erro_shift,
    atualizar_item_fim,
    atualizar_item_inicio,
    atualizar_tarefa_inicio,
    upsert_shift_data,
)
from src.controllers.buscar_numero_recipiente import buscar_prefixo_numero_recipiente
from src.controllers.endereco_controller import extrair_dados_endereco
from src.controllers.navigation_handler import (
    acessar_informacoes_paciente,
    buscar_os_no_sistema,
    esperar_tela_manutencao,
    fechar_janela_exame,
    fechar_janela_manutencao,
)
from src.controllers.paciente_controller import (
    extrair_dados_paciente,
    extrair_informacoes_paciente,
    obter_nome_paciente,
)


class ShiftController:
    """
    Controlador para gerenciar fluxos de automação no sistema SHIFT.
    """

    def __init__(self, url, usuario, senha, screenshot_path, api_client, robot_id):
        """Inicializa o controlador."""
        self.url = url
        self.usuario = usuario
        self.senha = senha
        self.screenshot_path = screenshot_path
        self.driver = iniciar_driver()
        self.login_page = ShiftLoginPage(self.driver)
        self.os_page = OSConsultaPage(self.driver)
        self.api_client = api_client
        self.robot_id = robot_id

    def realizar_login(self):
        """Realiza o login no sistema SHIFT."""
        try:
            logger.info("Iniciando fluxo de login.")
            self.login_page.acessar_pagina(self.url)
            self.login_page.preencher_usuario(self.usuario)
            self.login_page.preencher_senha(self.senha)
            self.login_page.clicar_login()

            if self.login_page.verificar_erro_login():
                logger.warning("Senha incorreta")
                return False

            logger.success("Login realizado com sucesso.")
            return True
        except Exception as e:
            logger.error(f"Erro durante o login: {str(e)}")
            return False

    def acessar_os_consulta(self):
        """Acessa a página de O.S Consulta após realizar o login."""
        try:
            logger.info("Acessando a página de O.S Consulta...")
            self.os_page.clicar_menu()
            self.os_page.pesquisar_os_consulta("O.S")
            logger.success("Página de O.S Consulta acessada com sucesso.")
            return True
        except Exception as e:
            logger.error(f"Erro ao acessar O.S Consulta: {str(e)}")
            return False

    def processar_dados(self, tasks):
        """Processa as tarefas recebidas, extrai dados e envia à API."""
        if not tasks:
            logger.warning("Nenhuma tarefa foi fornecida para processamento.")
            return

        if not self.realizar_login() or not self.acessar_os_consulta():
            return

        for task in tasks:
            os_numero = task.get("os")
            nome_pessoa = task.get("os_name")
            task_id = task["task_id"]
            item_id = task["item_id"]

            if not os_numero or not nome_pessoa:
                logger.warning(f"Tarefa {task_id} está incompleta: OS ou nome ausente.")
                continue

            atualizar_tarefa_inicio(self.api_client, task_id, nome_pessoa)
            atualizar_item_inicio(self.api_client, item_id)

            if not buscar_os_no_sistema(
                self.driver, self.api_client, task_id, item_id, os_numero
            ):
                continue  # Pula para a próxima O.S.

            dados_extraidos = self._extrair_dados_do_shift(os_numero, item_id, nome_pessoa)
            if not dados_extraidos:
                continue

            upsert_shift_data(self.api_client, task_id, item_id, dados_extraidos)
            atualizar_item_fim(
                self.api_client,
                item_id,
                status="COMPLETED",
                shift_result="PROCESSO FINALIZADO",
                stage="IMAGE_PROCESS",
            )

        logger.info("Processamento das tarefas concluído.")

    def _extrair_dados_do_shift(self, os_numero, item_id, nome_pessoa):
        """Extrai e organiza os dados da O.S."""

        recipiente_encontrado = buscar_prefixo_numero_recipiente(self.driver)
        logger.success(f"Recipiente encontrado: {recipiente_encontrado}")

        if not recipiente_encontrado:
            logger.warning("Recipiente correspondente à imagem não foi encontrado.")
            atualizar_item_erro_shift(
                self.api_client,
                item_id,
                "Recipiente correspondente à imagem não foi encontrado.",
            )
            return None

        nome_paciente_tela = obter_nome_paciente(self.driver)

        if not nome_paciente_tela or nome_paciente_tela != nome_pessoa:
            return None

        dados_paciente = extrair_dados_paciente(self.driver)
        dados_anatomopatologico = extrair_dados_anatomopatologico(self.driver)

        fechar_janela_exame(self.driver)
        if not acessar_informacoes_paciente(self.driver):
            return None

        if not esperar_tela_manutencao(self.driver):
            return None

        dados_paciente_guia_geral = extrair_informacoes_paciente(self.driver)
        dados_endereco = extrair_dados_endereco(self.driver)
        fechar_janela_manutencao(self.driver)

        return {
            "os_number": os_numero,
            "nome_paciente": nome_pessoa,
            "recipiente": recipiente_encontrado,
            **dados_paciente,
            **dados_anatomopatologico,
            **dados_paciente_guia_geral,
            **dados_endereco,
        }

    def finalizar(self):
        """Finaliza o navegador."""
        finalizar_driver(self.driver)
