import time
import subprocess
import os

INTERVAL_MINUTES = 60  # Treinar e reiniciar AI a cada 60 minutos

while True:
    print('\n[AI PIPELINE] Treinando modelo e reiniciando serviço AI...')
    subprocess.run(['python', 'train_model.py'], check=True)
    # Mata qualquer processo uvicorn anterior
    os.system('taskkill /F /IM uvicorn.exe >nul 2>&1')
    time.sleep(2)
    subprocess.Popen(['uvicorn', 'ai_model:app', '--host', '0.0.0.0', '--port', '5000'])
    print('[AI PIPELINE] Serviço AI rodando em http://localhost:5000/predict')
    print(f'[AI PIPELINE] Próxima atualização em {INTERVAL_MINUTES} minutos...')
    time.sleep(INTERVAL_MINUTES * 60)
