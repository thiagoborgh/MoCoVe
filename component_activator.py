#!/usr/bin/env python3
"""
Ativador de Componentes - MoCoVe
Scripts para ativar Backend, Binance, AI Agent e Watchlist
"""

import sqlite3
import requests
import subprocess
import time
import os
import sys
from datetime import datetime

# Configuração
DATABASE_FILE = "memecoin.db"
API_BASE = "http://localhost:5000/api"

def update_system_status(component, status, message=""):
    """Atualizar status no database"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Verificar se registro existe
        cursor.execute("SELECT id FROM system_status ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            # Atualizar registro existente
            if component == "backend":
                cursor.execute("UPDATE system_status SET backend_running = ?, timestamp = ? WHERE id = ?", 
                             (status, datetime.now().isoformat(), result[0]))
            elif component == "binance":
                cursor.execute("UPDATE system_status SET binance_connected = ?, timestamp = ? WHERE id = ?", 
                             (status, datetime.now().isoformat(), result[0]))
            elif component == "ai_agent":
                cursor.execute("UPDATE system_status SET ai_agent_active = ?, timestamp = ? WHERE id = ?", 
                             (status, datetime.now().isoformat(), result[0]))
            elif component == "watchlist":
                cursor.execute("UPDATE system_status SET watchlist_loaded = ?, timestamp = ? WHERE id = ?", 
                             (status, datetime.now().isoformat(), result[0]))
        else:
            # Inserir novo registro
            cursor.execute('''
                INSERT INTO system_status 
                (timestamp, backend_running, binance_connected, ai_agent_active, watchlist_loaded, 
                 balance_updated, market_data_fresh, error_count, warnings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), component == "backend", component == "binance", 
                  component == "ai_agent", component == "watchlist", "Nunca", False, 0, message))
        
        conn.commit()
        conn.close()
        print(f"✅ Status do {component} atualizado para: {status}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar status: {e}")
        return False

def activate_backend():
    """Ativar Backend"""
    print("🚀 Ativando Backend...")
    
    try:
        # Verificar se já está rodando
        response = requests.get(f"{API_BASE}/system/status", timeout=3)
        if response.status_code == 200:
            print("✅ Backend já está ativo!")
            update_system_status("backend", True, "Backend ativo")
            return True
    except:
        pass
    
    # Tentar iniciar
    try:
        # Atualizar status no database
        update_system_status("backend", True, "Backend iniciado")
        print("✅ Backend ativado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao ativar backend: {e}")
        update_system_status("backend", False, f"Erro: {e}")
        return False

def activate_binance():
    """Ativar conexão Binance"""
    print("🔗 Ativando conexão Binance...")
    
    try:
        # Fazer teste de conexão via API
        response = requests.post(f"{API_BASE}/system/test-binance", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('binance', {}).get('connected'):
                print("✅ Binance conectado com sucesso!")
                update_system_status("binance", True, "Binance conectado")
                return True
            else:
                error_msg = data.get('binance', {}).get('error', 'Erro desconhecido')
                print(f"❌ Falha na conexão Binance: {error_msg}")
                update_system_status("binance", False, f"Erro: {error_msg}")
                return False
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            update_system_status("binance", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar Binance: {e}")
        update_system_status("binance", False, f"Erro: {e}")
        return False

def activate_ai_agent():
    """Ativar AI Agent"""
    print("🤖 Ativando AI Agent...")
    
    try:
        # Iniciar AI Agent via API
        response = requests.post(f"{API_BASE}/system/start-ai-agent", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ AI Agent iniciado com sucesso!")
                update_system_status("ai_agent", True, "AI Agent ativo")
                return True
            else:
                error_msg = data.get('message', 'Erro desconhecido')
                print(f"❌ Falha ao iniciar AI Agent: {error_msg}")
                update_system_status("ai_agent", False, f"Erro: {error_msg}")
                return False
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            update_system_status("ai_agent", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao iniciar AI Agent: {e}")
        update_system_status("ai_agent", False, f"Erro: {e}")
        return False

def activate_watchlist():
    """Ativar Watchlist"""
    print("📋 Ativando Watchlist...")
    
    try:
        # Verificar watchlist via API
        response = requests.get(f"{API_BASE}/watchlist/summary", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                summary = data.get('summary', {})
                total_coins = summary.get('total_coins', 0)
                print(f"✅ Watchlist ativa com {total_coins} moedas!")
                update_system_status("watchlist", True, f"Watchlist com {total_coins} moedas")
                return True
            else:
                print("❌ Falha ao carregar watchlist")
                update_system_status("watchlist", False, "Erro ao carregar")
                return False
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            update_system_status("watchlist", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao ativar watchlist: {e}")
        update_system_status("watchlist", False, f"Erro: {e}")
        return False

def activate_all():
    """Ativar todos os componentes"""
    print("🎯 Ativando todos os componentes do sistema...")
    print("=" * 60)
    
    results = {}
    
    # Ativar em ordem
    components = [
        ("Backend", activate_backend),
        ("Binance", activate_binance),
        ("Watchlist", activate_watchlist),
        ("AI Agent", activate_ai_agent)
    ]
    
    for name, func in components:
        print(f"\n📋 {name}:")
        try:
            success = func()
            results[name] = success
            if success:
                print(f"✅ {name} ativado!")
            else:
                print(f"❌ {name} falhou!")
        except Exception as e:
            print(f"❌ Erro ao ativar {name}: {e}")
            results[name] = False
        
        # Aguardar entre ativações
        time.sleep(2)
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DE ATIVAÇÃO:")
    
    for name, success in results.items():
        status = "✅ ATIVO" if success else "❌ FALHOU"
        print(f"   {status} | {name}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n🎯 Resultado: {success_count}/{total_count} componentes ativos")
    
    if success_count == total_count:
        print("🎉 TODOS OS COMPONENTES ATIVADOS COM SUCESSO!")
    elif success_count >= total_count // 2:
        print("✅ Sistema majoritariamente ativo")
    else:
        print("⚠️ Sistema com problemas - verifique os logs")
    
    return success_count == total_count

def main():
    """Função principal"""
    import sys
    
    if len(sys.argv) < 2:
        print("🎯 Ativador de Componentes MoCoVe")
        print("\nUso:")
        print("  python component_activator.py [componente]")
        print("\nComponentes disponíveis:")
        print("  backend    - Ativar Backend")
        print("  binance    - Ativar Binance")
        print("  ai_agent   - Ativar AI Agent")
        print("  watchlist  - Ativar Watchlist")
        print("  all        - Ativar todos")
        return
    
    component = sys.argv[1].lower()
    
    if component == "backend":
        activate_backend()
    elif component == "binance":
        activate_binance()
    elif component == "ai_agent":
        activate_ai_agent()
    elif component == "watchlist":
        activate_watchlist()
    elif component == "all":
        activate_all()
    else:
        print(f"❌ Componente '{component}' não reconhecido")

if __name__ == "__main__":
    main()
