#!/usr/bin/env python3
"""
Teste rápido dos endpoints para confirmar correção do erro 500
"""

import requests
import json

def test_endpoint(url, name):
    """Testa um endpoint específico"""
    try:
        response = requests.get(url, timeout=5)
        status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
        print(f"{name}: {status}")
        if response.status_code != 200:
            print(f"   Erro: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"{name}: ❌ ERRO - {e}")
        return False

def main():
    """Testa todos os endpoints principais"""
    print("🧪 TESTE DOS ENDPOINTS")
    print("=" * 40)
    
    base_url = "http://localhost:5000"
    
    endpoints = [
        (f"{base_url}/api/status", "Status da API"),
        (f"{base_url}/api/market_data?symbol=DOGEUSDT", "Dados de Mercado"),
        (f"{base_url}/api/volatility?symbol=DOGEUSDT", "Volatilidade (CORRIGIDO)"),
        (f"{base_url}/api/balance", "Saldos"),
        (f"{base_url}/api/trades", "Histórico de Trades"),
        (f"{base_url}/api/settings", "Configurações"),
        (f"{base_url}/api/prices?symbol=DOGEUSDT&limit=10", "Preços Históricos")
    ]
    
    results = []
    for url, name in endpoints:
        result = test_endpoint(url, name)
        results.append(result)
    
    print("\n📊 RESUMO")
    print("=" * 20)
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print("🎉 TODOS OS ENDPOINTS FUNCIONANDO!")
        print("✅ Erro HTTP 500 corrigido")
        print("🌐 Interface web deve estar funcionando normalmente")
    else:
        print(f"⚠️  {success_count}/{total_count} endpoints funcionando")
        print("🔧 Alguns endpoints ainda precisam de correção")

if __name__ == "__main__":
    main()
