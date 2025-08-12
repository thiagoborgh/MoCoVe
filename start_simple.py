#!/usr/bin/env python3
"""
Start Simple - Versão Simplificada
Inicia o sistema de forma mais direta
"""

import subprocess
import sys
import time
import os
from datetime import datetime

def print_header(title):
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def start_backend_simple():
    """Iniciar backend de forma simples"""
    print_header("INICIANDO SISTEMA MOCOVE")
    
    # Verificar se arquivos existem
    if not os.path.exists('backend/app_real.py'):
        print("❌ Arquivo backend/app_real.py não encontrado!")
        return False
    
    if not os.path.exists('memecoin.db'):
        print("⚠️ Database não encontrado - será criado automaticamente")
    
    print("🚀 Iniciando MoCoVe Backend...")
    print("🌐 URL: http://localhost:5000")
    print("🎨 Favicon: http://localhost:5000/favicon.ico")
    print("📱 Frontend: http://localhost:5000/")
    print("📊 API Status: http://localhost:5000/api/system/status")
    print("\n⏹️ Para parar: Ctrl+C")
    print("=" * 60)
    
    try:
        # Executar backend diretamente (foreground)
        subprocess.run([sys.executable, 'backend/app_real.py'], check=True)
        return True
    except KeyboardInterrupt:
        print("\n⏹️ Sistema parado pelo usuário")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar backend: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def main():
    """Função principal"""
    print(f"🎯 MoCoVe - Start Simplificado")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('server.js'):  # Arquivo marcador do projeto
        print("❌ Execute este script na pasta raiz do projeto MoCoVe!")
        return False
    
    success = start_backend_simple()
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        sys.exit(1)
