"""
Teste Rápido da API MoCoVe
Script para verificar se todos os endpoints estão funcionando
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_endpoint(endpoint, method="GET", data=None):
    """Testa um endpoint da API"""
    try:
        url = f"{BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        print(f"✅ {method} {endpoint}: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   📊 Dados: {type(result)} com {len(result) if isinstance(result, (list, dict)) else 'N/A'} itens")
        else:
            print(f"   ❌ Erro: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ {method} {endpoint}: Erro - {str(e)}")
        return False

def main():
    print("🧪 Testando API do MoCoVe...\n")
    
    # Lista de endpoints para testar
    tests = [
        ("/status", "GET"),
        ("/trades", "GET"),
        ("/prices?symbol=DOGE/BUSD", "GET"),
        ("/volatility", "GET"),
        ("/settings", "GET"),
        ("/market_data?symbol=DOGE/BUSD", "GET"),
    ]
    
    passed = 0
    total = len(tests)
    
    for endpoint, method in tests:
        if test_endpoint(endpoint, method):
            passed += 1
        time.sleep(0.5)  # Pequena pausa entre requests
    
    print(f"\n📊 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os endpoints estão funcionando!")
    else:
        print("⚠️ Alguns endpoints têm problemas")
    
    # Teste adicional: simular um trade
    print("\n🔄 Testando execução de trade...")
    trade_data = {
        "type": "buy",
        "symbol": "DOGE/BUSD",
        "amount": 100
    }
    
    if test_endpoint("/execute_trade", "POST", trade_data):
        print("✅ Trade simulado executado com sucesso!")
    
    print("\n✅ Teste completo!")

if __name__ == "__main__":
    main()
