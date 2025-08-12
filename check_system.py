#!/usr/bin/env python3
"""
Verificação Rápida - MoCoVe
Testa se o sistema está funcionando sem problemas de timeout
"""

import requests
import time

def check_system():
    print("🔍 Verificação Rápida do Sistema MoCoVe")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    tests = [
        ("🎨 Favicon", f"{base_url}/favicon.ico"),
        ("🌐 Frontend", f"{base_url}/"),
        ("📊 API Status", f"{base_url}/api/system/status"),
        ("📋 Watchlist", f"{base_url}/api/watchlist/summary"),
    ]
    
    results = []
    
    for name, url in tests:
        try:
            print(f"Testing {name}... ", end="")
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                print("✅ OK")
                results.append(True)
            else:
                print(f"❌ HTTP {response.status_code}")
                results.append(False)
                
        except requests.exceptions.Timeout:
            print("⏰ Timeout")
            results.append(False)
        except requests.exceptions.ConnectionError:
            print("🔌 Conexão recusada")
            results.append(False)
        except Exception as e:
            print(f"❌ Erro: {e}")
            results.append(False)
    
    # Resultado final
    success_count = sum(results)
    total_tests = len(results)
    
    print("\n" + "=" * 50)
    print(f"📊 Resultado: {success_count}/{total_tests} testes passaram")
    
    if success_count == total_tests:
        print("🎉 SISTEMA 100% FUNCIONAL!")
        print("✅ Favicon corrigido - sem mais erros 404!")
    elif success_count >= total_tests // 2:
        print("✅ Sistema majoritariamente funcional!")
    else:
        print("⚠️ Sistema com problemas - verifique o backend")
    
    return success_count == total_tests

if __name__ == "__main__":
    try:
        check_system()
    except KeyboardInterrupt:
        print("\n⏹️ Verificação interrompida")
    except Exception as e:
        print(f"\n❌ Erro na verificação: {e}")
