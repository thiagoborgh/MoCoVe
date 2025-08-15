#!/usr/bin/env python3
"""
Script para iniciar o MoCoVe Dashboard Pro
"""

import os
import sys
import time
import webbrowser
from pathlib import Path

def start_dashboard():
    """Inicia o dashboard e abre no navegador"""
    
    # Caminho para o dashboard
    frontend_dir = Path(__file__).parent / 'frontend'
    dashboard_file = frontend_dir / 'dashboard_pro.html'
    
    if not dashboard_file.exists():
        print("❌ Arquivo do dashboard não encontrado!")
        print(f"Procurado em: {dashboard_file}")
        return False
    
    print("🚀 Iniciando MoCoVe Dashboard Pro...")
    
    # Verificar se o backend está rodando
    try:
        import requests
        response = requests.get('http://localhost:5000/api/system/status', timeout=5)
        if response.status_code == 200:
            print("✅ Backend detectado em http://localhost:5000")
        else:
            print("⚠️  Backend não respondeu corretamente")
    except:
        print("⚠️  Backend não detectado em http://localhost:5000")
        print("💡 Certifique-se de que o backend está rodando:")
        print("   python backend/app.py")
    
    # Abrir dashboard no navegador
    dashboard_url = f"file:///{dashboard_file.absolute()}"
    print(f"🌐 Abrindo dashboard em: {dashboard_url}")
    
    try:
        webbrowser.open(dashboard_url)
        print("✅ Dashboard aberto no navegador!")
        print("\n" + "="*50)
        print("📊 MOCOVE DASHBOARD PRO")
        print("="*50)
        print("🖥️  Frontend: Dashboard aberto no navegador")
        print("🔗 Backend:  http://localhost:5000")
        print("🤖 AI Agent: Verifique status no dashboard")
        print("="*50)
        print("\n💡 Dicas:")
        print("- Use o botão 'Atualizar' para refresh manual")
        print("- Dashboard atualiza automaticamente a cada 15s")
        print("- Verifique logs da IA na seção 'Atividade Recente'")
        print("\n🔧 Para iniciar componentes:")
        print("- Backend: python backend/app.py")
        print("- AI Agent: python ai_trading_agent_robust.py")
        print("- Sistema completo: python start_complete_system.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao abrir navegador: {e}")
        print(f"🌐 Abra manualmente: {dashboard_url}")
        return False

if __name__ == "__main__":
    print("🚀 MoCoVe Dashboard Launcher")
    print("="*40)
    
    success = start_dashboard()
    
    if success:
        print("\n✅ Dashboard iniciado com sucesso!")
        print("Pressione Ctrl+C para sair")
        
        try:
            # Manter o script rodando
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Saindo...")
    else:
        print("\n❌ Falha ao iniciar dashboard")
        sys.exit(1)
