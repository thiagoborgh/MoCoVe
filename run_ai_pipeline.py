import subprocess
import time
import os

# 1. Treinar modelo
print('Treinando modelo...')
subprocess.run(['python', 'train_model.py'], check=True)

# 2. Iniciar serviço FastAPI (ai_model.py)
print('Iniciando serviço FastAPI...')
# Mata qualquer processo uvicorn anterior
os.system('taskkill /F /IM uvicorn.exe >nul 2>&1')
# Aguarda modelo ser salvo
time.sleep(2)
subprocess.Popen(['uvicorn', 'ai_model:app', '--host', '0.0.0.0', '--port', '5000'])
print('Serviço AI rodando em http://localhost:5000/predict')

# 3. (Opcional) Você pode adicionar aqui um healthcheck ou integração contínua
