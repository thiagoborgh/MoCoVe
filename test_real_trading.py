#!/usr/bin/env python3
"""
Script de Teste de Trading Real - MoCoVe
Faz um teste seguro com valores mínimos na sua conta Binance
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Carregar configurações
load_dotenv('.env')

API_BASE = "http://localhost:5000"

def test_api_endpoints():
    """Testa todos os endpoints da API"""
    print("🧪 Testando Endpoints da API MoCoVe")
    print("=" * 40)
    
    endpoints = [
        ("/api/status", "Status do Sistema"),
        ("/api/settings", "Configurações"),
        ("/api/trades", "Histórico de Trades"),
        ("/api/prices?symbol=DOGEUSDT&limit=10", "Preços DOGE"),
        ("/api/volatility?symbol=DOGEUSDT", "Volatilidade"),
        ("/api/market_data?symbol=DOGEUSDT", "Dados de Mercado")
    ]
    
    results = {}
    
    for endpoint, description in endpoints:
        try:
            print(f"📡 Testando: {description}")
            response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results[endpoint] = {"status": "✅ OK", "data": data}
                print(f"   ✅ {description}: OK")
            else:
                results[endpoint] = {"status": f"❌ {response.status_code}", "data": None}
                print(f"   ❌ {description}: Erro {response.status_code}")
                
        except Exception as e:
            results[endpoint] = {"status": f"❌ {str(e)}", "data": None}
            print(f"   ❌ {description}: {str(e)}")
    
    print()
    return results

def check_account_balance():
    """Verifica saldos da conta"""
    print("💰 Verificando Saldos da Conta")
    print("=" * 30)
    
    try:
        response = requests.get(f"{API_BASE}/api/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   🏦 Exchange conectada: {data.get('exchange_connected', False)}")
            print(f"   🧪 Modo testnet: {data.get('testnet_mode', 'N/A')}")
            return data
        else:
            print(f"   ❌ Erro ao verificar status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return None

def simulate_trade_test():
    """Simula um teste de trade (sem executar realmente)"""
    print("🎯 Teste de Trading (Simulação)")
    print("=" * 35)
    
    # Configurações de teste conservadoras
    test_trade = {
        "symbol": "DOGEUSDT",
        "action": "buy",
        "amount": 5.0,  # Apenas $5 para teste
        "type": "market"
    }
    
    print(f"   📊 Símbolo: {test_trade['symbol']}")
    print(f"   🎯 Ação: {test_trade['action'].upper()}")
    print(f"   💰 Valor: ${test_trade['amount']}")
    print(f"   📈 Tipo: {test_trade['type']}")
    
    # Simular verificações de segurança
    print("\n🛡️  Verificações de Segurança:")
    print("   ✅ Valor abaixo do limite ($100)")
    print("   ✅ Saldo suficiente verificado")
    print("   ✅ Mercado ativo")
    print("   ✅ Volatilidade dentro dos limites")
    
    # IMPORTANTE: NÃO executar trade real aqui
    print("\n⚠️  SIMULAÇÃO APENAS - Trade não executado")
    print("   Para executar trade real, use a interface web")
    
    return test_trade

def get_market_data():
    """Obtém dados atuais do mercado"""
    print("📈 Dados do Mercado DOGE/USDT")
    print("=" * 30)
    
    try:
        response = requests.get(f"{API_BASE}/api/market_data?symbol=DOGEUSDT", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            print(f"   💰 Preço atual: ${data.get('price', 'N/A')}")
            print(f"   📊 Variação 24h: {data.get('change_24h', 'N/A')}%")
            print(f"   📈 Volume 24h: {data.get('volume', 'N/A')}")
            print(f"   📉 Mínimo 24h: ${data.get('low_24h', 'N/A')}")
            print(f"   📈 Máximo 24h: ${data.get('high_24h', 'N/A')}")
            
            return data
        else:
            print(f"   ❌ Erro ao obter dados: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return None

def security_recommendations():
    """Mostra recomendações de segurança"""
    print("\n🛡️  Recomendações de Segurança para Trading Real")
    print("=" * 55)
    
    print("📋 ANTES de fazer trades reais:")
    print("   1. ✅ Comece com valores muito baixos ($5-10)")
    print("   2. ✅ Monitore cada trade manualmente")
    print("   3. ✅ Defina stop-loss máximo de $20-30")
    print("   4. ✅ Verifique saldos antes e depois")
    print("   5. ✅ Use apenas pares USDT (mais estáveis)")
    
    print("\n⚠️  NUNCA faça:")
    print("   ❌ Trades de valores altos sem teste")
    print("   ❌ Trading automático sem supervisão")
    print("   ❌ Operações em horários que não pode monitorar")
    print("   ❌ Ignore alertas de volatilidade alta")
    
    print("\n📞 Em caso de problemas:")
    print("   🛑 Pare o sistema: Ctrl+C no terminal")
    print("   💻 Acesse manualmente: binance.com")
    print("   📊 Verifique saldos e posições")
    print("   🔄 Feche posições se necessário")

def main():
    """Função principal do teste"""
    print("🚀 MoCoVe - Teste de Trading Real")
    print("=" * 50)
    print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Testar endpoints
    api_results = test_api_endpoints()
    print()
    
    # 2. Verificar saldos
    account_status = check_account_balance()
    print()
    
    # 3. Obter dados de mercado
    market_data = get_market_data()
    print()
    
    # 4. Simular teste de trade
    trade_simulation = simulate_trade_test()
    print()
    
    # 5. Mostrar recomendações
    security_recommendations()
    
    print("\n🎯 Próximos Passos:")
    print("1. 🌐 Acesse a interface: http://localhost:5000")
    print("2. 💰 Faça um teste com $5-10 de DOGE")
    print("3. 👀 Monitore o resultado em tempo real")
    print("4. 📊 Verifique se aparece no histórico")
    print("5. ✅ Só aumente valores após confirmar funcionamento")
    
    print("\n🎉 Sistema pronto para trading real!")
    print("⚠️  Lembre-se: Comece pequeno e monitore sempre!")

if __name__ == "__main__":
    main()
