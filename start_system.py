#!/usr/bin/env python3
"""
MoCoVe Sistema Completo - Launcher
Inicialização completa do sistema com watchlist robusta
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path

def print_banner():
    """Imprimir banner do sistema"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                    🚀 MoCoVe AI Trading System                ║
    ║                  Sistema de Trading Inteligente              ║
    ║                    com Watchlist Robusta                     ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    📊 Funcionalidades Implementadas:
    ✅ AI Trading Agent com análise técnica avançada
    ✅ Backend Python Flask com Binance Real
    ✅ Frontend React Dashboard responsivo
    ✅ Watchlist Robusta com 30+ moedas
    ✅ Sistema de alertas automáticos
    ✅ Monitoramento em tempo real
    ✅ Configuração usando .env existente (porta 5000)
    
    """)

def check_files():
    """Verificar se os arquivos necessários existem"""
    required_files = [
        'coin_watchlist.json',
        'watchlist_manager.py',
        'backend/app_real.py',
        'frontend/index.html',
        'price_update_job.py',
        '.env'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Arquivos em falta:")
        for file in missing_files:
            print(f"   • {file}")
        return False
    
    print("✅ Todos os arquivos necessários encontrados")
    return True

def check_watchlist():
    """Verificar configuração da watchlist"""
    try:
        with open('coin_watchlist.json', 'r', encoding='utf-8') as f:
            watchlist = json.load(f)
        
        total_coins = 0
        
        # Contar memecoins
        for tier, coins in watchlist['memecoins'].items():
            if isinstance(coins, list):
                total_coins += len(coins)
                print(f"📈 {tier}: {len(coins)} moedas")
        
        # Contar altcoins
        for category, coins in watchlist['altcoins'].items():
            total_coins += len(coins)
            print(f"🔷 alt_{category}: {len(coins)} moedas")
        
        print(f"📊 Total: {total_coins} moedas na watchlist")
        
        # Verificar configurações
        config = watchlist.get('watchlist_config', {})
        alerts_enabled = config.get('price_alerts', {}).get('enabled', False)
        auto_trading = config.get('auto_trading', {}).get('enabled', False)
        
        print(f"🚨 Alertas: {'✅ Habilitados' if alerts_enabled else '❌ Desabilitados'}")
        print(f"🤖 Auto-trading: {'✅ Habilitado' if auto_trading else '❌ Desabilitado'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar watchlist: {e}")
        return False

def check_env():
    """Verificar configuração .env"""
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # Verificar variáveis importantes
        required_vars = ['BINANCE_API_KEY', 'BINANCE_API_SECRET', 'PORT']
        found_vars = {}
        
        for line in env_content.split('\n'):
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if key in required_vars:
                    found_vars[key] = '***' if 'KEY' in key or 'SECRET' in key else value
        
        print("🔧 Configuração .env:")
        for var in required_vars:
            if var in found_vars:
                print(f"   ✅ {var}: {found_vars[var]}")
            else:
                print(f"   ❌ {var}: Não encontrado")
        
        return len(found_vars) >= 2  # Pelo menos API key e secret
        
    except Exception as e:
        print(f"❌ Erro ao verificar .env: {e}")
        return False

def start_backend():
    """Iniciar backend"""
    print("\n🔧 Iniciando Backend Python...")
    try:
        # Usar subprocess para iniciar o backend
        backend_process = subprocess.Popen([
            sys.executable, 'backend/app_real.py'
        ], cwd=os.getcwd())
        
        print("✅ Backend iniciado (PID: {})".format(backend_process.pid))
        
        # Aguardar alguns segundos para o backend inicializar
        time.sleep(3)
        
        # Verificar se o processo ainda está rodando
        if backend_process.poll() is None:
            print("✅ Backend rodando em http://localhost:5000")
            return backend_process
        else:
            print("❌ Backend falhou ao iniciar")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao iniciar backend: {e}")
        return None

def start_price_updater():
    """Iniciar job de atualização de preços"""
    print("\n📊 Iniciando Price Update Job...")
    try:
        price_process = subprocess.Popen([
            sys.executable, 'price_update_job.py'
        ], cwd=os.getcwd())
        
        print("✅ Price Update Job iniciado (PID: {})".format(price_process.pid))
        time.sleep(1)
        
        if price_process.poll() is None:
            return price_process
        else:
            print("❌ Price Update Job falhou ao iniciar")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao iniciar price updater: {e}")
        return None

def show_urls():
    """Mostrar URLs de acesso"""
    print("""
    🌐 URLs de Acesso:
    
    📊 Dashboard Principal:     http://localhost:5000
    📈 API Watchlist:          http://localhost:5000/api/watchlist/summary
    🚨 Alertas:                http://localhost:5000/api/watchlist/alerts
    🏆 Top Performers:         http://localhost:5000/api/watchlist/top-performers
    🔧 Configurações:          http://localhost:5000/api/settings
    
    """)

def main():
    """Função principal"""
    print_banner()
    
    # Verificações
    print("🔍 Verificando sistema...")
    
    if not check_files():
        print("\n❌ Sistema incompleto. Execute a configuração primeiro.")
        return
    
    if not check_watchlist():
        print("\n❌ Watchlist inválida.")
        return
    
    if not check_env():
        print("\n❌ Configuração .env inválida.")
        return
    
    print("\n✅ Todas as verificações passaram!")
    
    # Iniciar componentes
    backend_process = start_backend()
    if not backend_process:
        print("\n❌ Falha ao iniciar backend")
        return
    
    price_process = start_price_updater()
    
    # Mostrar informações
    show_urls()
    
    print("🎯 Sistema MoCoVe inicializado com sucesso!")
    print("📊 Watchlist robusta com monitoramento automático ativada")
    print("🚀 AI Trading Agent operacional")
    print("\n⏹️  Pressione Ctrl+C para parar o sistema")
    
    try:
        # Manter processos rodando
        while True:
            time.sleep(10)
            
            # Verificar se os processos ainda estão rodando
            if backend_process.poll() is not None:
                print("❌ Backend parou inesperadamente")
                break
                
            if price_process and price_process.poll() is not None:
                print("⚠️ Price Update Job parou")
                price_process = start_price_updater()
                
    except KeyboardInterrupt:
        print("\n⏹️ Parando sistema...")
        
        if backend_process:
            backend_process.terminate()
            print("✅ Backend parado")
            
        if price_process:
            price_process.terminate()
            print("✅ Price Update Job parado")
            
        print("👋 Sistema finalizado")

if __name__ == "__main__":
    main()
