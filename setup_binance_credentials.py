#!/usr/bin/env python3
"""
Configurador de Credenciais Binance para MoCoVe
"""

import os
import json
import getpass
from pathlib import Path

def setup_binance_credentials():
    """Configura as credenciais da Binance de forma segura"""
    
    print("🔐 CONFIGURADOR DE CREDENCIAIS BINANCE")
    print("=" * 50)
    print("⚠️  IMPORTANTE: Suas credenciais serão salvas localmente")
    print("📍 Nunca compartilhe suas API keys!")
    print()
    
    # Caminhos
    project_root = Path(__file__).parent
    config_dir = project_root / 'config'
    config_file = config_dir / 'trading_config.json'
    env_file = project_root / '.env'
    
    # Criar diretório se não existir
    config_dir.mkdir(exist_ok=True)
    
    # Obter credenciais
    print("📝 Digite suas credenciais da Binance:")
    print("   (você pode obtê-las em: https://www.binance.com/pt/my/settings/api-management)")
    print()
    
    api_key = input("🔑 API Key: ").strip()
    if not api_key:
        print("❌ API Key é obrigatória!")
        return False
    
    api_secret = getpass.getpass("🔒 API Secret: ").strip()
    if not api_secret:
        print("❌ API Secret é obrigatória!")
        return False
    
    # Escolher modo inicial
    print("\n📊 Modo de Trading:")
    print("1. 🧪 Testnet (recomendado para testes)")
    print("2. 💰 Real (usar com cautela!)")
    
    while True:
        choice = input("\nEscolha (1 ou 2): ").strip()
        if choice == "1":
            use_testnet = True
            trading_mode = "testnet"
            break
        elif choice == "2":
            confirm = input("⚠️  Tem certeza que quer usar modo REAL? (digite 'SIM'): ")
            if confirm.upper() == "SIM":
                use_testnet = False
                trading_mode = "real"
                break
            else:
                print("Mantendo modo testnet por segurança.")
                use_testnet = True
                trading_mode = "testnet"
                break
        else:
            print("❌ Opção inválida!")
    
    # Salvar no arquivo de configuração
    try:
        # Carregar config existente ou criar novo
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Atualizar credenciais
        config.update({
            "binance_api_key": api_key,
            "binance_api_secret": api_secret,
            "use_testnet": use_testnet,
            "trading_mode": trading_mode,
            "credentials_configured": True,
            "last_updated": "2025-08-15T17:00:00.000000"
        })
        
        # Salvar configuração
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # Criar arquivo .env (alternativo)
        env_content = f"""# Credenciais Binance para MoCoVe
BINANCE_API_KEY={api_key}
BINANCE_API_SECRET={api_secret}
USE_TESTNET={'true' if use_testnet else 'false'}
"""
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("\n✅ Credenciais configuradas com sucesso!")
        print(f"📁 Salvo em: {config_file}")
        print(f"📁 Backup em: {env_file}")
        print(f"🎯 Modo: {trading_mode.upper()}")
        
        # Adicionar .env ao .gitignore se não estiver
        gitignore_file = project_root / '.gitignore'
        if gitignore_file.exists():
            with open(gitignore_file, 'r') as f:
                gitignore_content = f.read()
            
            if '.env' not in gitignore_content:
                with open(gitignore_file, 'a') as f:
                    f.write('\n# Arquivo de credenciais\n.env\n')
                print("🔒 Arquivo .env adicionado ao .gitignore")
        
        print("\n🚀 Agora você pode:")
        print("   1. Iniciar o backend: python backend/app_clean.py")
        print("   2. Usar o dashboard para alternar entre testnet/real")
        print("   3. Ativar o AI trading agent")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar credenciais: {e}")
        return False

def test_credentials():
    """Testa as credenciais configuradas"""
    try:
        import ccxt
        
        config_file = Path(__file__).parent / 'config' / 'trading_config.json'
        
        if not config_file.exists():
            print("❌ Configuração não encontrada. Execute setup_binance_credentials() primeiro.")
            return False
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        api_key = config.get('binance_api_key')
        api_secret = config.get('binance_api_secret')
        use_testnet = config.get('use_testnet', True)
        
        if not api_key or not api_secret:
            print("❌ Credenciais não configuradas.")
            return False
        
        print(f"🧪 Testando conexão... (Modo: {'Testnet' if use_testnet else 'Real'})")
        
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': use_testnet,
            'enableRateLimit': True,
        })
        
        # Testar conexão
        balance = exchange.fetch_balance()
        
        print("✅ Conexão bem-sucedida!")
        print(f"💰 Saldo USDT: {balance.get('USDT', {}).get('free', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def main():
    """Menu principal"""
    print("🚀 CONFIGURADOR BINANCE - MOCOVE")
    print("=" * 40)
    print("1. 🔐 Configurar Credenciais")
    print("2. 🧪 Testar Conexão")
    print("3. ❌ Sair")
    
    while True:
        try:
            choice = input("\n👉 Escolha uma opção (1-3): ").strip()
            
            if choice == '1':
                setup_binance_credentials()
                break
            elif choice == '2':
                test_credentials()
                break
            elif choice == '3':
                print("👋 Saindo...")
                break
            else:
                print("❌ Opção inválida!")
                
        except KeyboardInterrupt:
            print("\n👋 Saindo...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()
