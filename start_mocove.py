#!/usr/bin/env python3
"""
Script de Inicialização do MoCoVe - Sistema Completo
Inicia backend, testa sistema e prepara para trading real
"""

import subprocess
import time
import requests
import webbrowser
from datetime import datetime
import signal
import sys
import os

def kill_existing_processes():
    """Para processos existentes do Flask na porta 5000"""
    print("🔄 Verificando processos existentes...")
    try:
        # Para Windows - mata processos na porta 5000
        subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        # Simples approach: apenas avisa o usuário
        print("⚠️  Se houver erro de porta ocupada, pare outros processos manualmente")
    except:
        pass

def start_backend():
    """Inicia o backend em processo separado"""
    print("🚀 Iniciando Backend MoCoVe...")
    
    backend_path = os.path.join("backend", "app_real.py")
    if not os.path.exists(backend_path):
        print(f"❌ Arquivo backend não encontrado: {backend_path}")
        return None
    
    try:
        # Inicia o backend em processo separado
        process = subprocess.Popen(
            [sys.executable, backend_path],
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        print(f"✅ Backend iniciado (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Erro ao iniciar backend: {e}")
        return None

def wait_for_backend(max_attempts=30):
    """Aguarda o backend ficar disponível"""
    print("⏳ Aguardando backend ficar disponível...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:5000/api/status", timeout=2)
            if response.status_code == 200:
                print("✅ Backend disponível!")
                return True
        except:
            pass
        
        print(f"   Tentativa {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    print("❌ Backend não respondeu dentro do tempo limite")
    return False

def test_system():
    """Testa funcionalidades principais"""
    print("\n🧪 TESTANDO SISTEMA")
    print("=" * 40)
    
    tests = []
    
    # Teste 1: Status da API
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Status: {data.get('status')}")
            print(f"🏦 Exchange: {'Conectada' if data.get('exchange_connected') else 'Desconectada'}")
            print(f"📊 Símbolo: {data.get('default_symbol')}")
            tests.append(True)
        else:
            print(f"❌ Erro API Status: {response.status_code}")
            tests.append(False)
    except Exception as e:
        print(f"❌ Erro API Status: {e}")
        tests.append(False)
    
    # Teste 2: Dados de Mercado
    try:
        response = requests.get("http://localhost:5000/api/market_data?symbol=DOGEUSDT", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ DOGE/USDT: ${data.get('price', 'N/A')}")
            tests.append(True)
        else:
            print(f"❌ Erro Dados Mercado: {response.status_code}")
            tests.append(False)
    except Exception as e:
        print(f"❌ Erro Dados Mercado: {e}")
        tests.append(False)
    
    # Teste 3: Saldos
    try:
        response = requests.get("http://localhost:5000/api/balance", timeout=10)
        if response.status_code == 200:
            balances = response.json()
            balance_count = len([b for b in balances.values() if b.get('total', 0) > 0.001])
            print(f"✅ Saldos carregados: {balance_count} moedas")
            tests.append(True)
        else:
            print(f"❌ Erro Saldos: {response.status_code}")
            tests.append(False)
    except Exception as e:
        print(f"❌ Erro Saldos: {e}")
        tests.append(False)
    
    return all(tests)

def show_status():
    """Mostra status atual do sistema"""
    print("\n📊 STATUS DO SISTEMA")
    print("=" * 40)
    print(f"🕐 Hora: {datetime.now().strftime('%H:%M:%S')}")
    print("🌐 Interface: http://localhost:5000")
    print("🏦 Conta: Binance REAL (não testnet)")
    print("🛡️  Limites: $100 max trade, $50 max perda diária")
    print("⚡ Símbolo padrão: DOGEUSDT")

def show_safety_reminders():
    """Mostra lembretes importantes de segurança"""
    print("\n🚨 LEMBRETES DE SEGURANÇA")
    print("=" * 40)
    print("🔴 CONTA REAL: Trading com dinheiro real")
    print("💰 COMECE PEQUENO: Primeiro trade $5-10")
    print("👀 MONITORE: Acompanhe todas as operações")
    print("🛑 EMERGÊNCIA: Ctrl+C para parar sistema")
    print("💻 MANUAL: Use binance.com se necessário")

def signal_handler(signum, frame):
    """Manipula sinais de interrupção"""
    print("\n\n🛑 Parando sistema...")
    sys.exit(0)

def main():
    """Função principal"""
    print("🎯 MoCoVe - Sistema de Trading Real")
    print("=" * 50)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Configura manipulador de sinal
    signal.signal(signal.SIGINT, signal_handler)
    
    # Mata processos existentes se necessário
    kill_existing_processes()
    
    # Inicia backend
    backend_process = start_backend()
    if not backend_process:
        print("❌ Falha ao iniciar backend")
        return
    
    try:
        # Aguarda backend ficar disponível
        if not wait_for_backend():
            print("❌ Backend não ficou disponível")
            return
        
        # Testa sistema
        if test_system():
            print("\n🎉 SISTEMA FUNCIONANDO!")
            
            # Mostra informações
            show_status()
            show_safety_reminders()
            
            # Abre navegador
            print(f"\n🌐 Abrindo interface web...")
            webbrowser.open("http://localhost:5000")
            
            print("\n✅ PRONTO PARA TRADING!")
            print("=" * 30)
            print("Interface web aberta no navegador")
            print("Backend rodando em background")
            print("Pressione Ctrl+C para parar")
            
            # Mantém o script rodando
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("❌ Falhas nos testes do sistema")
    
    finally:
        # Para o backend
        if backend_process:
            print(f"\n🛑 Parando backend (PID: {backend_process.pid})...")
            backend_process.terminate()
            backend_process.wait()
            print("✅ Backend parado")

if __name__ == "__main__":
    main()
