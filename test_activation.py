#!/usr/bin/env python3
"""
Teste dos botões de ativação de componentes
"""

import requests
import json

API_BASE = "http://localhost:5000/api"

def test_activation(component):
    """Testar ativação de componente"""
    print(f"\n🔥 Testando ativação do {component}...")
    
    try:
        response = requests.post(f"{API_BASE}/system/activate/{component}", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Resposta: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def test_system_status():
    """Testar status do sistema"""
    print("\n📊 Testando status do sistema...")
    
    try:
        response = requests.get(f"{API_BASE}/system/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def main():
    """Testar todos os componentes"""
    print("🎯 TESTE DOS BOTÕES DE ATIVAÇÃO")
    print("=" * 50)
    
    # Testar status inicial
    test_system_status()
    
    # Testar ativação de cada componente
    components = ["backend", "binance", "ai_agent", "watchlist"]
    
    for component in components:
        test_activation(component)
    
    # Testar status final
    print("\n" + "=" * 50)
    print("📊 STATUS FINAL:")
    test_system_status()

if __name__ == "__main__":
    main()
