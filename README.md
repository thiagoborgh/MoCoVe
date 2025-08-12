# MoCoVe 🚀

**Mo**nitoramento, **Co**mpra e **Ve**nda automatizada de memecoins com Inteligência Artificial

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18.x-blue.svg)](https://reactjs.org/)

## 🎯 Visão Geral

O MoCoVe é um sistema completo de trading automatizado de memecoins que utiliza inteligência artificial para analisar volatilidade, indicadores técnicos e executar negociações estratégicas na Binance. O sistema oferece uma interface web moderna para monitoramento em tempo real e configuração de parâmetros de trading.

### 🌟 Principais Características

- **🤖 IA Integrada**: Modelo de Machine Learning para predições de mercado
- **📊 Análise Técnica**: RSI, Médias Móveis, Bandas de Bollinger, MACD
- **🔄 Trading Automatizado**: Ordens de compra/venda baseadas em regras inteligentes
- **📈 Interface Moderna**: Dashboard React com gráficos em tempo real
- **🔒 Ambiente Seguro**: Suporte completo ao testnet da Binance
- **🐳 Docker Ready**: Containerização completa para deploy fácil

## 🏗️ Arquitetura

```
MoCoVe/
├── 🖥️ backend/          # Flask API backend
├── 🎨 frontend/         # React frontend
├── 🧠 ai/              # Modelos de Machine Learning
├── 📜 scripts/         # Scripts de automação
├── ⚙️ config/          # Configurações
├── 🧪 tests/           # Testes automatizados
└── 🐳 docker/          # Configurações Docker
```

### 🔧 Stack Tecnológico

**Backend:**
- Python 3.9+ com Flask
- SQLite para armazenamento
- CCXT para integração com exchanges
- Scikit-learn para ML

**Frontend:**
- React 18 com Hooks
- Tailwind CSS para estilização
- Chart.js para gráficos
- Axios para comunicação API

**IA/ML:**
- RandomForest para classificação
- Pandas para manipulação de dados
- NumPy para computação numérica
- FastAPI para serviço de predição

## 🚀 Instalação Rápida

### Pré-requisitos
- Python 3.9+
- Node.js 16+
- Git

### 1. Clone o Repositório
```bash
git clone https://github.com/thiagoborgh/MoCoVe.git
cd MoCoVe
```

### 2. Configuração de Ambiente
```bash
# Copiar configurações de exemplo
cp config/.env.example .env

# Editar variáveis de ambiente
# Adicionar suas chaves da API Binance (testnet)
```

### 3. Instalação com Docker (Recomendado)
```bash
# Build e start dos serviços
docker-compose up -d

# Verificar status
docker-compose ps
```

### 4. Instalação Manual
```bash
# Instalar dependências Python
pip install -r requirements.txt

# Instalar dependências Node.js
npm install

# Inicializar banco de dados
python scripts/data_collector.py

# Treinar modelo inicial
python ai/train_model.py
```

## 🎮 Uso

### Iniciar Serviços

**Com Docker:**
```bash
docker-compose up -d
```

**Manual:**
```bash
# Terminal 1: Backend
cd backend && python app.py

# Terminal 2: Serviço IA
cd ai && uvicorn ai_model:app --host 0.0.0.0 --port 5001

# Terminal 3: Coleta de dados (opcional)
cd scripts && python data_collector.py
```

### Acessar Interface

- **Frontend**: http://localhost:5000
- **API Backend**: http://localhost:5000/api
- **Serviço IA**: http://localhost:5001
- **Documentação API**: http://localhost:5001/docs

## 📊 Funcionalidades

### 🎯 Dashboard Principal
- **Preços em Tempo Real**: Monitoramento de múltiplas memecoins
- **Gráficos Interativos**: Histórico de preços com Chart.js
- **Alertas de Volatilidade**: Notificações visuais para oportunidades
- **Controles de Trading**: Botões para compra/venda manual

### ⚙️ Configurações
- **Pares de Trading**: DOGE/BUSD, SHIB/BUSD, PEPE/BUSD, etc.
- **Quantidade**: Valor em USD ou quantidade de tokens
- **Limites**: Thresholds de volatilidade personalizáveis
- **Risk Management**: Stop loss e take profit

### 🤖 IA e Automação
- **Predições ML**: Modelo RandomForest treinado com dados históricos
- **Indicadores Técnicos**: RSI, MACD, Bollinger Bands
- **Análise de Sentimento**: Placeholder para integração futura
- **Retreinamento**: Modelo atualizado automaticamente

### 📈 Análise e Relatórios
- **Histórico de Trades**: Tabela com todas as negociações
- **Exportação CSV**: Download de dados para análise externa
- **Métricas de Performance**: Win rate, P&L, drawdown
- **Estatísticas de Volatilidade**: Análise de risco

## 🔧 Configuração Avançada

### 🔐 Variáveis de Ambiente
```bash
# Database
DB_PATH=./memecoin.db

# Binance API (Testnet)
BINANCE_API_KEY=your_testnet_key
BINANCE_API_SECRET=your_testnet_secret
USE_TESTNET=true

# Trading Parameters
DEFAULT_SYMBOL=DOGE/BUSD
DEFAULT_AMOUNT=100
DEFAULT_VOLATILITY_THRESHOLD=0.05

# AI Model
MODEL_PATH=./ai/memecoin_rf_model.pkl
AI_MODEL_URL=http://localhost:5001
```

### 📝 Configuração de Trading
```json
{
  "trading": {
    "buy_threshold": 0.02,
    "sell_threshold": -0.02,
    "max_daily_trades": 10,
    "risk_management": {
      "stop_loss": 0.05,
      "take_profit": 0.10
    }
  }
}
```

## 🧪 Testes

### Executar Testes
```bash
# Todos os testes
python -m pytest tests/

# Testes específicos
python -m pytest tests/test_backend.py
python -m pytest tests/test_ai.py

# Com cobertura
python -m pytest --cov=backend tests/
```

### Testes Manuais
```bash
# Testar coleta de dados
python scripts/data_collector.py

# Testar modelo IA
python ai/train_model.py

# Testar API
curl http://localhost:5000/api/status
```

## 📚 API Endpoints

### Backend API
- `GET /api/status` - Status do sistema
- `GET /api/trades` - Histórico de negociações
- `GET /api/prices` - Dados de preços
- `GET /api/volatility` - Análise de volatilidade
- `POST /api/execute_trade` - Executar negociação
- `GET/POST /api/settings` - Configurações

### IA API
- `POST /predict` - Predição de trading
- `GET /health` - Health check
- `POST /reload_model` - Recarregar modelo

## 🚀 Deploy em Produção

### Requisitos de Produção
- VPS com IP fixo (DigitalOcean, AWS, etc.)
- SSL/TLS certificado
- Backup automático do banco de dados
- Monitoramento e logs

### Deploy com Docker
```bash
# Produção
docker-compose -f docker-compose.prod.yml up -d

# Nginx para SSL
docker-compose -f docker-compose.nginx.yml up -d
```

### Considerações de Segurança
- ✅ Usar HTTPS em produção
- ✅ Configurar firewall adequadamente
- ✅ Backup regular do banco de dados
- ✅ Monitoramento de logs
- ✅ Rate limiting na API

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## ⚠️ Disclaimer

**AVISO IMPORTANTE**: Este projeto é para fins educacionais e de demonstração. Trading de criptomoedas envolve riscos significativos. Sempre:

- ✅ Use o testnet durante desenvolvimento
- ✅ Teste extensivamente antes da produção
- ✅ Invista apenas o que pode perder
- ✅ Entenda os riscos do trading automatizado
- ✅ Consulte um consultor financeiro

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- [CCXT](https://github.com/ccxt/ccxt) - Biblioteca de exchange
- [Binance](https://binance.com) - Exchange e testnet
- [CoinGecko](https://coingecko.com) - Dados de mercado
- [React](https://reactjs.org) - Framework frontend
- [Flask](https://flask.palletsprojects.com) - Framework backend

---

**Desenvolvido com ❤️ por [Thiago Borgh](https://github.com/thiagoborgh)**

🚀 **Happy Trading!** 🚀
