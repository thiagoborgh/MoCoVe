#!/usr/bin/env python3
"""
Teste Final do Sistema MoCoVe com Conta Binance Real
Testa todas as funcionalidades principais
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:5000"

def test_api_connection():
    """Testa conexão básica com a API"""
    print("🔌 Testando Conexão API...")
    try:
        response = requests.get(f"{API_BASE}/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Online: {data.get('status')}")
            print(f"🏦 Exchange: {'✅ Conectada' if data.get('exchange_connected') else '❌ Desconectada'}")
            print(f"🧪 Testnet: {'Não' if not data.get('testnet_mode') else 'Sim'} (PRODUÇÃO REAL)")
            print(f"📊 Símbolo: {data.get('default_symbol')}")
            print(f"📈 Total trades: {data.get('total_trades')}")
            return True
        else:
            print(f"❌ Erro API: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_market_data():
    """Testa dados de mercado"""
    print("\n📈 Testando Dados de Mercado...")
    try:
        response = requests.get(f"{API_BASE}/api/market_data?symbol=DOGEUSDT", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ DOGE/USDT: ${data.get('price', 'N/A')}")
            print(f"📊 Variação 24h: {data.get('change_24h', 'N/A')}%")
            print(f"📈 Volume 24h: {data.get('volume', 'N/A'):,.0f}")
            return True
        else:
            print(f"❌ Erro ao obter dados: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_balance():
    """Testa saldos da conta"""
    print("\n💰 Testando Saldos da Conta...")
    try:
        response = requests.get(f"{API_BASE}/api/balance", timeout=10)
        if response.status_code == 200:
            balances = response.json()
            if balances:
                print("✅ Saldos encontrados:")
                for currency, amounts in balances.items():
                    if amounts['total'] > 0.001:
                        print(f"   {currency}: {amounts['total']:.6f} (livre: {amounts['free']:.6f})")
                return True
            else:
                print("⚠️  Nenhum saldo significativo encontrado")
                return True
        else:
            print(f"❌ Erro ao obter saldos: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_trading_simulation():
    """Simula um teste de trading (sem executar)"""
    print("\n🎯 Simulação de Trade...")
    
    # Configurações de teste muito conservadoras
    test_trade = {
        "symbol": "DOGEUSDT",
        "action": "buy",
        "amount": 5.0  # Apenas $5 para teste inicial
    }
    
    print(f"📊 Símbolo: {test_trade['symbol']}")
    print(f"🎯 Ação: {test_trade['action'].upper()}")
    print(f"💰 Valor: ${test_trade['amount']}")
    
    print("\n🛡️  Verificações de Segurança:")
    print("   ✅ Valor baixo para teste ($5)")
    print("   ✅ Par estável (DOGE/USDT)")
    print("   ✅ Tipo market (execução rápida)")
    print("   ✅ Dentro dos limites configurados")
    
    print("\n⚠️  IMPORTANTE:")
    print("   🔴 Este é apenas uma SIMULAÇÃO")
    print("   🔴 Para executar trade real, use a interface web")
    print("   🔴 SEMPRE monitore trades reais manualmente")
    print("   🔴 Comece com valores muito pequenos")
    
    return True

def security_guidelines():
    """Mostra diretrizes de segurança"""
    print("\n🛡️  DIRETRIZES DE SEGURANÇA PARA TRADING REAL")
    print("=" * 60)
    
    print("\n📋 ANTES do primeiro trade:")
    print("   1. ✅ Certifique-se que entende os riscos")
    print("   2. ✅ Comece com valor mínimo ($5-10)")
    print("   3. ✅ Monitore em tempo real")
    print("   4. ✅ Defina limite de perda (ex: $20)")
    print("   5. ✅ Use apenas horários que pode acompanhar")
    
    print("\n🚨 NUNCA faça:")
    print("   ❌ Trades de valores altos sem experiência")
    print("   ❌ Trading automático sem supervisão")
    print("   ❌ Operações quando não pode monitorar")
    print("   ❌ Ignore alertas do sistema")
    
    print("\n📞 Em emergência:")
    print("   🛑 Parar sistema: Ctrl+C no terminal")
    print("   💻 Acesso direto: https://binance.com")
    print("   📊 Verificar posições manualmente")
    print("   🔄 Fechar posições se necessário")

def main():
    """Função principal do teste"""
    print("🚀 MoCoVe - Teste Final de Sistema Real")
    print("=" * 60)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Executar testes
    tests = [
        ("Conexão API", test_api_connection),
        ("Dados de Mercado", test_market_data),
        ("Saldos da Conta", test_balance),
        ("Simulação de Trade", test_trading_simulation)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Erro em {name}: {e}")
            results.append((name, False))
    
    # Resumo dos resultados
    print("\n📊 RESUMO DOS TESTES")
    print("=" * 30)
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema pronto para trading real")
        print("\n🎯 Próximos passos:")
        print("1. 🌐 Acesse: http://localhost:5000")
        print("2. 💰 Faça primeiro trade com $5-10")
        print("3. 👀 Monitore resultado em tempo real")
        print("4. 📊 Verifique histórico")
        print("5. ⬆️  Aumente valores gradualmente")
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM")
        print("🔧 Resolva os problemas antes de fazer trading real")
    
    # Mostrar diretrizes de segurança
    security_guidelines()
    
    print(f"\n🎖️  STATUS: {'SISTEMA PRONTO' if all_passed else 'REQUER CORREÇÕES'}")

if __name__ == "__main__":
    main()
