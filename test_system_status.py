#!/usr/bin/env python3
"""
Teste e Correção do Status do Sistema MoCoVe
Script para testar e corrigir problemas de status
"""

import subprocess
import time
import sys
import os

def test_and_fix_system():
    """Testar sistema e corrigir problemas"""
    print("🔧 TESTE E CORREÇÃO DO SISTEMA MOCOVE")
    print("=" * 50)
    
    # 1. Verificar se backend está rodando
    print("\n1. 📡 Verificando Backend...")
    try:
        import requests
        response = requests.get("http://localhost:5000/api/health", timeout=3)
        if response.status_code == 200:
            print("✅ Backend está rodando")
            backend_ok = True
        else:
            print(f"❌ Backend respondeu com status {response.status_code}")
            backend_ok = False
    except:
        print("❌ Backend não está respondendo")
        backend_ok = False
    
    # 2. Verificar AI Agent
    print("\n2. 🤖 Verificando AI Agent...")
    ai_agent_log = "ai_trading_agent.log"
    if os.path.exists(ai_agent_log):
        stat = os.stat(ai_agent_log)
        import time
        last_modified = time.time() - stat.st_mtime
        if last_modified < 120:  # 2 minutos
            print(f"✅ AI Agent ativo (log atualizado há {last_modified:.0f}s)")
            ai_ok = True
        else:
            print(f"⚠️ AI Agent pode estar inativo (log há {last_modified:.0f}s)")
            ai_ok = False
    else:
        print("❌ Log do AI Agent não encontrado")
        ai_ok = False
    
    # 3. Atualizar status na base
    print("\n3. 🔄 Atualizando status na base...")
    try:
        result = subprocess.run([sys.executable, "update_system_status.py", "--once"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Status atualizado na base")
        else:
            print(f"⚠️ Aviso ao atualizar status: {result.stderr}")
    except Exception as e:
        print(f"❌ Erro ao atualizar status: {e}")
    
    # 4. Testar API de status
    print("\n4. 🧪 Testando API de status...")
    try:
        import requests
        response = requests.get("http://localhost:5000/api/system/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', {})
            
            print("📊 Status atual:")
            print(f"   Backend: {'✅' if status.get('backend_running') else '❌'}")
            print(f"   AI Agent: {'✅' if status.get('ai_agent_active') else '❌'}")
            print(f"   Binance: {'✅' if status.get('binance_connected') else '❌'}")
            print(f"   Watchlist: {'✅' if status.get('watchlist_loaded') else '❌'}")
            
            warnings = status.get('warnings', [])
            if warnings:
                print(f"⚠️ Avisos: {', '.join(warnings)}")
            
        else:
            print(f"❌ API retornou status {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao testar API: {e}")
    
    # 5. Recomendações
    print("\n5. 💡 Recomendações:")
    
    if not backend_ok:
        print("   🔧 Inicie o backend: python backend/app_real.py")
    
    if not ai_ok:
        print("   🤖 Inicie o AI Agent: python ai_trading_agent.py")
    
    print("   📊 Para monitorar: python update_system_status.py")
    print("   🌐 Dashboard: http://localhost:5000")
    
    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    test_and_fix_system()
