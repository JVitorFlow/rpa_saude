import time
import traceback
from datetime import datetime

import schedule

from main import OrquestradorRPA

executando = False

def rodar_main():
    global executando

    if executando:
        print(f"[{datetime.now()}] Execução anterior ainda em andamento. Pulando...")
        return

    try:
        executando = True
        print(f"[{datetime.now()}] Iniciando RPA…")

        
        orquestrador = OrquestradorRPA()

        
        if not orquestrador.autenticar_api():
            print(f"[{datetime.now()}] Falha na autenticação. Abortando esta execução.")
            executando = False
            return

        orquestrador.api_client.send_alert(
            robot_id=orquestrador.config.ROBOT_ID,
            alert_type="Informacao",
            message="RPA iniciando execução."
        )

        orquestrador.executar()


        orquestrador.api_client.send_alert(
            robot_id=orquestrador.config.ROBOT_ID,
            alert_type="Sucesso",
            message="RPA concluiu execução com sucesso."
        )

    except Exception as e:
        print(f"[{datetime.now()}] Erro ao executar RPA:")
        traceback.print_exc()

        # Se o api_client já existir (autenticou antes), envia alerta de erro
        if orquestrador.api_client:
            detalhes = traceback.format_exc()
            orquestrador.api_client.send_alert(
                robot_id=orquestrador.config.ROBOT_ID,
                alert_type="Erro",
                message="Falha durante execução da RPA.",
                details=detalhes
            )
    finally:
        executando = False


schedule.every(1).minutes.do(rodar_main)

if __name__ == "__main__":
    print("Iniciando Scheduler…")
    while True:
        schedule.run_pending()
        time.sleep(1)
