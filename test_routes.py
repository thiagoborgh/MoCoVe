#!/usr/bin/env python3
"""
Lista todas as rotas registradas no Flask
"""

import requests
import json

def test_route(url, method='GET'):
    """Testar uma rota específica"""
    try:
        if method.upper() == 'POST':
            response = requests.post(url, timeout=5)
        else:
            response = requests.get(url, timeout=5)
        
        print(f"✅ {method} {url} -> {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   📊 Response: {json.dumps(data, indent=2)[:200]}...")
            except:
                print(f"   📝 Text: {response.text[:100]}...")
        else:
            print(f"   ❌ Error: {response.text[:100]}")
            
    except Exception as e:
        print(f"❌ {method} {url} -> ERROR: {e}")

def main():
    """Testar rotas principais"""
    base_url = "http://localhost:5000"
    
    print("🔍 TESTANDO ROTAS DO BACKEND")
    print("=" * 50)
    
    # Rotas básicas
    routes_to_test = [
        ("/", "GET"),
        ("/api/status", "GET"),
        ("/api/system/status", "GET"),
        ("/api/system/activate/backend", "POST"),
        ("/api/system/activate/binance", "POST"),
        ("/api/system/activate/ai_agent", "POST"),
        ("/api/system/activate/watchlist", "POST"),
    ]
    
    for route, method in routes_to_test:
        test_route(f"{base_url}{route}", method)
        print()

if __name__ == "__main__":
    main()
