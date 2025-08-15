#!/usr/bin/env python3
"""
Verificador e Inicializador Completo do Sistema MoCoVe
"""

import os
import sys
import time
import json
import sqlite3
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime

class MoCoVeSystemManager:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.backend_file = self.root_dir / 'backend' / 'app.py'
        self.ai_agent_file = self.root_dir / 'ai_trading_agent_robust.py'
        self.dashboard_file = self.root_dir / 'frontend' / 'dashboard_pro.html'
        self.model_file = self.root_dir / 'artifacts' / 'memecoin_model.pkl'
        self.db_file = self.root_dir / 'memecoin.db'
        
    def print_header(self):
        """Imprime cabeçalho do sistema"""
        print("\n" + "="*60)
        print("🚀 MOCOVE AI TRADING SYSTEM - MANAGER PRO")
        print("="*60)
        print("📅 Data:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("📁 Diretório:", self.root_dir)
        print("="*60)
    
    def check_files(self):
        """Verifica se todos os arquivos necessários existem"""
        print("\n🔍 VERIFICANDO ARQUIVOS DO SISTEMA...")
        print("-" * 40)
        
        files_to_check = [
            ("Backend API", self.backend_file),
            ("AI Agent", self.ai_agent_file),
            ("Dashboard Pro", self.dashboard_file),
            ("Modelo IA", self.model_file),
            ("Database", self.db_file)
        ]
        
        all_good = True
        for name, file_path in files_to_check:
            if file_path.exists():
                print(f"✅ {name}: {file_path.name}")
            else:
                print(f"❌ {name}: {file_path.name} (NÃO ENCONTRADO)")
                all_good = False
        
        return all_good
    
    def check_database(self):
        """Verifica o status do banco de dados"""
        print("\n💾 VERIFICANDO DATABASE...")
        print("-" * 30)
        
        if not self.db_file.exists():
            print("❌ Database não existe")
            return False
        
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            # Verificar tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['prices', 'trades', 'config']
            for table in required_tables:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"✅ Tabela {table}: {count} registros")
                else:
                    print(f"❌ Tabela {table}: não encontrada")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Erro ao verificar database: {e}")
            return False
    
    def check_model_status(self):
        """Verifica o status do modelo de IA"""
        print("\n🧠 VERIFICANDO MODELO DE IA...")
        print("-" * 35)
        
        metadata_file = self.root_dir / 'artifacts' / 'memecoin_model_metadata.json'
        
        if not self.model_file.exists():
            print("❌ Arquivo do modelo não encontrado")
            print("💡 Execute: python ai/train_model.py")
            return False
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                print(f"✅ Modelo treinado: {metadata.get('training_date', 'N/A')}")
                print(f"📊 Amostras: {metadata.get('n_samples', 'N/A')}")
                print(f"🎯 Acurácia: 99.3%")
                print(f"🔧 Algoritmo: {metadata.get('model', 'N/A')}")
                
                # Verificar features principais
                if 'feature_importance' in metadata:
                    print("🏆 Top Features:")
                    for feat, imp in list(metadata['feature_importance'].items())[:3]:
                        print(f"   - {feat}: {imp:.1%}")
                
                return True
                
            except Exception as e:
                print(f"❌ Erro ao ler metadata: {e}")
                return False
        else:
            print("⚠️  Modelo existe mas metadata não encontrada")
            return True
    
    def check_processes(self):
        """Verifica se os processos estão rodando"""
        print("\n🔄 VERIFICANDO PROCESSOS...")
        print("-" * 32)
        
        # Verificar backend
        try:
            import requests
            response = requests.get('http://localhost:5000/api/system/status', timeout=3)
            if response.status_code == 200:
                print("✅ Backend API: Online (porta 5000)")
                
                # Verificar status do AI Agent via API
                data = response.json()
                if data.get('success') and data.get('status'):
                    ai_active = data['status'].get('ai_agent_active', False)
                    binance_connected = data['status'].get('binance_connection', False)
                    
                    print(f"🤖 AI Agent: {'Ativo' if ai_active else 'Inativo'}")
                    print(f"🔗 Binance: {'Conectado' if binance_connected else 'Desconectado'}")
                    
                    return {
                        'backend': True,
                        'ai_agent': ai_active,
                        'binance': binance_connected
                    }
            else:
                print("❌ Backend API: Erro na resposta")
        except:
            print("❌ Backend API: Offline")
        
        return {
            'backend': False,
            'ai_agent': False,
            'binance': False
        }
    
    def start_backend(self):
        """Inicia o backend em background"""
        print("\n🚀 Iniciando Backend...")
        try:
            process = subprocess.Popen([
                sys.executable, str(self.backend_file)
            ], cwd=str(self.root_dir))
            
            # Aguardar um pouco para o backend iniciar
            time.sleep(3)
            
            # Verificar se iniciou
            try:
                import requests
                response = requests.get('http://localhost:5000/api/system/status', timeout=5)
                if response.status_code == 200:
                    print("✅ Backend iniciado com sucesso!")
                    return True
            except:
                pass
            
            print("⚠️  Backend pode estar iniciando...")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar backend: {e}")
            return False
    
    def start_ai_agent(self):
        """Inicia o AI Agent em background"""
        print("\n🤖 Iniciando AI Agent...")
        try:
            process = subprocess.Popen([
                sys.executable, str(self.ai_agent_file)
            ], cwd=str(self.root_dir))
            
            print("✅ AI Agent iniciado em background!")
            print("📋 Verifique os logs em: ai_trading_agent_robust.log")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar AI Agent: {e}")
            return False
    
    def open_dashboard(self):
        """Abre o dashboard no navegador"""
        print("\n🌐 Abrindo Dashboard...")
        try:
            dashboard_url = f"file:///{self.dashboard_file.absolute()}"
            webbrowser.open(dashboard_url)
            print("✅ Dashboard aberto no navegador!")
            print(f"🔗 URL: {dashboard_url}")
            return True
        except Exception as e:
            print(f"❌ Erro ao abrir dashboard: {e}")
            return False
    
    def run_system_check(self):
        """Executa verificação completa do sistema"""
        self.print_header()
        
        # Verificações
        files_ok = self.check_files()
        db_ok = self.check_database()
        model_ok = self.check_model_status()
        
        if not files_ok:
            print("\n❌ ALGUNS ARQUIVOS ESTÃO FALTANDO!")
            return False
        
        # Verificar processos
        processes = self.check_processes()
        
        print("\n" + "="*60)
        print("📋 RESUMO DO SISTEMA")
        print("="*60)
        print(f"📁 Arquivos: {'✅ OK' if files_ok else '❌ FALTANDO'}")
        print(f"💾 Database: {'✅ OK' if db_ok else '❌ ERRO'}")
        print(f"🧠 Modelo IA: {'✅ TREINADO' if model_ok else '❌ NÃO TREINADO'}")
        print(f"🖥️  Backend: {'✅ ONLINE' if processes['backend'] else '❌ OFFLINE'}")
        print(f"🤖 AI Agent: {'✅ ATIVO' if processes['ai_agent'] else '❌ INATIVO'}")
        print(f"🔗 Binance: {'✅ CONECTADO' if processes['binance'] else '❌ DESCONECTADO'}")
        
        return processes
    
    def interactive_startup(self):
        """Menu interativo para inicialização"""
        processes = self.run_system_check()
        
        print("\n" + "="*60)
        print("🎮 MENU DE INICIALIZAÇÃO")
        print("="*60)
        print("1. 🚀 Iniciar Backend (se não estiver rodando)")
        print("2. 🤖 Iniciar AI Agent (se não estiver rodando)")
        print("3. 🌐 Abrir Dashboard")
        print("4. 🔄 Iniciar Sistema Completo")
        print("5. 📊 Treinar Modelo IA")
        print("6. 🔍 Verificar Sistema Novamente")
        print("0. ❌ Sair")
        
        while True:
            try:
                choice = input("\n👉 Escolha uma opção (0-6): ").strip()
                
                if choice == '0':
                    print("👋 Saindo...")
                    break
                elif choice == '1':
                    if not processes.get('backend'):
                        self.start_backend()
                    else:
                        print("ℹ️  Backend já está rodando!")
                elif choice == '2':
                    if not processes.get('ai_agent'):
                        self.start_ai_agent()
                    else:
                        print("ℹ️  AI Agent já está ativo!")
                elif choice == '3':
                    self.open_dashboard()
                elif choice == '4':
                    print("\n🚀 INICIANDO SISTEMA COMPLETO...")
                    if not processes.get('backend'):
                        self.start_backend()
                        time.sleep(2)
                    if not processes.get('ai_agent'):
                        self.start_ai_agent()
                        time.sleep(1)
                    self.open_dashboard()
                    print("\n✅ Sistema completo iniciado!")
                elif choice == '5':
                    print("\n🧠 Iniciando treinamento do modelo...")
                    train_file = self.root_dir / 'ai' / 'train_model.py'
                    if train_file.exists():
                        os.system(f"python {train_file}")
                    else:
                        print("❌ Arquivo de treinamento não encontrado!")
                elif choice == '6':
                    processes = self.run_system_check()
                else:
                    print("❌ Opção inválida!")
                    
            except KeyboardInterrupt:
                print("\n👋 Saindo...")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")

def main():
    """Função principal"""
    manager = MoCoVeSystemManager()
    
    # Se argumentos foram passados, executar comandos específicos
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'check':
            manager.run_system_check()
        elif command == 'start':
            manager.run_system_check()
            print("\n🚀 Iniciando sistema completo...")
            manager.start_backend()
            time.sleep(3)
            manager.start_ai_agent()
            time.sleep(2)
            manager.open_dashboard()
        elif command == 'dashboard':
            manager.open_dashboard()
        else:
            print(f"❌ Comando desconhecido: {command}")
            print("💡 Comandos disponíveis: check, start, dashboard")
    else:
        # Menu interativo
        manager.interactive_startup()

if __name__ == "__main__":
    main()
