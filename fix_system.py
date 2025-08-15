#!/usr/bin/env python3
"""
Script de Checagem e Correção Automática - MoCoVe
Verifica problemas comuns e tenta corrigir automaticamente
"""

import os
import sys
import subprocess
import sqlite3
import json
from pathlib import Path

def check_and_fix_environment():
    """Verificar e corrigir ambiente"""
    print("🔧 Verificando ambiente do sistema...")
    
    # 1. Verificar arquivo .env
    if not os.path.exists('.env'):
        print("⚠️ Arquivo .env não encontrado")
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Arquivo .env criado a partir do exemplo")
        else:
            with open('.env', 'w') as f:
                f.write("""# Configurações do MoCoVe
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_secret_here
USE_TESTNET=true
DEFAULT_SYMBOL=DOGEUSDT
DEFAULT_AMOUNT=10.0
DB_PATH=memecoin.db
DEBUG=true
""")
            print("✅ Arquivo .env criado com valores padrão")
    
    # 2. Verificar database
    if not os.path.exists('memecoin.db'):
        print("⚠️ Database não encontrado. Criando...")
        try:
            conn = sqlite3.connect('memecoin.db')
            conn.execute('''CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                price REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            conn.commit()
            conn.close()
            print("✅ Database criado")
        except Exception as e:
            print(f"❌ Erro ao criar database: {e}")
    
    # 3. Verificar watchlist
    if not os.path.exists('coin_watchlist_expanded.json'):
        print("⚠️ Watchlist não encontrada. Criando padrão...")
        default_watchlist = {
            "coins": [
                {"symbol": "DOGEUSDT", "enabled": True},
                {"symbol": "SHIBUSDT", "enabled": True},
                {"symbol": "PEPEUSDT", "enabled": True}
            ]
        }
        with open('coin_watchlist_expanded.json', 'w') as f:
            json.dump(default_watchlist, f, indent=2)
        print("✅ Watchlist criada")
    
    # 4. Verificar arquivo de configuração da IA
    if not os.path.exists('ai_agent_config.json'):
        print("⚠️ Configuração da IA não encontrada. Criando padrão...")
        default_config = {
            "trading_enabled": False,
            "symbol": "DOGEUSDT",
            "monitoring_interval": 30,
            "min_confidence": 0.7,
            "max_position_size": 50.0,
            "max_daily_trades": 10,
            "stop_loss_pct": 0.02,
            "take_profit_pct": 0.03,
            "min_trade_interval": 300,
            "risk_level": "conservative",
            "strategies_enabled": {
                "moving_averages": True,
                "rsi": True,
                "bollinger_bands": True,
                "trend_following": True,
                "volatility_filter": True
            },
            "notifications": {
                "trade_execution": True,
                "high_confidence_signals": True,
                "daily_summary": True
            }
        }
        with open('ai_agent_config.json', 'w') as f:
            json.dump(default_config, f, indent=2)
        print("✅ Configuração da IA criada")

def check_dependencies():
    """Verificar dependências Python"""
    print("📦 Verificando dependências...")
    
    required_packages = [
        'flask', 'flask-cors', 'ccxt', 'pandas', 'numpy', 
        'requests', 'python-dotenv', 'scikit-learn'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - FALTANDO")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Pacotes faltando: {', '.join(missing_packages)}")
        print("💡 Execute: pip install -r requirements.txt")
        return False
    
    return True

def check_ports():
    """Verificar se portas estão livres"""
    print("🔌 Verificando portas...")
    
    import socket
    
    def is_port_free(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return True
            except OSError:
                return False
    
    ports_to_check = [5000, 3000, 8080]
    
    for port in ports_to_check:
        if is_port_free(port):
            print(f"✅ Porta {port} livre")
        else:
            print(f"⚠️ Porta {port} em uso")

def main():
    """Função principal"""
    print("🚀 MoCoVe - Checagem e Correção Automática")
    print("=" * 50)
    
    # Verificações
    check_and_fix_environment()
    deps_ok = check_dependencies()
    check_ports()
    
    print("\n" + "=" * 50)
    if deps_ok:
        print("✅ Sistema pronto para execução!")
        print("💡 Execute: python start_complete_system.py")
    else:
        print("⚠️ Corrija as dependências antes de continuar")
        print("💡 Execute: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
