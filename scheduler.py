import schedule
import time
import traceback
from datetime import datetime
from main import OrquestradorRPA

executando = False

def rodar_main():
    global executando
   
    if executando:
        print(f"[{datetime.now()}] Execução anterior ainda em andamento. Pulando...")
        return

    try:
        executando = True
        print(f"[{datetime.now()}] Iniciando RPA...")
        orquestrador = OrquestradorRPA()
        orquestrador.executar()
        print(f"[{datetime.now()}] RPA finalizada!")
    except Exception as e:
        print("Erro ao executar RPA:")
        traceback.print_exc()
    finally:
        executando = False

# Agendamento a cada 1 minuto
schedule.every(1).minutes.do(rodar_main)

if __name__ == "__main__":
    print("Iniciando Scheduler...")
    while True:
        schedule.run_pending()
        time.sleep(1)