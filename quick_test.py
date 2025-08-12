#!/usr/bin/env python3
"""
Teste Rápido - Verificar se o favicon foi corrigido
"""

import requests
import time

def test_favicon():
    """Testar favicon"""
    try:
        print("🧪 Testando favicon...")
        response = requests.get("http://localhost:5000/favicon.ico", timeout=5)
        
        if response.status_code == 200:
            print("✅ Favicon funcionando!")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   Content-Length: {response.headers.get('content-length')} bytes")
            return True
        else:
            print(f"❌ Favicon falhou: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Erro ao testar favicon: {e}")
        return False

def test_api():
    """Testar API básica"""
    try:
        print("🧪 Testando API principal...")
        response = requests.get("http://localhost:5000/api/system/status", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API funcionando!")
            if data.get('success'):
                status = data['status']
                print(f"   Backend: {'✅' if status['backend_running'] else '❌'}")
                print(f"   Watchlist: {'✅' if status['watchlist_loaded'] else '❌'}")
            return True
        else:
            print(f"❌ API falhou: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Erro ao testar API: {e}")
        return False

def test_frontend():
    """Testar frontend"""
    try:
        print("🧪 Testando frontend...")
        response = requests.get("http://localhost:5000/", timeout=5)
        
        if response.status_code == 200:
            print("✅ Frontend funcionando!")
            print(f"   Content-Length: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ Frontend falhou: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Erro ao testar frontend: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MoCoVe - Teste Rápido de Funcionamento")
    print("=" * 50)
    
    results = []
    
    # Aguardar servidor estar pronto
    print("⏳ Aguardando servidor...")
    time.sleep(2)
    
    # Testes
    results.append(("Favicon", test_favicon()))
    results.append(("API Principal", test_api()))
    results.append(("Frontend", test_frontend()))
    
    # Relatório
    print("\n" + "=" * 50)
    print("📊 RELATÓRIO FINAL:")
    
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"   {status} | {test_name}")
    
    success_count = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\n🎯 Resultado: {success_count}/{total_tests} testes passaram")
    
    if success_count == total_tests:
        print("🎉 SISTEMA 100% FUNCIONAL!")
        print("✅ Problema do favicon RESOLVIDO!")
    else:
        print("⚠️ Alguns problemas ainda existem")
