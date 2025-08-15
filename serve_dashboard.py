#!/usr/bin/env python3
"""
Servidor HTTP simples para servir o dashboard MoCoVe
"""

import os
import http.server
import socketserver
import webbrowser
import time
from pathlib import Path

def start_dashboard_server():
    """Inicia servidor HTTP para o dashboard"""
    
    # Mudar para o diretório frontend
    frontend_dir = Path(__file__).parent / 'frontend'
    os.chdir(frontend_dir)
    
    PORT = 8000
    
    # Verificar se a porta está disponível
    try:
        with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
            print(f"🌐 Servidor do Dashboard iniciado em http://localhost:{PORT}")
            print(f"📁 Servindo arquivos de: {frontend_dir}")
            print("🚀 Abrindo dashboard no navegador...")
            
            # Aguardar um momento e abrir no navegador
            time.sleep(1)
            webbrowser.open(f"http://localhost:{PORT}/dashboard_pro.html")
            
            print("✅ Dashboard aberto! Pressione Ctrl+C para parar o servidor.")
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"⚠️  Porta {PORT} já está em uso!")
            print(f"🌐 Abrindo dashboard em: http://localhost:{PORT}/dashboard_pro.html")
            webbrowser.open(f"http://localhost:{PORT}/dashboard_pro.html")
        else:
            print(f"❌ Erro ao iniciar servidor: {e}")

if __name__ == "__main__":
    try:
        start_dashboard_server()
    except KeyboardInterrupt:
        print("\n👋 Servidor parado.")
