#!/usr/bin/env python3
"""
MoCoVe Setup Script - Configuração Automatizada
Script para configurar e inicializar o projeto MoCoVe
"""

import os
import sys
import subprocess
import sqlite3
import json
import time
from pathlib import Path

def print_banner():
    """Exibe banner do MoCoVe"""
    print("""
    ███╗   ███╗ ██████╗  ██████╗ ██████╗ ██╗   ██╗███████╗
    ████╗ ████║██╔═══██╗██╔════╝██╔═══██╗██║   ██║██╔════╝
    ██╔████╔██║██║   ██║██║     ██║   ██║██║   ██║█████╗  
    ██║╚██╔╝██║██║   ██║██║     ██║   ██║╚██╗ ██╔╝██╔══╝  
    ██║ ╚═╝ ██║╚██████╔╝╚██████╗╚██████╔╝ ╚████╔╝ ███████╗
    ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚═════╝   ╚═══╝  ╚══════╝
    
    🚀 Sistema de Trading Automatizado de Memecoins com IA
    """)

def check_requirements():
    """Verifica requisitos do sistema"""
    print("🔍 Verificando requisitos do sistema...")
    
    # Verificar Python
    python_version = sys.version_info
    if python_version < (3, 9):
        print("❌ Python 3.9+ é necessário")
        return False
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Verificar pip
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print("✅ pip instalado")
    except subprocess.CalledProcessError:
        print("❌ pip não encontrado")
        return False
    
    # Verificar Node.js (opcional)
    try:
        result = subprocess.run(["node", "--version"], 
                              check=True, capture_output=True, text=True)
        print(f"✅ Node.js {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ Node.js não encontrado (opcional para desenvolvimento)")
    
    return True

def install_dependencies():
    """Instala dependências Python"""
    print("\n📦 Instalando dependências Python...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Dependências instaladas com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def setup_environment():
    """Configura arquivo de ambiente"""
    print("\n⚙️ Configurando arquivo de ambiente...")
    
    env_path = Path(".env")
    env_example_path = Path("config/.env.example")
    
    if env_path.exists():
        print("✅ Arquivo .env já existe")
        return True
    
    if env_example_path.exists():
        # Copiar exemplo
        with open(env_example_path, 'r') as src:
            content = src.read()
        
        with open(env_path, 'w') as dst:
            dst.write(content)
        
        print("✅ Arquivo .env criado a partir do exemplo")
        print("📝 Edite o arquivo .env com suas configurações da API Binance")
        return True
    else:
        # Criar arquivo básico
        env_content = """# MoCoVe Configuration
DB_PATH=./memecoin.db
USE_TESTNET=true
PORT=5000
DEBUG=false
DEFAULT_SYMBOL=DOGE/BUSD
DEFAULT_AMOUNT=100
DEFAULT_VOLATILITY_THRESHOLD=0.05
"""
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print("✅ Arquivo .env básico criado")
        return True

def init_database():
    """Inicializa banco de dados"""
    print("\n🗄️ Inicializando banco de dados...")
    
    db_path = "memecoin.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tabela de preços
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                price REAL NOT NULL,
                volume REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de negociações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATETIME NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('buy', 'sell')),
                symbol TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                status TEXT DEFAULT 'completed',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de configurações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                amount REAL NOT NULL,
                volatility_threshold REAL NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Configuração padrão
        cursor.execute('SELECT COUNT(*) FROM settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO settings (symbol, amount, volatility_threshold)
                VALUES ('DOGE/BUSD', 100, 0.05)
            ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Banco de dados inicializado")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        return False

def create_directories():
    """Cria diretórios necessários"""
    print("\n📁 Criando diretórios...")
    
    directories = ["logs", "ai/models", "data/backup"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Diretório criado: {directory}")

def collect_initial_data():
    """Coleta dados iniciais"""
    print("\n📊 Coletando dados iniciais...")
    
    try:
        # Verificar se temos dados
        conn = sqlite3.connect("memecoin.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM prices")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 100:
            print("✅ Dados suficientes já existem no banco")
            return True
        
        # Executar coleta de dados
        print("📡 Coletando dados históricos...")
        result = subprocess.run([
            sys.executable, "scripts/data_collector.py"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Dados iniciais coletados")
            return True
        else:
            print(f"⚠️ Aviso na coleta de dados: {result.stderr}")
            return True  # Continuar mesmo com avisos
            
    except subprocess.TimeoutExpired:
        print("⚠️ Timeout na coleta de dados (continuando...)")
        return True
    except Exception as e:
        print(f"⚠️ Erro na coleta de dados: {e}")
        return True  # Não crítico

def train_initial_model():
    """Treina modelo inicial"""
    print("\n🧠 Treinando modelo inicial de IA...")
    
    try:
        result = subprocess.run([
            sys.executable, "ai/train_model.py"
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✅ Modelo inicial treinado")
            return True
        else:
            print(f"⚠️ Aviso no treinamento: {result.stderr}")
            return True  # Continuar mesmo com avisos
            
    except subprocess.TimeoutExpired:
        print("⚠️ Timeout no treinamento (continuando...)")
        return True
    except Exception as e:
        print(f"⚠️ Erro no treinamento: {e}")
        return True  # Não crítico

def test_components():
    """Testa componentes principais"""
    print("\n🧪 Testando componentes...")
    
    tests_passed = 0
    total_tests = 3
    
    # Teste 1: Backend
    print("1. Testando backend...")
    try:
        # Import test
        sys.path.insert(0, 'backend')
        import app
        print("   ✅ Backend importado com sucesso")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Erro no backend: {e}")
    
    # Teste 2: IA
    print("2. Testando serviço de IA...")
    try:
        sys.path.insert(0, 'ai')
        import ai_model
        print("   ✅ Serviço de IA importado com sucesso")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Erro no serviço de IA: {e}")
    
    # Teste 3: Scripts
    print("3. Testando scripts...")
    try:
        sys.path.insert(0, 'scripts')
        import data_collector
        print("   ✅ Scripts importados com sucesso")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Erro nos scripts: {e}")
    
    print(f"\n📊 Testes: {tests_passed}/{total_tests} passaram")
    return tests_passed >= 2  # Pelo menos 2 devem passar

def print_next_steps():
    """Exibe próximos passos"""
    print("""
🎉 Setup do MoCoVe concluído com sucesso!

📋 PRÓXIMOS PASSOS:

1. 🔐 Configurar API Keys:
   - Edite o arquivo .env
   - Adicione suas chaves da API Binance (testnet)
   - Obtenha em: https://testnet.binance.vision/

2. 🚀 Iniciar Serviços:
   
   Opção A - Docker (Recomendado):
   docker-compose up -d
   
   Opção B - Manual:
   # Terminal 1: Backend
   cd backend && python app.py
   
   # Terminal 2: IA
   cd ai && uvicorn ai_model:app --host 0.0.0.0 --port 5001

3. 🌐 Acessar Interface:
   - Frontend: http://localhost:5000
   - API Docs: http://localhost:5001/docs

4. 📚 Documentação:
   - README.md para informações detalhadas
   - config/settings.json para configurações avançadas

⚠️  IMPORTANTE:
- Use apenas o testnet durante desenvolvimento
- Teste extensivamente antes da produção
- Trading envolve riscos - invista com responsabilidade

🤝 Suporte:
- Issues: https://github.com/thiagoborgh/MoCoVe/issues
- Documentação: README.md

Happy Trading! 🚀
""")

def main():
    """Função principal do setup"""
    print_banner()
    
    # Verificar se estamos no diretório correto
    if not Path("requirements.txt").exists():
        print("❌ Execute este script no diretório raiz do projeto MoCoVe")
        sys.exit(1)
    
    # Executar etapas do setup
    steps = [
        ("Verificando requisitos", check_requirements),
        ("Instalando dependências", install_dependencies),
        ("Configurando ambiente", setup_environment),
        ("Criando diretórios", create_directories),
        ("Inicializando banco", init_database),
        ("Coletando dados iniciais", collect_initial_data),
        ("Treinando modelo", train_initial_model),
        ("Testando componentes", test_components),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n{'='*60}")
        print(f"🔄 {step_name}...")
        
        try:
            if step_func():
                print(f"✅ {step_name} - Concluído")
            else:
                print(f"❌ {step_name} - Falhou")
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} - Erro: {e}")
            failed_steps.append(step_name)
    
    print(f"\n{'='*60}")
    
    if failed_steps:
        print(f"⚠️ Setup concluído com {len(failed_steps)} avisos:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nO sistema pode funcionar com limitações.")
    
    print_next_steps()

if __name__ == "__main__":
    main()
