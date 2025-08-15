#!/usr/bin/env python3
"""
Script para inicializar sistema MoCoVe completo
"""

import subprocess
import time
import os
import sys

def run_command_background(cmd, title="Process"):
    """Executa comando em background"""
    try:
        if os.name == 'nt':  # Windows
            subprocess.Popen(f'start "{title}" cmd /k "{cmd}"', shell=True)
        else:  # Unix/Linux
            subprocess.Popen(cmd, shell=True)
        return True
    except Exception as e:
        print(f"Erro ao executar {title}: {e}")
        return False

def main():
    print("🚀 Iniciando Sistema MoCoVe...")
    
    # Configurar variáveis de ambiente
    env_vars = {
        'BINANCE_API_KEY': 'HxfDczSoWcWa1O3OUU65nSa98VTXrPhVjHYY545r2XSdrnHQAyDJsJoeDw9rs32o',
        'BINANCE_API_SECRET': 'lJrrJ55ssd7sE2XBLXJY2mqs2M4TmnpgyhTRtVHU1WXJltpJk7McsDCUeT4jjO0p',
        'USE_TESTNET': 'true',
        'DEFAULT_SYMBOL': 'DOGE/USDT',
        'DEFAULT_AMOUNT': '25.0'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Variáveis de ambiente configuradas")
    
    # Definir comandos
    commands = [
        {
            'cmd': 'cd backend && python app.py',
            'title': 'MoCoVe Backend API',
            'wait': 3
        },
        {
            'cmd': 'python ai_trading_agent_robust.py',
            'title': 'AI Trading Agent',
            'wait': 2
        },
        {
            'cmd': 'python -m http.server 8000',
            'title': 'Frontend Server',
            'wait': 2
        }
    ]
    
    # Executar comandos
    for cmd_info in commands:
        print(f"📡 Iniciando {cmd_info['title']}...")
        if run_command_background(cmd_info['cmd'], cmd_info['title']):
            print(f"✅ {cmd_info['title']} iniciado")
            time.sleep(cmd_info['wait'])
        else:
            print(f"❌ Erro ao iniciar {cmd_info['title']}")
    
    print("\n🎉 Sistema MoCoVe iniciado com sucesso!")
    print("\n🌐 URLs importantes:")
    print("   Dashboard: http://localhost:8000/frontend/index_complete_dashboard_clean.html")
    print("   API Status: http://localhost:5000/api/system/status")
    print("\n⚡ Todos os componentes estão rodando em background")
    print("💡 Use Ctrl+C nos terminais individuais para parar cada serviço")

if __name__ == "__main__":
    main()
