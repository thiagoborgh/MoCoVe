#!/usr/bin/env python3
"""
Script para configurar e testar conexão com Binance Real
Execute este script antes de usar o MoCoVe com conta real
"""

import os
import sys
import ccxt
from dotenv import load_dotenv

def create_env_file():
    """Cria arquivo .env interativo"""
    print("🔐 Configuração da Conta Binance Real para MoCoVe")
    print("=" * 50)
    
    # Carregar .env existente se houver
    env_path = '.env'
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print("📄 Arquivo .env existente encontrado.")
        
    # Coletar credenciais
    print("\n🔑 Insira suas credenciais da Binance:")
    api_key = input("API Key: ").strip()
    api_secret = input("Secret Key: ").strip()
    
    # Confirmar uso de produção
    print("\n⚠️  ATENÇÃO: Você está configurando para PRODUÇÃO!")
    print("Isso usará dinheiro real da sua conta Binance.")
    confirm = input("Digite 'CONFIRMO' para continuar: ").strip()
    
    if confirm != 'CONFIRMO':
        print("❌ Configuração cancelada.")
        return False
    
    # Configurações de trading
    print("\n💰 Configurações de Trading:")
    default_amount = input("Quantidade padrão para trading (ex: 10.0): ").strip() or "10.0"
    default_symbol = input("Par padrão (ex: DOGEUSDT): ").strip() or "DOGEUSDT"
    volatility_threshold = input("Limite de volatilidade % (ex: 2.0): ").strip() or "2.0"
    
    # Criar conteúdo do .env
    env_content = f"""# MoCoVe Configuration - PRODUÇÃO
# ⚠️ NUNCA compartilhe este arquivo!
# Gerado automaticamente em {os.path.basename(__file__)}

# Database
DB_PATH=./memecoin.db

# 🔥 BINANCE API REAL (PRODUÇÃO)
BINANCE_API_KEY={api_key}
BINANCE_API_SECRET={api_secret}
USE_TESTNET=false

# AI Model
MODEL_PATH=./ai/memecoin_rf_model.pkl
AI_MODEL_URL=http://localhost:5000

# Server Configuration
PORT=5000
DEBUG=false

# 💰 Trading Parameters
DEFAULT_SYMBOL={default_symbol}
DEFAULT_AMOUNT={default_amount}
DEFAULT_VOLATILITY_THRESHOLD={float(volatility_threshold)/100}

# Data Collection
COLLECTION_INTERVAL=60
COINGECKO_API_KEY=

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/mocove.log

# Security
MAX_TRADE_AMOUNT=100.0
DAILY_LOSS_LIMIT=50.0
"""
    
    # Salvar arquivo
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ Arquivo .env criado em: {os.path.abspath(env_path)}")
    return True

def test_binance_connection():
    """Testa conexão com Binance"""
    print("\n🔍 Testando conexão com Binance...")
    
    # Recarregar variáveis
    load_dotenv('.env')
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    use_testnet = os.getenv('USE_TESTNET', 'false').lower() == 'true'
    
    if not api_key or not api_secret:
        print("❌ Credenciais não encontradas no .env")
        return False
    
    try:
        # Configurar exchange
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': use_testnet,
            'enableRateLimit': True,
        })
        
        # Testar conexão
        print("📡 Testando autenticação...")
        account = exchange.fetch_balance()
        
        print("✅ Conexão estabelecida com sucesso!")
        print(f"🏦 Modo: {'TESTNET' if use_testnet else 'PRODUÇÃO'}")
        
        # Mostrar saldos principais
        print("\n💰 Saldos principais:")
        main_assets = ['USDT', 'BUSD', 'BNB', 'DOGE', 'SHIB']
        for asset in main_assets:
            if asset in account['total'] and account['total'][asset] > 0:
                print(f"   {asset}: {account['total'][asset]:.6f}")
        
        # Testar mercados
        print("\n📊 Testando acesso aos mercados...")
        markets = exchange.load_markets()
        
        symbol = os.getenv('DEFAULT_SYMBOL', 'DOGEUSDT')
        if symbol in markets:
            ticker = exchange.fetch_ticker(symbol)
            print(f"✅ {symbol}: ${ticker['last']:.6f}")
        else:
            print(f"⚠️  Símbolo {symbol} não encontrado")
            
        return True
        
    except ccxt.AuthenticationError as e:
        print(f"❌ Erro de autenticação: {e}")
        print("🔧 Verifique suas chaves API na Binance")
        return False
        
    except ccxt.PermissionDenied as e:
        print(f"❌ Permissão negada: {e}")
        print("🔧 Verifique as permissões da sua API Key")
        return False
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def security_checklist():
    """Mostra checklist de segurança"""
    print("\n🛡️  CHECKLIST DE SEGURANÇA")
    print("=" * 30)
    print("✅ API Key criada com permissões mínimas")
    print("✅ Restrição de IP configurada")
    print("✅ Withdrawals DESABILITADOS na API")
    print("✅ Valores baixos para testes iniciais")
    print("✅ Monitoramento ativo das operações")
    print("✅ Backup das configurações")
    print("\n⚠️  LEMBRE-SE:")
    print("- Comece com valores pequenos")
    print("- Monitore constantemente")
    print("- Tenha um stop-loss definido")
    print("- NUNCA compartilhe suas chaves")

def main():
    """Função principal"""
    print("🚀 MoCoVe - Setup de Conta Binance Real")
    print("=====================================")
    
    # Verificar se está na pasta correta
    if not os.path.exists('backend') or not os.path.exists('frontend'):
        print("❌ Execute este script na pasta raiz do MoCoVe")
        sys.exit(1)
    
    # Criar diretório de logs
    os.makedirs('logs', exist_ok=True)
    
    # Menu
    while True:
        print("\n📋 Opções:")
        print("1. 🔧 Configurar credenciais Binance")
        print("2. 🔍 Testar conexão")
        print("3. 🛡️  Ver checklist de segurança")
        print("4. 📄 Ver arquivo .env atual")
        print("5. ❌ Sair")
        
        choice = input("\nEscolha uma opção (1-5): ").strip()
        
        if choice == '1':
            if create_env_file():
                print("\n🎯 Próximo passo: Teste a conexão (opção 2)")
                
        elif choice == '2':
            if os.path.exists('.env'):
                test_binance_connection()
            else:
                print("❌ Arquivo .env não encontrado. Configure primeiro (opção 1)")
                
        elif choice == '3':
            security_checklist()
            
        elif choice == '4':
            if os.path.exists('.env'):
                print("\n📄 Conteúdo atual do .env:")
                with open('.env', 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Ocultar credenciais sensíveis
                    lines = content.split('\n')
                    for line in lines:
                        if 'API_KEY=' in line or 'SECRET=' in line:
                            key, value = line.split('=', 1)
                            if value:
                                masked = value[:8] + '*' * (len(value) - 8)
                                print(f"{key}={masked}")
                            else:
                                print(line)
                        else:
                            print(line)
            else:
                print("❌ Arquivo .env não encontrado")
                
        elif choice == '5':
            print("👋 Até logo!")
            break
            
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main()
