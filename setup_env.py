#!/usr/bin/env python3
"""
Script para inicializar o ambiente e carregar configurações
"""

import os
import sys
from pathlib import Path

def load_env_file(env_file='.env.example'):
    """Carrega variáveis de ambiente de um arquivo"""
    env_path = Path(__file__).parent / env_file
    
    if not env_path.exists():
        print(f"❌ Arquivo {env_file} não encontrado")
        return False
    
    print(f"📄 Carregando configurações de {env_file}")
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
                print(f"✅ {key} = {value[:20]}..." if len(value) > 20 else f"✅ {key} = {value}")
    
    return True

if __name__ == "__main__":
    print("🚀 Inicializando MoCoVe Trading System...")
    
    # Carregar configurações
    if load_env_file():
        print("\n✅ Configurações carregadas com sucesso!")
        print("\n🔧 Configuração atual:")
        print(f"   • USE_TESTNET: {os.getenv('USE_TESTNET', 'true')}")
        print(f"   • DEFAULT_SYMBOL: {os.getenv('DEFAULT_SYMBOL', 'DOGEUSDT')}")
        print(f"   • INVESTMENT_AMOUNT: {os.getenv('INVESTMENT_AMOUNT', '25.0')}")
        
        # Verificar credenciais
        api_key = os.getenv('BINANCE_API_KEY', '')
        if api_key and len(api_key) > 10:
            print(f"   • Binance API Key: {api_key[:8]}...{api_key[-4:]}")
        else:
            print("   • ⚠️  Binance API Key não configurada")
    else:
        print("❌ Falha ao carregar configurações")
        sys.exit(1)
