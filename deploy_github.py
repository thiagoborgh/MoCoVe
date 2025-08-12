#!/usr/bin/env python3
"""
Script de Deploy para GitHub - MoCoVe
Prepara e sobe o projeto para o GitHub
"""

import os
import sys
import subprocess
from datetime import datetime

def print_header(title):
    print("\n" + "="*70)
    print(f"🚀 {title}")
    print("="*70)

def run_command(command, description):
    """Executar comando e mostrar resultado"""
    print(f"🔧 {description}")
    print(f"💻 Comando: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Sucesso!")
            if result.stdout:
                print(f"📄 Output: {result.stdout.strip()}")
        else:
            print("❌ Erro!")
            if result.stderr:
                print(f"🚨 Erro: {result.stderr.strip()}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return False

def create_gitignore():
    """Criar arquivo .gitignore"""
    print_header("CRIANDO .gitignore")
    
    gitignore_content = """# MoCoVe - Trading System
# Arquivos sensíveis e temporários

# Configurações sensíveis
.env
*.env
api_keys.txt
config_local.json

# Database e dados
*.db
*.sqlite
*.sqlite3
backup/
logs/

# Modelos treinados
*.pkl
*.joblib
*.h5
models/

# Cache Python
__pycache__/
*.py[cod]
*$py.class
*.so

# Distribuição / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/
log/

# Temporary files
*.tmp
*.temp
temp/
tmp/

# Node modules (se houver frontend em Node)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Dados de mercado em cache
market_data/
price_cache/
historical_data/

# Backups
*.bak
backup_*
"""
    
    try:
        with open('.gitignore', 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("✅ .gitignore criado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar .gitignore: {e}")
        return False

def create_readme():
    """Criar README.md completo"""
    print_header("CRIANDO README.md")
    
    readme_content = """# 🚀 MoCoVe - Sistema Completo de Trading com IA

## 📋 Descrição
MoCoVe é um sistema avançado de trading de criptomoedas com inteligência artificial, monitoramento em tempo real e interface web completa. O sistema monitora 40+ criptomoedas, analisa sentimentos sociais e fornece predições baseadas em IA.

## ✨ Funcionalidades Principais

### 🤖 Inteligência Artificial
- Modelo de machine learning treinado para predições de preço
- Análise de sentimento social em tempo real
- Pipeline automatizado de IA com retreinamento periódico
- Alertas baseados em confiança do modelo

### 📊 Monitoramento de Mercado
- **40+ Criptomoedas** organizadas por categorias:
  - 🎭 **Memecoins**: DOGE, SHIB, PEPE, WIF, FLOKI, BONK, etc.
  - 🏗️ **DeFi**: UNI, AAVE, COMP, SUSHI, CRV, 1INCH
  - 🌐 **Layer 1**: SOL, ADA, AVAX, DOT, ATOM, NEAR
  - 🤖 **AI Tokens**: FET, AGIX, OCEAN, RLC, RENDER
  - 🎮 **Gaming**: AXS, SAND, MANA, ENJ

### 🔗 Integração Binance
- Conexão segura com API da Binance
- Monitoramento de saldo em tempo real
- Testes de conectividade automatizados
- Suporte para testnet e produção

### 🌐 Interface Web Completa
- Dashboard responsivo em React
- Controles de sistema em tempo real
- Visualização de dados de mercado
- Alertas e notificações

### 📈 Sistema de Alertas
- Alertas de variação de preço
- Detecção de picos de volume
- Monitoramento de sentimento social
- Sistema de notificações configurável

## 🛠️ Instalação e Configuração

### Pré-requisitos
```bash
# Python 3.8+
python --version

# Pacotes necessários
pip install flask requests pandas numpy scikit-learn python-binance
```

### Configuração Rápida
```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/mocove.git
cd mocove

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas chaves da Binance

# 3. Execute o script de inicialização
python start_complete_system.py
```

### Configuração Manual
```bash
# 1. Popular dados históricos
python populate_prices.py

# 2. Treinar modelo de IA
python train_model.py

# 3. Iniciar backend
python backend/app_real.py

# 4. Abrir frontend
# Abra frontend/index_complete.html no navegador
```

## 🚀 Uso do Sistema

### Inicialização Completa
```bash
# Inicia todos os componentes automaticamente
python start_complete_system.py
```

### Testes do Sistema
```bash
# Executa bateria completa de testes
python test_complete_system.py
```

### Componentes Individuais
```bash
# Apenas backend
python backend/app_real.py

# Pipeline de IA
python run_ai_pipeline.py

# Sistema periódico
python run_ai_pipeline_periodic.py
```

## 📡 API Endpoints

### Sistema
- `GET /api/system/status` - Status geral do sistema
- `POST /api/system/test-binance` - Testar conexão Binance
- `POST /api/system/start-ai-agent` - Iniciar agente de IA
- `POST /api/system/update-balance` - Atualizar saldo
- `POST /api/system/update-market-data` - Atualizar dados de mercado

### Watchlist
- `GET /api/watchlist/summary` - Resumo da watchlist
- `GET /api/watchlist/coins` - Lista de moedas
- `GET /api/watchlist/top-performers` - Melhores performers
- `GET /api/watchlist/alerts` - Alertas ativos

### Dados
- `GET /api/prices/recent` - Preços recentes
- `GET /api/predictions/latest` - Últimas predições
- `GET /api/system/sentiment` - Dados de sentimento

## 🎯 Arquitetura do Sistema

```
MoCoVe/
├── 🤖 AI Components/
│   ├── train_model.py          # Treinamento do modelo
│   ├── run_ai_pipeline.py      # Pipeline de IA
│   └── ai_model.py             # Modelo principal
├── 🌐 Backend/
│   ├── app_real.py             # API Flask principal
│   ├── system_controller.py    # Controlador do sistema
│   └── watchlist_manager.py    # Gerenciador da watchlist
├── 🖥️ Frontend/
│   └── index_complete.html     # Interface web completa
├── 📊 Data/
│   ├── memecoin.db            # Database SQLite
│   ├── coin_watchlist_expanded.json # Configuração das moedas
│   └── config.json            # Configurações do sistema
└── 🔧 Scripts/
    ├── start_complete_system.py    # Inicialização completa
    ├── test_complete_system.py     # Testes integrados
    └── populate_prices.py          # População de dados
```

## ⚙️ Configuração

### Arquivo .env
```env
# Binance API
BINANCE_API_KEY=sua_api_key_aqui
BINANCE_SECRET_KEY=sua_secret_key_aqui
BINANCE_TESTNET=true

# Sistema
FLASK_ENV=production
FLASK_PORT=5000
DEBUG=false

# Database
DB_BACKUP_ENABLED=true
DB_CLEANUP_DAYS=30

# IA
AI_RETRAIN_INTERVAL=24
AI_CONFIDENCE_THRESHOLD=0.7
```

### Configurações Avançadas
Edite `config.json` para personalizar:
- Intervalos de atualização
- Thresholds de alertas
- Configurações de trading
- Parâmetros de IA

## 📊 Monitoramento e Alertas

### Tipos de Alertas
- 📈 **PUMP**: Variações positivas significativas
- 📉 **DUMP**: Quedas bruscas de preço
- 📊 **VOLUME_SPIKE**: Picos de volume anômalos
- 🤖 **AI_PREDICTION**: Predições de alta confiança

### Sistema de Sentimento
- Análise de redes sociais
- Score de sentimento (-1 a +1)
- Contagem de menções
- Tendências em tempo real

## 🔒 Segurança

- ✅ Chaves API criptografadas
- ✅ Conexões HTTPS
- ✅ Rate limiting
- ✅ Validação de entrada
- ✅ Logs de segurança

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 🆘 Suporte

### Problemas Comuns

#### ❌ "Backend não responde"
```bash
# Verificar se o processo está rodando
netstat -ano | findstr :5000

# Reiniciar sistema
python start_complete_system.py
```

#### ❌ "Erro de conexão Binance"
```bash
# Verificar chaves no .env
# Testar conectividade
python -c "from system_controller import SystemController; sc = SystemController(); print(sc.test_binance_connection())"
```

#### ❌ "Database não encontrado"
```bash
# Recriar database
python populate_prices.py
```

### Logs e Debug
```bash
# Logs do sistema
tail -f logs/mocove.log

# Debug modo
export FLASK_ENV=development
python backend/app_real.py
```

## 📞 Contato

- 📧 Email: suporte@mocove.com
- 💬 Discord: [MoCoVe Community](https://discord.gg/mocove)
- 🐦 Twitter: [@MoCoVeTrading](https://twitter.com/mocovetrading)

---

**⚠️ Aviso Legal**: Este sistema é apenas para fins educacionais e de pesquisa. Trading de criptomoedas envolve riscos significativos. Sempre faça sua própria pesquisa (DYOR) e nunca invista mais do que pode perder.

---

💡 **Feito com ❤️ para a comunidade crypto brasileira** 🇧🇷
"""
    
    try:
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("✅ README.md criado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar README.md: {e}")
        return False

def create_env_example():
    """Criar arquivo .env.example"""
    print_header("CRIANDO .env.example")
    
    env_example = """# MoCoVe - Configurações de Ambiente
# Copie este arquivo para .env e configure suas chaves

# Binance API Configuration
BINANCE_API_KEY=sua_binance_api_key_aqui
BINANCE_SECRET_KEY=sua_binance_secret_key_aqui
BINANCE_TESTNET=true

# Flask Configuration
FLASK_ENV=production
FLASK_PORT=5000
FLASK_DEBUG=false

# Database Configuration
DATABASE_FILE=memecoin.db
DB_BACKUP_ENABLED=true
DB_CLEANUP_DAYS=30

# AI Configuration
AI_ENABLED=true
AI_RETRAIN_INTERVAL_HOURS=24
AI_CONFIDENCE_THRESHOLD=0.7
AI_MODEL_FILE=memecoin_model.pkl

# Trading Configuration (CUIDADO - APENAS PARA ESPECIALISTAS)
TRADING_ENABLED=false
TRADING_MAX_POSITION_SIZE=0.01
TRADING_STOP_LOSS=5.0
TRADING_TAKE_PROFIT=15.0

# Alerts Configuration
ALERTS_ENABLED=true
PRICE_ALERT_THRESHOLD=5.0
VOLUME_ALERT_THRESHOLD=50.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/mocove.log

# Security
API_RATE_LIMIT=100
SESSION_TIMEOUT_MINUTES=60

# Performance
CACHE_SIZE_MB=100
MAX_CONCURRENT_REQUESTS=50
"""
    
    try:
        with open('.env.example', 'w', encoding='utf-8') as f:
            f.write(env_example)
        print("✅ .env.example criado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar .env.example: {e}")
        return False

def prepare_for_github():
    """Preparar arquivos para GitHub"""
    print_header("PREPARAÇÃO PARA GITHUB")
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('server.js'):
        print("❌ Não estamos no diretório raiz do projeto MoCoVe!")
        return False
    
    # Criar arquivos necessários
    files_created = []
    
    if create_gitignore():
        files_created.append('.gitignore')
    
    if create_readme():
        files_created.append('README.md')
    
    if create_env_example():
        files_created.append('.env.example')
    
    print(f"\n✅ Arquivos criados: {', '.join(files_created)}")
    
    # Verificar se .env existe (não deve ser commitado)
    if os.path.exists('.env'):
        print("⚠️ Arquivo .env detectado - será ignorado pelo .gitignore")
    
    return True

def init_git_repo():
    """Inicializar repositório Git"""
    print_header("INICIALIZANDO REPOSITÓRIO GIT")
    
    commands = [
        ("git init", "Inicializar repositório Git"),
        ("git add .", "Adicionar todos os arquivos"),
        ('git commit -m "Initial commit: MoCoVe Trading System v1.0"', "Fazer commit inicial")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def show_github_instructions():
    """Mostrar instruções para subir no GitHub"""
    print_header("INSTRUÇÕES PARA GITHUB")
    
    print("📋 Para subir no GitHub, execute os seguintes comandos:")
    print()
    print("1. 🌐 Crie um repositório no GitHub:")
    print("   • Vá para https://github.com/new")
    print("   • Nome: mocove-trading-system")
    print("   • Descrição: Sistema Completo de Trading com IA")
    print("   • Público ou Privado (sua escolha)")
    print("   • NÃO inicialize com README (já temos um)")
    print()
    print("2. 🔗 Conecte o repositório local:")
    print("   git remote add origin https://github.com/SEU_USUARIO/mocove-trading-system.git")
    print("   git branch -M main")
    print("   git push -u origin main")
    print()
    print("3. 🎯 Comandos completos:")
    print("   git remote add origin https://github.com/SEU_USUARIO/mocove-trading-system.git")
    print("   git branch -M main")
    print("   git push -u origin main")
    print()
    print("⚠️ IMPORTANTE:")
    print("• Substitua 'SEU_USUARIO' pelo seu username do GitHub")
    print("• Suas chaves da Binance NÃO serão enviadas (protegidas pelo .gitignore)")
    print("• Configure o .env.example com instruções para outros usuários")
    print()
    print("📁 Estrutura do repositório:")
    print("• README.md completo com documentação")
    print("• .gitignore protegendo arquivos sensíveis")
    print("• .env.example com template de configuração")
    print("• Código fonte completo e organizado")

def main():
    """Função principal"""
    print("🚀 MoCoVe - Preparação para Deploy no GitHub")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. Preparar arquivos
        if not prepare_for_github():
            print("\n❌ Falha na preparação dos arquivos")
            return False
        
        # 2. Inicializar Git
        if not os.path.exists('.git'):
            if not init_git_repo():
                print("\n❌ Falha na inicialização do Git")
                return False
        else:
            print("\n✅ Repositório Git já existe")
            
            # Adicionar novos arquivos
            run_command("git add .", "Adicionando arquivos atualizados")
            run_command('git commit -m "Update: Complete system with frontend and expanded watchlist"', 
                       "Commitando atualizações")
        
        # 3. Mostrar instruções
        show_github_instructions()
        
        print("\n🎉 Preparação concluída com sucesso!")
        print("🚀 Seu projeto MoCoVe está pronto para o GitHub!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante preparação: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
