from src.config.logger import logger
from src.utils.data_utils import formatar_data_iso
from datetime import datetime

def gerar_payload_api(task_id, item_id, dados):
    """Gera o payload padronizado para envio à API."""
    return {
        "task": task_id,
        "item": item_id,
        "os_number": dados.get("os_number", ""),
        "nome_paciente": dados.get("nome_paciente", ""),
        "idade_paciente": (
            int(dados["idade_paciente"]) if dados.get("idade_paciente") else None
        ),
        "raca_etinia": dados.get("raca_etinia"),
        "cartao_sus": dados.get("CNS"),
        "data_coleta": formatar_data_iso(dados.get("data_coleta")),
        "data_liberacao": formatar_data_iso(dados.get("data_liberacao")),
        "tamanho_lesao": dados.get("tamanho_lesao"),
        "caracteristica_lesao": dados.get("caracteristica_lesao"),
        "localizacao_lesao": dados.get("localizacao_lesao"),
        "data_nascimento": formatar_data_iso(dados.get("data_nascimento")),
        "sexo": dados.get("Sexo"),
        "codigo_postal": dados.get("codigo_postal"),
        "logradouro": dados.get("logradouro"),
        "numero_residencial": dados.get("numero_residencial"),
        "cidade": dados.get("cidade"),
        "estado": dados.get("estado"),
        "status_shift": None,
        "shift_result": None,
        "sismama_result": None,
        "stage": None
    }

def enviar_dados_api(api_client, task_id, item_id, dados):
    """Envia os dados extraídos para a API."""
    try:
        payload = gerar_payload_api(task_id, item_id, dados)
        logger.info(f"Enviando dados para API: {payload}")

        response = api_client.create_shift_data(payload)

        if response:
            logger.info(f"Dados enviados com sucesso: {response}")
        else:
            logger.error(f"Falha ao enviar dados para a API para tarefa {task_id}.")

    except Exception as e:
        logger.error(f"Erro ao enviar dados para API: {str(e)}")


def atualizar_tarefa_inicio(api_client, task_id, nome_pessoa):
    """Atualiza o status da tarefa para 'STARTED' na API."""
    started_at = datetime.now().isoformat(timespec="seconds")
    shift_result = f"Processamento iniciado para {nome_pessoa}"

    response = api_client.update_task(
        task_id=task_id,
        status="STARTED",
        started_at=started_at,
        shift_result=shift_result,
        stage="PROCESSING",
    )

    if response:
        logger.info(f"Tarefa {task_id} atualizada para 'STARTED' com sucesso.")
    else:
        logger.error(f"Falha ao atualizar tarefa {task_id} para 'STARTED'.")

def atualizar_item_inicio(api_client, item_id):
    """Atualiza o status do item para 'STARTED' na API."""
    started_at = datetime.now().isoformat(timespec="seconds")

    response = api_client.update_item(
        item_id=item_id, status="STARTED", started_at=started_at, stage="SHIFT"
    )

    if response:
        logger.info(f"Item {item_id} atualizado para 'STARTED' com sucesso.")
    else:
        logger.error(f"Falha ao atualizar item {item_id} para 'STARTED'.")

def atualizar_item_fim(api_client, item_id, status, shift_result, stage=None):
    """
    Atualiza o status do item para 'COMPLETED' ou outro status desejado.
    
    Args:
        api_client: Cliente da API para enviar a requisição.
        item_id (int): ID do item a ser atualizado.
        status (str): Novo status do item.
        shift_result (str): Mensagem de resultado do processamento.
        stage (str, optional): Estágio do processamento (se aplicável).
    """
    dados = {
        "status": status,
        "shift_result": shift_result,
    }

    if stage:  # Apenas adiciona se `stage` for passado
        dados["stage"] = stage

    logger.info(f"Atualizando item {item_id} para '{status}' com stage '{stage}'.")
    response = api_client.update_item(item_id, **dados)

    if response:
        logger.info(f"Item {item_id} atualizado com sucesso.")
    else:
        logger.error(f"Falha ao atualizar item {item_id}.")


def atualizar_item_sismama(api_client, item_id):
    """
    Atualiza o status do item para 'COMPLETED' no estágio SISMAMA.
    
    Args:
        api_client: Cliente da API para enviar a requisição.
        item_id (int): ID do item a ser atualizado.
    """
    dados = {
        "status": "COMPLETED",
        "stage": "COMPLETED",
        "ended_at": datetime.now().isoformat(),
        "sismama_result": "Processamento finalizado sem alertas."
    }

    logger.info(f"Atualizando item {item_id} para 'COMPLETED' no estágio 'SISMAMA'.")
    response = api_client.update_item(item_id, **dados)

    if response:
        logger.info(f"Item {item_id} atualizado com sucesso no SISMAMA.")
    else:
        logger.error(f"Falha ao atualizar item {item_id} para 'COMPLETED'.")


def atualizar_item_erro_sismama(api_client, item_id, mensagem_erro):
    """
    Atualiza o status do item para 'ERROR' no estágio SISMAMA.

    Args:
        api_client: Cliente da API para enviar a requisição.
        item_id (int): ID do item a ser atualizado.
        mensagem_erro (str): Mensagem de erro descritiva.
    """
    dados = {
        "status": "ERROR",
        "stage": "SISMAMA",
        "ended_at": datetime.now().isoformat(),
        "bot_error_message": mensagem_erro,
    }

    logger.info(f"Atualizando item {item_id} para 'ERROR' no estágio 'SISMAMA'.")
    response = api_client.update_item(item_id, **dados)

    if response:
        logger.info(f"Item {item_id} atualizado como 'ERROR' no SISMAMA com mensagem: {mensagem_erro}")
    else:
        logger.error(f"Falha ao atualizar item {item_id} para 'ERROR'.")
