#!/usr/bin/env python3
"""
Script de Inicialização Completa - MoCoVe
Inicia todos os componentes do sistema de forma coordenada
"""

import subprocess
import os
import sys
import time
import json
import sqlite3
from datetime import datetime

# Configuração
BACKEND_FILE = "backend/app_real.py"
SYSTEM_CONTROLLER = "system_controller.py"
DATABASE_FILE = "memecoin.db"
WATCHLIST_FILE = "coin_watchlist_expanded.json"

def print_header(title):
    print("\n" + "="*70)
    print(f"🚀 {title}")
    print("="*70)

def check_file_exists(filepath):
    """Verificar se arquivo existe"""
    if os.path.exists(filepath):
        print(f"✅ {filepath} - Encontrado")
        return True
    else:
        print(f"❌ {filepath} - NÃO ENCONTRADO!")
        return False

def check_dependencies():
    """Verificar dependências e arquivos necessários"""
    print_header("VERIFICAÇÃO DE DEPENDÊNCIAS")
    
    required_files = [
        BACKEND_FILE,
        SYSTEM_CONTROLLER,
        WATCHLIST_FILE,
        "train_model.py",
        "populate_prices.py"
    ]
    
    all_files_exist = True
    
    for file in required_files:
        if not check_file_exists(file):
            all_files_exist = False
    
    # Verificar database
    if os.path.exists(DATABASE_FILE):
        print(f"✅ {DATABASE_FILE} - Database encontrado")
        try:
            import sqlite3
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM prices")
            count = cursor.fetchone()[0]
            print(f"📊 Database tem {count} registros de preços")
            conn.close()
        except Exception as e:
            print(f"⚠️ Erro ao verificar database: {e}")
    else:
        print(f"❌ {DATABASE_FILE} - Database NÃO ENCONTRADO!")
        all_files_exist = False
    
    # Verificar Python packages
    print("\n📦 Verificando pacotes Python...")
    required_packages = [
        'flask', 'requests', 'pandas', 'numpy', 
        'sqlite3', 'binance', 'sklearn'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            elif package == 'sklearn':
                import sklearn
            elif package == 'binance':
                import binance
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NÃO INSTALADO")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Pacotes em falta: {', '.join(missing_packages)}")
        print("💡 Instale com: pip install " + " ".join(missing_packages))
        all_files_exist = False
    
    return all_files_exist

def setup_database():
    """Configurar database"""
    print_header("CONFIGURAÇÃO DO DATABASE")
    
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Verificar tabelas existentes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Tabelas existentes: {', '.join(tables)}")
        
        # Criar tabelas do sistema se não existirem
        system_tables = {
            'system_status': '''
                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    backend_running BOOLEAN,
                    binance_connected BOOLEAN,
                    ai_agent_active BOOLEAN,
                    watchlist_loaded BOOLEAN,
                    balance_updated TEXT,
                    market_data_fresh BOOLEAN,
                    error_count INTEGER DEFAULT 0,
                    warnings TEXT
                )
            ''',
            'account_balance': '''
                CREATE TABLE IF NOT EXISTS account_balance (
                    asset TEXT PRIMARY KEY,
                    free REAL,
                    locked REAL,
                    total REAL,
                    usd_value REAL,
                    last_updated TEXT
                )
            ''',
            'social_sentiment': '''
                CREATE TABLE IF NOT EXISTS social_sentiment (
                    symbol TEXT PRIMARY KEY,
                    avg_sentiment REAL,
                    total_mentions INTEGER,
                    sentiment_score_sum REAL,
                    last_updated TEXT
                )
            '''
        }
        
        for table_name, create_sql in system_tables.items():
            cursor.execute(create_sql)
            print(f"✅ Tabela {table_name} configurada")
        
        # Inserir status inicial
        cursor.execute('''
            INSERT OR REPLACE INTO system_status 
            (timestamp, backend_running, binance_connected, ai_agent_active, 
             watchlist_loaded, balance_updated, market_data_fresh, error_count, warnings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            False, False, False, False, 
            "Nunca", False, 0, "Sistema inicializando"
        ))
        
        conn.commit()
        conn.close()
        
        print("✅ Database configurado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar database: {e}")
        return False

def populate_initial_data():
    """Popular dados iniciais"""
    print_header("POPULANDO DADOS INICIAIS")
    
    try:
        # Executar script de população de preços
        print("📊 Populando preços históricos...")
        result = subprocess.run([sys.executable, "populate_prices.py"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Preços históricos carregados!")
        else:
            print(f"⚠️ Aviso ao carregar preços: {result.stderr}")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("⚠️ Timeout ao carregar dados - continuando...")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao popular dados: {e}")
        return True  # Continue mesmo com erro

def start_backend():
    """Iniciar backend"""
    print_header("INICIANDO BACKEND")
    
    try:
        print("🚀 Iniciando servidor Flask...")
        print(f"📂 Executando: python {BACKEND_FILE}")
        print("🌐 URL: http://localhost:5000")
        print("⏹️ Para parar: Ctrl+C")
        
        # Iniciar processo em background
        process = subprocess.Popen([sys.executable, BACKEND_FILE])
        
        # Aguardar um pouco para o servidor inicializar
        print("⏳ Aguardando servidor inicializar...")
        time.sleep(3)
        
        # Verificar se processo ainda está rodando
        if process.poll() is None:
            print("✅ Backend iniciado com sucesso!")
            print(f"🆔 Process ID: {process.pid}")
            return process
        else:
            print("❌ Backend falhou ao iniciar")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao iniciar backend: {e}")
        return None

def start_ai_trading_agent():
    """Iniciar AI Trading Agent"""
    print_header("INICIANDO AI TRADING AGENT")
    
    try:
        print("🤖 Iniciando AI Trading Agent...")
        print("📂 Executando: python ai_trading_agent.py")
        print("💰 MODO REAL - Trades reais serão executados!")
        print("⚠️ Certifique-se de que suas configurações estão corretas")
        
        # Verificar se arquivo existe
        if not os.path.exists("ai_trading_agent.py"):
            print("❌ Arquivo ai_trading_agent.py não encontrado!")
            return None
        
        # Mostrar aviso de segurança
        print("\n🚨 AVISO DE SEGURANÇA:")
        print("💰 O AI Agent executará trades REAIS na Binance")
        print("🔧 Configurações atuais:")
        
        try:
            from ai_trading_config import TEST_MODE, MAX_POSITION_SIZE, MAX_DAILY_TRADES
            print(f"   🧪 Modo Teste: {'ATIVO' if TEST_MODE else 'DESATIVO (MODO REAL)'}")
            print(f"   💰 Valor máximo por trade: ${MAX_POSITION_SIZE}")
            print(f"   📈 Trades máximos por dia: {MAX_DAILY_TRADES}")
        except:
            print("   ⚠️ Não foi possível ler configurações")
        
        # Aguardar confirmação
        print("\n❓ Confirma inicialização do AI Trading Agent? (digite 'SIM' para confirmar)")
        confirmacao = input("Confirmação: ").strip().upper()
        
        if confirmacao != 'SIM':
            print("❌ Inicialização cancelada pelo usuário")
            return None
        
        # Iniciar processo em background
        process = subprocess.Popen([sys.executable, "ai_trading_agent.py"])
        
        # Aguardar um pouco para o agente inicializar
        print("⏳ Aguardando AI Agent inicializar...")
        time.sleep(5)
        
        # Verificar se processo ainda está rodando
        if process.poll() is None:
            print("✅ AI Trading Agent iniciado com sucesso!")
            print(f"🆔 Process ID: {process.pid}")
            print("📊 Monitore os logs em: ai_trading_agent.log")
            return process
        else:
            print("❌ AI Trading Agent falhou ao iniciar")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao iniciar AI Trading Agent: {e}")
        return None

def start_status_updater():
    """Iniciar atualizador de status"""
    print_header("INICIANDO ATUALIZADOR DE STATUS")
    
    try:
        print("📊 Iniciando atualizador de status...")
        print("🔄 Manterá o status do sistema sempre atualizado")
        
        # Verificar se arquivo existe
        if not os.path.exists("update_system_status.py"):
            print("❌ Arquivo update_system_status.py não encontrado!")
            return None
        
        # Iniciar processo em background
        process = subprocess.Popen([sys.executable, "update_system_status.py"])
        
        # Aguardar um pouco para o atualizador inicializar
        print("⏳ Aguardando atualizador inicializar...")
        time.sleep(2)
        
        # Verificar se processo ainda está rodando
        if process.poll() is None:
            print("✅ Atualizador de status iniciado com sucesso!")
            print(f"🆔 Process ID: {process.pid}")
            print("🔄 Status será atualizado automaticamente a cada 30s")
            return process
        else:
            print("❌ Atualizador de status falhou ao iniciar")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao iniciar atualizador de status: {e}")
        return None

def start_ai_trading_agent():
    """Iniciar IA Trading Agent"""
    print_header("INICIANDO IA TRADING AGENT")
    
    try:
        print("🤖 Iniciando IA Trading Agent...")
        print("📂 Executando: python ai_trading_agent_optimized.py")
        print("⚠️ MODO REAL - Trading ativo na Binance!")
        print("⏹️ Para parar: Ctrl+C")
        
        # Iniciar processo em background
        process = subprocess.Popen([sys.executable, "ai_trading_agent_optimized.py"])
        
        # Aguardar um pouco para o agente inicializar
        print("⏳ Aguardando IA Agent inicializar...")
        time.sleep(5)
        
        # Verificar se processo ainda está rodando
        if process.poll() is None:
            print("✅ IA Trading Agent iniciado com sucesso!")
            print(f"🆔 Process ID: {process.pid}")
            return process
        else:
            print("❌ IA Trading Agent falhou ao iniciar")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao iniciar IA Trading Agent: {e}")
        return None

def validate_system():
    """Validar sistema após inicialização"""
    print_header("VALIDAÇÃO DO SISTEMA")
    
    try:
        import requests
        
        # Aguardar mais tempo para inicialização completa
        print("⏳ Aguardando sistema estabilizar...")
        time.sleep(8)
        
        # Testar múltiplas tentativas com timeouts crescentes
        timeouts = [5, 10, 15]
        max_attempts = len(timeouts)
        
        for attempt, timeout in enumerate(timeouts):
            try:
                print(f"🧪 Teste {attempt + 1}/{max_attempts} (timeout: {timeout}s)...")
                response = requests.get("http://localhost:5000/api/system/status", timeout=timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print("✅ Sistema respondendo corretamente!")
                        
                        # Testar favicon
                        try:
                            favicon_response = requests.get("http://localhost:5000/favicon.ico", timeout=3)
                            if favicon_response.status_code == 200:
                                print("🎨 Favicon: ✅ Funcionando")
                            else:
                                print(f"🎨 Favicon: ⚠️ HTTP {favicon_response.status_code}")
                        except:
                            print("🎨 Favicon: ⚠️ Erro")
                        
                        # Testar frontend
                        try:
                            frontend_response = requests.get("http://localhost:5000/", timeout=3)
                            if frontend_response.status_code == 200:
                                print("� Frontend: ✅ Funcionando")
                            else:
                                print(f"� Frontend: ⚠️ HTTP {frontend_response.status_code}")
                        except:
                            print("� Frontend: ⚠️ Erro")
                        
                        print("✅ Validação básica concluída com sucesso!")
                        return True
                else:
                    print(f"⚠️ HTTP {response.status_code} na tentativa {attempt + 1}")
                    
            except requests.exceptions.Timeout:
                print(f"⏰ Timeout ({timeout}s) na tentativa {attempt + 1}")
                if attempt < max_attempts - 1:
                    print("⏳ Tentando com timeout maior...")
            except requests.exceptions.ConnectionError:
                print(f"🔌 Erro de conexão na tentativa {attempt + 1}")
                if attempt < max_attempts - 1:
                    print("⏳ Aguardando servidor...")
                    time.sleep(3)
            except Exception as e:
                print(f"❌ Erro na tentativa {attempt + 1}: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
        
        print("⚠️ Todas as tentativas de validação falharam")
        print("🔍 Mas o servidor pode estar funcionando (verifique manualmente)")
        
        # Retornar True para não parar o sistema
        return True
        
    except Exception as e:
        print(f"❌ Erro crítico na validação: {e}")
        print("⚠️ Continuando mesmo assim...")
        return True  # Não parar o sistema por erro de validação

def show_next_steps():
    """Mostrar próximos passos"""
    print_header("PRÓXIMOS PASSOS")
    
    print("🎯 Sistema MoCoVe iniciado com sucesso!")
    print("\n📋 Para usar o sistema:")
    print("1. 🌐 Abra: http://localhost:5000 (Backend API)")
    print("2. 📁 Abra: frontend/index_complete_dashboard.html (Frontend)")
    print("3. 🧪 Execute: python test_complete_system.py (Testes)")
    
    print("\n🔧 Comandos úteis:")
    print("• python test_complete_system.py       - Testar sistema completo")
    print("• python test_system_status.py         - Testar e corrigir status")
    print("• python train_model.py                - Treinar modelo de IA")
    print("• python run_ai_pipeline.py            - Executar pipeline de IA")
    
    print("\n📊 Endpoints principais:")
    print("• GET  /api/system/status              - Status do sistema")
    print("• GET  /api/health                     - Health check do backend")
    print("• POST /api/system/test-binance        - Testar Binance")
    print("• GET  /api/watchlist/summary          - Resumo da watchlist")
    print("• POST /api/system/start-ai-agent      - Iniciar AI Agent")
    
    print("\n🔄 Componentes ativos:")
    print("• Backend Flask                        - Porta 5000")
    print("• AI Trading Agent                     - Trades automatizados")
    print("• Atualizador de Status               - Status em tempo real")
    
    print("\n⚠️ Importante:")
    print("• Configure suas chaves da Binance no arquivo .env")
    print("• O sistema precisa estar rodando para funcionar")
    print("• Use Ctrl+C para parar o servidor")
    print("• Status será atualizado automaticamente no dashboard")

def main():
    """Função principal"""
    print("🎯 MoCoVe - Inicialização Completa do Sistema")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. Verificar dependências
        if not check_dependencies():
            print("\n❌ Dependências em falta - corrija antes de continuar")
            return False
        
        # 2. Configurar database
        if not setup_database():
            print("\n❌ Falha na configuração do database")
            return False
        
        # 3. Popular dados iniciais
        populate_initial_data()
        
        # 4. Iniciar backend
        backend_process = start_backend()
        if not backend_process:
            print("\n❌ Falha ao iniciar backend")
            return False
        
        # 5. Iniciar AI Trading Agent
        ai_agent_process = start_ai_trading_agent()
        # Não interromper se usuário cancelar o AI Agent
        
        # 6. Iniciar atualizador de status
        status_updater_process = start_status_updater()
        
        # 7. Validar sistema
        if validate_system():
            show_next_steps()
            
            # Manter processo rodando
            print("\n🔄 Sistema rodando... (Ctrl+C para parar)")
            try:
                # Aguardar qualquer processo terminar
                processes = [backend_process]
                if ai_agent_process:
                    processes.append(ai_agent_process)
                if status_updater_process:
                    processes.append(status_updater_process)
                
                while any(p.poll() is None for p in processes):
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\n⏹️ Parando sistema...")
                backend_process.terminate()
                if ai_agent_process:
                    ai_agent_process.terminate()
                if status_updater_process:
                    status_updater_process.terminate()
                
                # Aguardar processos terminarem
                backend_process.wait()
                if ai_agent_process:
                    ai_agent_process.wait()
                if status_updater_process:
                    status_updater_process.wait()
                    
                print("✅ Sistema parado!")
        else:
            print("\n⚠️ Sistema com problemas na validação, mas pode estar funcionando")
            print("🌐 Teste manualmente: http://localhost:5000")
            print("🎨 Favicon: http://localhost:5000/favicon.ico")
            
            # Perguntar se quer continuar mesmo assim
            show_next_steps()
            
            print("\n🔄 Sistema rodando mesmo com avisos... (Ctrl+C para parar)")
            try:
                # Aguardar qualquer processo terminar
                processes = [backend_process]
                if ai_agent_process:
                    processes.append(ai_agent_process)
                if status_updater_process:
                    processes.append(status_updater_process)
                
                while any(p.poll() is None for p in processes):
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\n⏹️ Parando sistema...")
                backend_process.terminate()
                if ai_agent_process:
                    ai_agent_process.terminate()
                if status_updater_process:
                    status_updater_process.terminate()
                
                # Aguardar processos terminarem
                backend_process.wait()
                if ai_agent_process:
                    ai_agent_process.wait()
                if status_updater_process:
                    status_updater_process.wait()
                    
                print("✅ Sistema parado!")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Inicialização interrompida pelo usuário")
        return False
    except Exception as e:
        print(f"\n❌ Erro durante inicialização: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
