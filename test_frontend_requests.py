#!/usr/bin/env python3
"""
Teste específico que simula as requisições do frontend
"""

import requests
import json
import time

def test_frontend_requests():
    """Testa exatamente as requisições que o frontend faz"""
    print("🧪 TESTANDO REQUISIÇÕES DO FRONTEND")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Default symbol (para simular o frontend)
    symbol = "DOGE/BUSD"  # Símbolo que está sendo usado no frontend
    
    # Lista das requisições que o frontend faz em loadData()
    frontend_requests = [
        (f"{base_url}/api/trades", "Trades"),
        (f"{base_url}/api/prices?symbol={symbol}&limit=50", "Prices"),
        (f"{base_url}/api/volatility?symbol={symbol}", "Volatility"),
        (f"{base_url}/api/status", "Status"),
        (f"{base_url}/api/settings", "Settings"),
        (f"{base_url}/api/market_data?symbol={symbol}", "Market Data")
    ]
    
    results = []
    
    for url, name in frontend_requests:
        print(f"\n📡 Testando {name}...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ {response.status_code} - OK")
                data = response.json()
                # Mostrar um preview dos dados
                if isinstance(data, dict):
                    keys = list(data.keys())[:3]
                    print(f"   📄 Dados: {keys}...")
                elif isinstance(data, list):
                    print(f"   📄 {len(data)} itens")
                results.append(True)
            else:
                print(f"   ❌ {response.status_code} - {response.text[:100]}")
                results.append(False)
                
        except requests.exceptions.ConnectionError:
            print(f"   🔌 CONEXÃO RECUSADA - Backend não está rodando")
            results.append(False)
        except requests.exceptions.Timeout:
            print(f"   ⏰ TIMEOUT - Requisição demorou muito")
            results.append(False)
        except Exception as e:
            print(f"   ❌ ERRO: {e}")
            results.append(False)
    
    # Resumo
    print(f"\n📊 RESUMO FINAL")
    print("=" * 30)
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print("🎉 TODAS as requisições do frontend funcionaram!")
        print("✅ O erro 'Failed to fetch' não deveria aparecer")
    elif success_count == 0:
        print("🔴 NENHUMA requisição funcionou")
        print("💡 Backend provavelmente não está rodando")
        print("🔧 Execute: python start_mocove.py")
    else:
        print(f"⚠️  {success_count}/{total_count} requisições funcionaram")
        print("🔧 Algumas requisições estão falhando")
    
    return success_count == total_count

if __name__ == "__main__":
    test_frontend_requests()
