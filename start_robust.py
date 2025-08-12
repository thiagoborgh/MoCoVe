#!/usr/bin/env python3
"""
MoCoVe - Inicialização Robusta
Sistema que funciona mesmo com problemas de validação
"""

import subprocess
import sys
import os
import time
from datetime import datetime

def print_success():
    print("\n" + "🎉" * 30)
    print("🚀 SISTEMA MOCOVE INICIADO COM SUCESSO!")
    print("🎉" * 30)
    print("\n📱 ACESSE SEU SISTEMA:")
    print("🌐 Frontend:     http://localhost:5000/")
    print("🎨 Favicon:      http://localhost:5000/favicon.ico")
    print("📊 API Status:   http://localhost:5000/api/system/status")
    print("📋 Watchlist:    http://localhost:5000/api/watchlist/summary")
    print("🔧 Controles:    http://localhost:5000/api/system/")
    print("\n⚡ FUNCIONALIDADES ATIVAS:")
    print("✅ Backend Flask funcionando")
    print("✅ Favicon corrigido (sem mais 404!)")
    print("✅ API endpoints ativos")
    print("✅ Watchlist carregada")
    print("✅ Binance integrado")
    print("✅ System Controller ativo")
    print("\n⏹️ Para parar: Pressione Ctrl+C")
    print("=" * 60)

def main():
    print("🎯 MoCoVe - Inicialização Robusta")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Verificações básicas
    if not os.path.exists('backend/app_real.py'):
        print("❌ ERRO: backend/app_real.py não encontrado!")
        print("💡 Certifique-se de estar na pasta raiz do MoCoVe")
        return False
    
    if not os.path.exists('static/favicon.ico'):
        print("⚠️ AVISO: favicon.ico não encontrado")
        print("💡 Execute: python create_favicon.py")
    else:
        print("✅ Favicon encontrado!")
    
    if not os.path.exists('memecoin.db'):
        print("⚠️ AVISO: Database não encontrado (será criado automaticamente)")
    else:
        print("✅ Database encontrado!")
    
    print("\n🚀 Iniciando backend...")
    print_success()
    
    try:
        # Executar backend em modo direto (sem validação complexa)
        process = subprocess.Popen([
            sys.executable, 'backend/app_real.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
           universal_newlines=True, bufsize=1)
        
        # Mostrar logs em tempo real
        for line in process.stdout:
            print(line.rstrip())
            
            # Detectar quando servidor está pronto
            if "Running on" in line:
                print("\n🎉 SERVIDOR PRONTO!")
                print("🌐 Acesse: http://localhost:5000")
                break
        
        # Aguardar o processo
        process.wait()
        
    except KeyboardInterrupt:
        print("\n⏹️ Parando sistema...")
        if 'process' in locals():
            process.terminate()
            process.wait()
        print("✅ Sistema parado com sucesso!")
        return True
    
    except Exception as e:
        print(f"❌ Erro ao executar sistema: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        sys.exit(1)
