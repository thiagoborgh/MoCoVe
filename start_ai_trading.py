#!/usr/bin/env python3
"""
MoCoVe AI Trading System - Launcher
Inicializador completo do sistema de trading com IA
"""

import subprocess
import time
import os
import sys
import signal
import threading
from datetime import datetime

class TradingSystemLauncher:
    """Controlador principal do sistema de trading"""
    
    def __init__(self):
        self.backend_process = None
        self.agent_process = None
        self.monitor_process = None
        self.is_running = False
        
    def check_requirements(self):
        """Verifica se todos os requisitos estão instalados"""
        print("🔍 Verificando requisitos...")
        
        required_files = [
            "backend/app_real.py",
            "ai_trading_agent.py",
            "ai_agent_config.py",
            "ai_agent_monitor.py"
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print("❌ Arquivos obrigatórios não encontrados:")
            for file in missing_files:
                print(f"   - {file}")
            return False
        
        print("✅ Todos os arquivos necessários encontrados")
        return True
    
    def start_backend(self):
        """Inicia o backend"""
        print("🚀 Iniciando backend...")
        try:
            self.backend_process = subprocess.Popen(
                [sys.executable, "backend/app_real.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Aguarda o backend ficar disponível
            for attempt in range(30):
                try:
                    import requests
                    response = requests.get("http://localhost:5000/api/status", timeout=2)
                    if response.status_code == 200:
                        print("✅ Backend online")
                        return True
                except:
                    pass
                print(f"   Aguardando backend... ({attempt + 1}/30)")
                time.sleep(2)
            
            print("❌ Backend não ficou disponível")
            return False
            
        except Exception as e:
            print(f"❌ Erro ao iniciar backend: {e}")
            return False
    
    def show_menu(self):
        """Mostra menu principal"""
        print("\n🤖 MOCOVE AI TRADING SYSTEM")
        print("=" * 50)
        print("1. 🔧 Configurar Agente de IA")
        print("2. 🚀 Iniciar Sistema Completo")
        print("3. 📊 Apenas Monitor (se agente já estiver rodando)")
        print("4. 🛠️  Apenas Backend")
        print("5. ⚙️  Status do Sistema")
        print("6. 📋 Ver Logs do Agente")
        print("7. 🛑 Parar Tudo")
        print("8. ❌ Sair")
        print("=" * 50)
        
        return input("Escolha uma opção: ").strip()
    
    def configure_agent(self):
        """Executa configurador do agente"""
        print("🔧 Abrindo configurador...")
        try:
            subprocess.run([sys.executable, "ai_agent_config.py"], check=True)
        except Exception as e:
            print(f"❌ Erro ao abrir configurador: {e}")
    
    def start_full_system(self):
        """Inicia sistema completo"""
        print("\n🚀 INICIANDO SISTEMA COMPLETO")
        print("=" * 40)
        
        # 1. Verificar requisitos
        if not self.check_requirements():
            return False
        
        # 2. Iniciar backend
        if not self.start_backend():
            return False
        
        # 3. Mostrar aviso de segurança
        self.show_safety_warning()
        
        # 4. Confirmar início do agente
        confirm = input("\n🤖 Iniciar AI Trading Agent? (s/N): ").lower()
        if not confirm.startswith('s'):
            print("⏹️  Sistema iniciado apenas com backend")
            return True
        
        # 5. Iniciar agente de IA
        print("🤖 Iniciando AI Trading Agent...")
        try:
            self.agent_process = subprocess.Popen(
                [sys.executable, "ai_trading_agent.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            print("✅ AI Trading Agent iniciado")
            
            # 6. Opção de monitor
            monitor = input("📊 Abrir monitor em tempo real? (S/n): ").lower()
            if not monitor.startswith('n'):
                time.sleep(2)  # Aguarda agente inicializar
                self.start_monitor()
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar agente: {e}")
            return False
    
    def start_monitor(self):
        """Inicia apenas o monitor"""
        print("📊 Iniciando monitor...")
        try:
            subprocess.run([sys.executable, "ai_agent_monitor.py"])
        except Exception as e:
            print(f"❌ Erro ao iniciar monitor: {e}")
    
    def show_system_status(self):
        """Mostra status do sistema"""
        print("\n📊 STATUS DO SISTEMA")
        print("=" * 30)
        
        # Backend
        try:
            import requests
            response = requests.get("http://localhost:5000/api/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("🟢 Backend: ONLINE")
                print(f"   Exchange: {'Conectada' if data.get('exchange_connected') else 'Desconectada'}")
                print(f"   Símbolo: {data.get('default_symbol')}")
            else:
                print("🔴 Backend: OFFLINE")
        except:
            print("🔴 Backend: OFFLINE")
        
        # Processos
        print(f"\n🔧 Processos:")
        print(f"   Backend: {'🟢 Rodando' if self.backend_process and self.backend_process.poll() is None else '🔴 Parado'}")
        print(f"   AI Agent: {'🟢 Rodando' if self.agent_process and self.agent_process.poll() is None else '🔴 Parado'}")
        
        # Arquivos de log
        if os.path.exists("ai_trading_agent.log"):
            stat = os.stat("ai_trading_agent.log")
            mod_time = datetime.fromtimestamp(stat.st_mtime)
            print(f"   Log Agent: Atualizado {mod_time.strftime('%H:%M:%S')}")
        else:
            print(f"   Log Agent: Não encontrado")
    
    def show_agent_logs(self):
        """Mostra logs do agente"""
        log_file = "ai_trading_agent.log"
        if os.path.exists(log_file):
            print("\n📋 ÚLTIMAS 20 LINHAS DO LOG")
            print("=" * 50)
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-20:]:
                        print(line.strip())
            except Exception as e:
                print(f"❌ Erro ao ler log: {e}")
        else:
            print("📭 Arquivo de log não encontrado")
    
    def show_safety_warning(self):
        """Mostra avisos de segurança"""
        print("\n🚨 AVISOS DE SEGURANÇA IMPORTANTES")
        print("=" * 60)
        print("⚠️  VOCÊ ESTÁ PRESTES A INICIAR TRADING AUTOMATIZADO REAL")
        print("💰 O agente fará trades com SUA CONTA BINANCE REAL")
        print("📊 Certifique-se de que:")
        print("   1. ✅ Configurou limites apropriados")
        print("   2. ✅ Entende os riscos envolvidos")
        print("   3. ✅ Pode monitorar o sistema")
        print("   4. ✅ Sabe como parar o agente (Ctrl+C)")
        print("🛡️  Limites recomendados para início:")
        print("   💰 Máximo $25 por trade")
        print("   📈 Máximo 5 trades por dia")
        print("   🎯 Confiança mínima 0.8")
        print("=" * 60)
    
    def stop_all(self):
        """Para todos os processos"""
        print("🛑 Parando todos os processos...")
        
        processes = [
            (self.agent_process, "AI Agent"),
            (self.backend_process, "Backend")
        ]
        
        for process, name in processes:
            if process and process.poll() is None:
                print(f"   Parando {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                    print(f"   ✅ {name} parado")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"   🔴 {name} forçado a parar")
        
        print("✅ Todos os processos parados")
    
    def signal_handler(self, signum, frame):
        """Manipula sinais de interrupção"""
        print(f"\n🛑 Recebido sinal {signum}")
        self.stop_all()
        sys.exit(0)
    
    def run(self):
        """Loop principal"""
        # Configurar manipuladores de sinal
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🤖 MoCoVe AI Trading System Launcher")
        print("=" * 50)
        
        try:
            while True:
                choice = self.show_menu()
                
                if choice == "1":
                    self.configure_agent()
                    
                elif choice == "2":
                    self.start_full_system()
                    if self.agent_process:
                        # Manter sistema rodando
                        print("\n✅ Sistema rodando!")
                        print("🔄 Pressione qualquer tecla para voltar ao menu")
                        input()
                    
                elif choice == "3":
                    self.start_monitor()
                    
                elif choice == "4":
                    if self.start_backend():
                        print("✅ Backend rodando em http://localhost:5000")
                        print("🔄 Pressione qualquer tecla para voltar ao menu")
                        input()
                    
                elif choice == "5":
                    self.show_system_status()
                    input("\nPressione Enter para continuar...")
                    
                elif choice == "6":
                    self.show_agent_logs()
                    input("\nPressione Enter para continuar...")
                    
                elif choice == "7":
                    self.stop_all()
                    
                elif choice == "8":
                    self.stop_all()
                    print("👋 Até logo!")
                    break
                    
                else:
                    print("❌ Opção inválida")
                    
        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")
        except Exception as e:
            print(f"❌ Erro: {e}")
        finally:
            self.stop_all()

def main():
    """Função principal"""
    launcher = TradingSystemLauncher()
    launcher.run()

if __name__ == "__main__":
    main()
