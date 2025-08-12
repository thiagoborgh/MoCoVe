# MoCoVe AI Trading System - Documentação Completa

## 🎯 Visão Geral

O **MoCoVe** é um sistema completo de trading automatizado com Inteligência Artificial, desenvolvido para monitoramento de criptomoedas (especialmente memecoins) com análise de sentimento das redes sociais e execução automática de trades baseada em indicadores técnicos avançados.

### 🌟 Características Principais

- **🤖 AI Trading Agent**: Sistema autônomo com análise técnica completa
- **📊 Dashboard Moderno**: Interface React responsiva em tempo real
- **🐦 Análise de Sentimento**: Monitoramento Twitter, Reddit, Telegram
- **💰 Gestão de Risco**: Sistema avançado de controle de perdas
- **📱 PWA Ready**: Instalável como aplicativo mobile
- **🚀 Deploy Automático**: Integração com Surge.sh
- **🔄 Monitoramento 24/7**: Operação contínua e alertas

## 🏗️ Arquitetura do Sistema

```
MoCoVe AI Trading System
├── 🤖 AI Trading Agent (Python)
│   ├── Análise Técnica (SMA, EMA, RSI, Bollinger)
│   ├── Machine Learning (Previsões)
│   ├── Gestão de Risco
│   └── Execução de Trades
├── 🖥️ Backend API (Flask)
│   ├── Integração Binance
│   ├── Banco de Dados SQLite
│   ├── Análise de Sentimento
│   └── Monitoramento de Memecoins
├── 🌐 Frontend Dashboard (React)
│   ├── Monitoramento em Tempo Real
│   ├── Configuração do Agent
│   ├── Histórico de Trades
│   └── Análise de Performance
└── 🚀 Deploy & Automation
    ├── Surge.sh Integration
    ├── Process Management
    └── Auto-scaling
```

## 🚀 Instalação e Configuração

### Pré-requisitos

- **Python 3.8+**
- **Node.js 16+**
- **Conta Binance** (Testnet recomendado)
- **Chaves API Binance**

### 1. Quick Start (Recomendado)

```bash
# Clonar e entrar no diretório
git clone <repository-url>
cd MoCoVe

# Configuração interativa
node quick-start.js --config

# Iniciar sistema completo
node quick-start.js
```

### 2. Instalação Manual

#### Backend Setup
```bash
# Instalar dependências Python
pip install flask flask-cors python-binance pandas numpy requests

# Configurar variáveis de ambiente
copy .env.example .env
# Editar .env com suas chaves Binance
```

#### Frontend Setup
```bash
# Instalar dependências Node.js
npm install

# Ou usar servidor estático simples incluído
# Nenhuma instalação adicional necessária
```

## ⚙️ Configuração

### 1. Configuração das Chaves API

Crie um arquivo `.env`:

```env
# Binance API (use Testnet para testes)
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
BINANCE_TESTNET=true

# Configurações do Sistema
DEFAULT_SYMBOL=DOGEUSDT
INVESTMENT_AMOUNT=25.0
RISK_LEVEL=conservative

# APIs de Redes Sociais (opcional)
TWITTER_BEARER_TOKEN=your_token
REDDIT_CLIENT_ID=your_client_id
TELEGRAM_BOT_TOKEN=your_token
```

### 2. Configuração do AI Agent

```bash
# Configuração interativa do agent
python ai_agent_config.py

# Ou editar diretamente
vim ai_agent_settings.json
```

Exemplo de configuração:

```json
{
  "trading": {
    "symbol": "DOGEUSDT",
    "investment_amount": 25.0,
    "risk_level": "conservative",
    "max_trades_per_day": 5,
    "stop_loss_percentage": 5.0,
    "take_profit_percentage": 10.0
  },
  "technical_analysis": {
    "sma_period": 20,
    "ema_period": 12,
    "rsi_period": 14,
    "bollinger_period": 20,
    "confidence_threshold": 0.7
  },
  "sentiment_analysis": {
    "enabled": true,
    "weight": 0.3,
    "sources": ["twitter", "reddit", "telegram"]
  }
}
```

## 🤖 AI Trading Agent

### Funcionalidades

#### Análise Técnica
- **SMA (Simple Moving Average)**: Tendência de preço
- **EMA (Exponential Moving Average)**: Responsividade a mudanças
- **RSI (Relative Strength Index)**: Níveis de sobrecompra/sobrevenda
- **Bollinger Bands**: Volatilidade e pontos de entrada
- **MACD**: Momentum e sinais de cruzamento

#### Sistema de Scoring
```python
def calculate_confidence_score(self, indicators):
    """
    Calcula confiança baseada em múltiplos indicadores
    
    Pesos:
    - Tendência (SMA/EMA): 40%
    - Momentum (RSI/MACD): 30%
    - Volatilidade (Bollinger): 20%
    - Sentimento Social: 10%
    """
    trend_score = self.analyze_trend(indicators)
    momentum_score = self.analyze_momentum(indicators)
    volatility_score = self.analyze_volatility(indicators)
    sentiment_score = self.get_sentiment_score()
    
    total_score = (
        trend_score * 0.4 +
        momentum_score * 0.3 +
        volatility_score * 0.2 +
        sentiment_score * 0.1
    )
    
    return min(max(total_score, 0), 1)
```

#### Gestão de Risco

- **Stop Loss Dinâmico**: Ajuste baseado em volatilidade
- **Take Profit Escalonado**: Múltiplos níveis de saída
- **Position Sizing**: Cálculo de tamanho baseado em risco
- **Diversificação**: Limites por símbolo e tempo

### Modos de Operação

1. **Conservative** (Padrão)
   - Confiança mínima: 80%
   - Stop loss: 3%
   - Take profit: 6%
   - Max trades/dia: 3

2. **Moderate**
   - Confiança mínima: 70%
   - Stop loss: 5%
   - Take profit: 10%
   - Max trades/dia: 5

3. **Aggressive**
   - Confiança mínima: 60%
   - Stop loss: 7%
   - Take profit: 15%
   - Max trades/dia: 8

## 📊 Dashboard e Frontend

### Funcionalidades do Dashboard

#### 1. Overview em Tempo Real
- **Preço Atual**: Atualização a cada 5 segundos
- **Performance 24h**: Variação percentual
- **Volume de Trading**: Análise de liquidez
- **Status do Agent**: Ativo/Inativo, último trade

#### 2. Gestão de Trades
- **Histórico Completo**: Todos os trades executados
- **Análise de Performance**: ROI, Sharpe ratio, drawdown
- **Filtros Avançados**: Por período, símbolo, tipo
- **Exportação**: CSV, PDF para análise

#### 3. Monitoramento de Memecoins
- **Top 20 Memecoins**: Ordenação por volume/sentimento
- **Análise de Sentimento**: Score das redes sociais
- **Alertas**: Notificações de oportunidades
- **Watchlist**: Personalização de moedas

#### 4. Configuração do Agent
- **Parâmetros de Trading**: Risk level, amounts, symbols
- **Indicadores Técnicos**: Períodos e thresholds
- **Notificações**: Email, webhook, Telegram
- **Backup/Restore**: Configurações salvás

### Interface Responsiva

O dashboard é totalmente responsivo com:

- **Mobile First**: Otimizado para smartphones
- **PWA Support**: Instalável como app
- **Dark/Light Mode**: Temas alternativos
- **Real-time Updates**: WebSocket para dados instantâneos

## 🐦 Análise de Sentimento

### Fontes de Dados

1. **Twitter**
   - Hashtags relevantes: #DOGE, #cryptocurrency, etc.
   - Análise de volume de menções
   - Sentiment scoring com NLP
   - Influenciadores identificados

2. **Reddit**
   - Subreddits: r/cryptocurrency, r/dogecoin, etc.
   - Posts e comentários analisados
   - Upvotes como peso de relevância
   - Trending topics detection

3. **Telegram**
   - Canais públicos relevantes
   - Análise de mensagens
   - Volume de atividade
   - Bot sentiment scoring

### Algoritmo de Sentiment

```python
def calculate_sentiment_score(self, social_data):
    """
    Calcula score de sentimento agregado
    
    Inputs:
    - social_data: Dict com dados das fontes
    
    Output:
    - score: Float entre -1 (negativo) e 1 (positivo)
    """
    twitter_sentiment = self.analyze_twitter(social_data['twitter'])
    reddit_sentiment = self.analyze_reddit(social_data['reddit'])
    telegram_sentiment = self.analyze_telegram(social_data['telegram'])
    
    # Pesos baseados na confiabilidade da fonte
    weighted_score = (
        twitter_sentiment * 0.4 +  # Mais reativo
        reddit_sentiment * 0.4 +   # Mais fundamentado
        telegram_sentiment * 0.2   # Suporte adicional
    )
    
    return weighted_score
```

## 🛡️ Segurança e Gestão de Risco

### Medidas de Segurança

1. **API Keys Protection**
   - Variáveis de ambiente
   - Encrypting keys em produção
   - Rotation automática

2. **Trading Limits**
   - Limites diários/mensais
   - Stop loss obrigatório
   - Validation de orders

3. **Monitoring & Alerts**
   - Detecção de anomalias
   - Alertas de alta volatilidade
   - Emergency stop triggers

### Sistema de Gestão de Risco

```python
class RiskManager:
    def __init__(self):
        self.daily_loss_limit = 0.05  # 5% do capital
        self.position_size_limit = 0.1  # 10% por trade
        self.max_open_positions = 3
        
    def check_risk_before_trade(self, trade_data):
        """Valida trade antes da execução"""
        if self.daily_losses >= self.daily_loss_limit:
            return False, "Daily loss limit exceeded"
            
        if trade_data['size'] > self.position_size_limit:
            return False, "Position size too large"
            
        if len(self.open_positions) >= self.max_open_positions:
            return False, "Too many open positions"
            
        return True, "Risk check passed"
```

## 🚀 Deploy e Produção

### Deploy no Surge.sh

```bash
# Deploy automático
node deploy-surge.js

# Deploy manual
surge frontend/ mocove-ai-trading.surge.sh
```

### Configuração de Produção

1. **Backend Deployment**
   - Heroku, DigitalOcean, AWS
   - Variáveis de ambiente
   - Database scaling
   - SSL certificates

2. **Monitoring Setup**
   - Uptime monitoring
   - Performance metrics
   - Error tracking
   - Log aggregation

3. **Backup Strategy**
   - Database backups
   - Configuration backups
   - Trade history export
   - Recovery procedures

## 📈 Monitoramento e Analytics

### Métricas de Performance

1. **Trading Metrics**
   - Total Return: ROI acumulado
   - Sharpe Ratio: Retorno ajustado ao risco
   - Maximum Drawdown: Maior perda consecutiva
   - Win Rate: Percentual de trades positivos

2. **System Metrics**
   - Uptime: Disponibilidade do sistema
   - Latency: Tempo de resposta
   - Error Rate: Taxa de erros
   - API Call Usage: Limits e custos

3. **Business Metrics**
   - Active Users: Usuários ativos
   - Trade Volume: Volume negociado
   - Feature Usage: Utilização de funcionalidades
   - User Satisfaction: Feedback e ratings

### Dashboard de Analytics

O sistema inclui analytics avançados:

- **Performance Charts**: Gráficos de retorno
- **Risk Analysis**: Métricas de risco detalhadas
- **Comparative Analysis**: Benchmark vs. mercado
- **Prediction Accuracy**: Taxa de acerto das previsões

## 🔧 Manutenção e Troubleshooting

### Comandos Úteis

```bash
# Verificar status do sistema
python ai_agent_monitor.py --status

# Restart todos os serviços
node quick-start.js --restart

# Backup completo
python backup_system.py --full

# Logs em tempo real
tail -f logs/ai_agent.log
tail -f logs/backend.log
```

### Problemas Comuns

1. **Erro de Conexão com Binance**
   ```bash
   # Verificar chaves API
   python -c "from binance import Client; print('OK')"
   
   # Testar conectividade
   curl https://testnet.binance.vision/api/v3/ping
   ```

2. **Frontend não Carrega**
   ```bash
   # Verificar backend
   curl http://localhost:5000/api/status
   
   # Restart frontend
   node quick-start.js --frontend-only
   ```

3. **AI Agent Parado**
   ```bash
   # Verificar logs
   python ai_agent_monitor.py --logs
   
   # Restart agent
   python ai_trading_agent.py --restart
   ```

### Logs e Debugging

- **Backend Logs**: `logs/backend.log`
- **AI Agent Logs**: `logs/ai_agent.log`
- **Trading Logs**: `logs/trades.log`
- **Error Logs**: `logs/errors.log`

## 📚 API Reference

### Endpoints Principais

#### Trading API
```http
GET /api/status              # Status do sistema
GET /api/market_data/{symbol} # Dados de mercado
GET /api/trades              # Histórico de trades
POST /api/trade              # Executar trade manual
GET /api/balance             # Saldo da conta
```

#### AI Agent API
```http
GET /api/agent/status        # Status do agent
GET /api/agent/config        # Configuração atual
POST /api/agent/config       # Atualizar configuração
POST /api/agent/start        # Iniciar agent
POST /api/agent/stop         # Parar agent
GET /api/agent/performance   # Métricas de performance
```

#### Social Sentiment API
```http
GET /api/sentiment/{symbol}  # Sentiment de um símbolo
GET /api/memecoins          # Lista de memecoins
GET /api/social/trending    # Trending topics
GET /api/watchlist          # Watchlist personalizada
POST /api/watchlist         # Adicionar à watchlist
```

### Exemplo de Uso da API

```javascript
// Verificar status do sistema
const status = await fetch('/api/status').then(r => r.json());

// Configurar AI Agent
await fetch('/api/agent/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        symbol: 'DOGEUSDT',
        investment_amount: 25.0,
        risk_level: 'moderate'
    })
});

// Obter dados de mercado
const marketData = await fetch('/api/market_data/DOGEUSDT')
    .then(r => r.json());
```

## 🎯 Roadmap e Futuras Melhorias

### Versão 2.0 (Próximos 3 meses)

- **Multi-Exchange Support**: Binance, Coinbase, KuCoin
- **Advanced ML Models**: Deep Learning para previsões
- **Portfolio Management**: Gestão de múltiplos ativos
- **Social Trading**: Copy trading e sinais

### Versão 3.0 (6 meses)

- **DeFi Integration**: DEX trading e yield farming
- **NFT Analytics**: Análise de mercado NFT
- **Mobile App**: App nativo iOS/Android
- **Institutional Features**: API para instituições

### Funcionalidades Avançadas

- **Backtesting Engine**: Teste de estratégias históricas
- **Strategy Builder**: GUI para criar estratégias
- **Multi-User Support**: Contas e permissões
- **Webhook Integration**: Alertas para Discord/Slack

## 📞 Suporte e Comunidade

### Documentação
- **GitHub Wiki**: Documentação técnica completa
- **Video Tutorials**: Tutoriais passo a passo
- **API Docs**: Swagger/OpenAPI documentation
- **FAQ**: Perguntas frequentes

### Comunidade
- **Discord Server**: Chat em tempo real
- **Telegram Group**: Updates e discussões
- **Reddit Community**: r/MoCoVeTrading
- **YouTube Channel**: Tutoriais e updates

### Suporte Técnico
- **GitHub Issues**: Bug reports e feature requests
- **Email Support**: support@mocove.trading
- **Live Chat**: Suporte em tempo real
- **Consultoria**: Consultoria personalizada

## 📄 Licença e Termos

### Licença MIT

Este projeto está licenciado sob a Licença MIT. Você pode usar, modificar e distribuir o código livremente, mantendo os créditos originais.

### Disclaimer

**⚠️ IMPORTANTE**: Trading de criptomoedas envolve riscos significativos. Este sistema é fornecido para fins educacionais e de pesquisa. Os usuários são responsáveis por suas próprias decisões de investimento. Sempre teste em ambiente testnet antes de usar dinheiro real.

### Termos de Uso

- Use apenas com fundos que você pode perder
- Teste extensivamente antes de produção
- Monitore constantemente o sistema
- Mantenha backups regulares
- Respeite os limites das APIs
- Contribua com melhorias para a comunidade

---

## 🙏 Agradecimentos

Desenvolvido com ❤️ para a comunidade de trading automatizado. Contribuições são bem-vindas!

**Versão**: 1.0.0  
**Última Atualização**: ${new Date().toISOString().split('T')[0]}  
**Autor**: MoCoVe Development Team  
**Website**: https://mocove-ai-trading.surge.sh
