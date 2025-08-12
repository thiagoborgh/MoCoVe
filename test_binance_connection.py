#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de autenticação Binance
"""

import os
import ccxt
from dotenv import load_dotenv
import time

def test_binance_connection():
    """Testa conexão com Binance com diagnósticos detalhados"""
    
    print("🔍 Diagnóstico de Conexão Binance")
    print("=" * 40)
    
    # Carregar variáveis do .env
    load_dotenv('.env')
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    use_testnet = os.getenv('USE_TESTNET', 'false').lower() == 'true'
    
    print(f"📄 Arquivo .env carregado")
    print(f"🔑 API Key encontrada: {api_key[:8]}...{api_key[-4:] if api_key else 'NENHUMA'}")
    print(f"🔐 Secret encontrada: {api_secret[:8] if api_secret else 'NENHUMA'}...{api_secret[-4:] if api_secret else 'NENHUMA'}")
    print(f"🌐 Modo: {'TESTNET' if use_testnet else 'PRODUÇÃO'}")
    print()
    
    if not api_key or not api_secret:
        print("❌ Credenciais não encontradas no arquivo .env")
        return False
    
    # Verificar formato das chaves
    print("🔍 Verificando formato das chaves...")
    if len(api_key) != 64:
        print(f"⚠️  API Key tem {len(api_key)} caracteres (esperado: 64)")
    else:
        print("✅ API Key tem o tamanho correto (64 caracteres)")
    
    if len(api_secret) != 64:
        print(f"⚠️  Secret Key tem {len(api_secret)} caracteres (esperado: 64)")
    else:
        print("✅ Secret Key tem o tamanho correto (64 caracteres)")
    
    print()
    
    # Testar diferentes configurações
    configurations = [
        {"sandbox": False, "name": "PRODUÇÃO"},
        {"sandbox": True, "name": "TESTNET"}
    ]
    
    for config in configurations:
        print(f"🧪 Testando {config['name']}...")
        
        try:
            exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': config['sandbox'],
                'enableRateLimit': True,
                'timeout': 30000,
                'verbose': False  # Desabilitar logs verbosos
            })
            
            print(f"   📡 Testando conectividade...")
            
            # Teste básico de conectividade
            exchange.load_markets()
            print(f"   ✅ Mercados carregados com sucesso")
            
            # Teste de autenticação
            print(f"   🔐 Testando autenticação...")
            account = exchange.fetch_balance()
            
            print(f"   ✅ {config['name']}: Autenticação bem-sucedida!")
            
            # Mostrar saldos principais
            main_assets = ['USDT', 'BUSD', 'BNB', 'DOGE', 'SHIB']
            balances_found = False
            
            for asset in main_assets:
                if asset in account['total'] and account['total'][asset] > 0:
                    if not balances_found:
                        print(f"   💰 Saldos encontrados:")
                        balances_found = True
                    print(f"      {asset}: {account['total'][asset]:.6f}")
            
            if not balances_found:
                print(f"   📊 Nenhum saldo significativo encontrado")
            
            print()
            return True
            
        except ccxt.AuthenticationError as e:
            print(f"   ❌ {config['name']}: Erro de autenticação: {e}")
            
        except ccxt.NetworkError as e:
            print(f"   ❌ {config['name']}: Erro de rede: {e}")
            
        except ccxt.ExchangeError as e:
            print(f"   ❌ {config['name']}: Erro da exchange: {e}")
            
        except Exception as e:
            print(f"   ❌ {config['name']}: Erro geral: {e}")
        
        print()
    
    return False

def check_api_permissions():
    """Verifica as permissões configuradas na API"""
    print("🔍 Verificações Adicionais")
    print("=" * 30)
    
    print("📋 Checklist de configuração da API Binance:")
    print("   ✅ API Key criada na Binance?")
    print("   ✅ Permissão 'Enable Reading' habilitada?")
    print("   ✅ Permissão 'Enable Spot & Margin Trading' habilitada?")
    print("   ❌ Permissão 'Enable Withdrawals' DESABILITADA?")
    print("   ✅ Restrição de IP configurada (opcional)?")
    print("   ✅ API Key está ativa (não expirada)?")
    print()
    
    print("🕐 Possíveis causas do erro -2008:")
    print("   1. API Key incorreta ou mal copiada")
    print("   2. API Key foi criada recentemente (aguardar 1-2 minutos)")
    print("   3. API Key foi desabilitada na Binance")
    print("   4. API Key expirou")
    print("   5. Restrição de IP bloqueando o acesso")
    print("   6. Permissões insuficientes")
    print()

def test_connectivity():
    """Testa conectividade básica com Binance"""
    print("🌐 Testando conectividade básica...")
    
    try:
        # Teste sem autenticação
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'timeout': 30000
        })
        
        # Testar acesso público
        ticker = exchange.fetch_ticker('BTCUSDT')
        print(f"✅ Conectividade OK - BTC/USDT: ${ticker['last']:.2f}")
        return True
        
    except Exception as e:
        print(f"❌ Problema de conectividade: {e}")
        return False

def main():
    print("🚀 Diagnóstico Completo - Binance API")
    print("=" * 50)
    print()
    
    # 1. Teste de conectividade básica
    if not test_connectivity():
        print("❌ Problema de conectividade básica. Verifique sua internet.")
        return
    
    print()
    
    # 2. Teste de autenticação
    if not test_binance_connection():
        print()
        check_api_permissions()
        
        print("🔧 Soluções recomendadas:")
        print("1. Verifique se copiou as chaves corretamente")
        print("2. Aguarde 1-2 minutos após criar a API")
        print("3. Verifique se a API está ativa na Binance")
        print("4. Confirme as permissões da API")
        print("5. Verifique restrições de IP")
        
    else:
        print("🎉 Tudo funcionando perfeitamente!")
        print("Seu MoCoVe está pronto para trading real!")

if __name__ == "__main__":
    main()
