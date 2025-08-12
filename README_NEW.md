# 🤖 MoCoVe AI Trading System

> **Sistema Completo de Trading Automatizado com Inteligência Artificial para Criptomoedas**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/thiagoborgh/MoCoVe)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![Node.js](https://img.shields.io/badge/node.js-16+-green.svg)](https://nodejs.org)
[![Live Demo](https://img.shields.io/badge/demo-live-orange.svg)](https://mocove-ai-trading.surge.sh)

## 🎯 Visão Geral

O **MoCoVe** é um sistema revolucionário de trading automatizado que combina Inteligência Artificial, análise técnica avançada e monitoramento de sentimento das redes sociais para maximizar oportunidades de trading em criptomoedas, especialmente memecoins.

### ✨ Principais Funcionalidades

- 🤖 **AI Trading Agent** com análise técnica completa (SMA, EMA, RSI, Bollinger Bands)
- 📊 **Dashboard Moderno** com interface React responsiva e tempo real
- 🐦 **Análise de Sentimento** de Twitter, Reddit e Telegram
- 💰 **Gestão de Risco** avançada com stop-loss dinâmico
- 📱 **PWA Ready** - instalável como aplicativo mobile
- 🚀 **Deploy Automático** para Surge.sh
- 🔄 **Monitoramento 24/7** com alertas em tempo real

## 🚀 Quick Start

### Inicialização em 3 Passos

```bash
# 1. Clonar o repositório
git clone https://github.com/thiagoborgh/MoCoVe.git
cd MoCoVe

# 2. Configuração interativa
npm run config

# 3. Iniciar sistema completo
npm start
```

### Acesso ao Dashboard

- **Local**: http://localhost:3000
- **Demo Online**: https://mocove-ai-trading.surge.sh

## 📋 Pré-requisitos

- **Python 3.9+**
- **Node.js 16+**
- **Conta Binance** (recomendado usar Testnet)
- **Chaves API Binance**

## ⚙️ Configuração

### 1. Variáveis de Ambiente

Crie um arquivo `.env`:

```env
# Binance API (use Testnet para testes)
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
BINANCE_TESTNET=true

# Configurações padrão
DEFAULT_SYMBOL=DOGEUSDT
INVESTMENT_AMOUNT=25.0
RISK_LEVEL=conservative
```

### 2. Configuração do AI Agent

```bash
# Configuração interativa
npm run ai-config

# Monitoramento em tempo real
npm run ai-monitor
```

## 🤖 AI Trading Agent

### Análise Técnica Avançada

- **SMA/EMA**: Análise de tendências
- **RSI**: Níveis de sobrecompra/sobrevenda  
- **Bollinger Bands**: Volatilidade e pontos de entrada
- **MACD**: Momentum e sinais de cruzamento
- **Machine Learning**: Previsões baseadas em histórico

### Modos de Risco

| Modo | Confiança Mín. | Stop Loss | Take Profit | Trades/Dia |
|------|----------------|-----------|-------------|------------|
| **Conservative** | 80% | 3% | 6% | 3 |
| **Moderate** | 70% | 5% | 10% | 5 |
| **Aggressive** | 60% | 7% | 15% | 8 |

## 📊 Dashboard Features

### 🎛️ Overview em Tempo Real
- Preço atual e variação 24h
- Volume de trading e liquidez
- Status do AI Agent
- Performance do portfolio

### 📈 Gestão de Trades
- Histórico completo de trades
- Análise de performance (ROI, Sharpe ratio)
- Filtros avançados por período/símbolo
- Exportação para CSV/PDF

### 🪙 Monitoramento de Memecoins
- Top 20 memecoins por volume/sentimento
- Scores de sentimento das redes sociais
- Alertas de oportunidades
- Watchlist personalizada

### ⚙️ Configuração do Agent
- Parâmetros de trading em tempo real
- Configuração de indicadores técnicos
- Sistema de notificações
- Backup/restore de configurações

## 🐦 Análise de Sentimento

### Fontes Monitoradas

- **Twitter**: Hashtags relevantes e influenciadores
- **Reddit**: Subreddits especializados (r/cryptocurrency, r/dogecoin)
- **Telegram**: Canais públicos de trading

### Algoritmo de Scoring

O sistema agrega sentimentos com pesos:
- Twitter: 40% (mais reativo)
- Reddit: 40% (mais fundamentado)  
- Telegram: 20% (suporte adicional)

## 🛡️ Segurança e Gestão de Risco

### Medidas de Proteção

- ✅ **Proteção de API Keys** com variáveis de ambiente
- ✅ **Limites de Trading** diários e por posição
- ✅ **Stop Loss Obrigatório** em todos os trades
- ✅ **Monitoramento de Anomalias** em tempo real
- ✅ **Emergency Stop** para situações críticas

### Gestão de Risco Avançada

- Limite de perda diária: 5% do capital
- Tamanho máximo por posição: 10%
- Máximo de posições abertas: 3
- Diversificação automática de símbolos

## 📱 Scripts Disponíveis

### Comandos Principais

```bash
npm start          # Iniciar sistema completo
npm run config     # Configuração interativa
npm run deploy     # Deploy para Surge.sh
npm run ai-start   # Iniciar apenas AI Agent
npm run status     # Status do sistema
npm run logs       # Visualizar logs em tempo real
```

### Desenvolvimento

```bash
npm run dev        # Modo desenvolvimento
npm run test       # Executar testes
npm run lint       # Verificar código
npm run docs       # Abrir documentação
npm run backup     # Backup completo do sistema
```

### Deploy e Produção

```bash
npm run build      # Build para produção
npm run serve      # Servidor estático
npm run tunnel     # Túnel ngrok para testes
npm run docker:up  # Executar com Docker
```

## 🚀 Deploy no Surge.sh

### Deploy Automático

```bash
npm run deploy
```

O sistema será publicado em: `https://mocove-ai-trading.surge.sh`

### Configuração de Domínio Customizado

```bash
# Editar CNAME no build
echo "meudominio.com" > dist/CNAME
surge dist/ meudominio.com
```

## 📊 API Reference

### Endpoints Principais

```http
# Status e Informações
GET /api/status              # Status do sistema
GET /api/market_data/{symbol} # Dados de mercado
GET /api/balance             # Saldo da conta

# Trading
GET /api/trades              # Histórico de trades
POST /api/trade              # Executar trade manual

# AI Agent
GET /api/agent/status        # Status do agent
GET /api/agent/config        # Configuração atual
POST /api/agent/config       # Atualizar configuração
GET /api/agent/performance   # Métricas de performance

# Social Sentiment
GET /api/sentiment/{symbol}  # Sentiment de um símbolo
GET /api/memecoins          # Lista de memecoins
GET /api/watchlist          # Watchlist personalizada
```

## 📈 Performance e Métricas

### Métricas Acompanhadas

- **Total Return**: ROI acumulado
- **Sharpe Ratio**: Retorno ajustado ao risco
- **Maximum Drawdown**: Maior perda consecutiva
- **Win Rate**: Percentual de trades positivos
- **Prediction Accuracy**: Taxa de acerto das previsões IA

### Benchmark

O sistema mantém métricas comparativas com:
- Performance do Bitcoin
- Índices de mercado crypto
- Estratégias buy-and-hold
- Outros bots de trading

## 🔧 Troubleshooting

### Problemas Comuns

#### Erro de Conexão Binance
```bash
# Verificar chaves API
python -c "from binance import Client; print('OK')"

# Testar conectividade
curl https://testnet.binance.vision/api/v3/ping
```

#### Frontend não Carrega
```bash
# Verificar backend
curl http://localhost:5000/api/status

# Restart completo
npm start
```

#### AI Agent Parado
```bash
# Verificar logs
npm run logs

# Restart apenas o agent
npm run ai-start
```

## 📚 Documentação Completa

Para documentação técnica detalhada, consulte:
- [**DOCUMENTATION.md**](DOCUMENTATION.md) - Documentação completa
- [**AI_TRADING_README.md**](AI_TRADING_README.md) - Guia do AI Agent
- [**API Documentation**](https://mocove-ai-trading.surge.sh/docs) - Referência da API

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Roadmap

- [ ] Multi-exchange support (Coinbase, KuCoin)
- [ ] Advanced ML models (Deep Learning)
- [ ] Portfolio management multi-assets
- [ ] Mobile app nativo
- [ ] DeFi integration

## 📞 Suporte

### Comunidade
- **Discord**: [MoCoVe Trading Community](https://discord.gg/mocove)
- **Telegram**: [@MoCoVeTrading](https://t.me/mocovetrading)
- **Reddit**: [r/MoCoVeTrading](https://reddit.com/r/mocovetrading)

### Suporte Técnico
- **GitHub Issues**: Para bugs e feature requests
- **Email**: support@mocove.trading
- **Documentação**: Consulte DOCUMENTATION.md

## ⚠️ Disclaimer

**IMPORTANTE**: Trading de criptomoedas envolve riscos significativos. Este sistema é fornecido para fins educacionais e de pesquisa. Os usuários são responsáveis por suas próprias decisões de investimento.

### Recomendações de Segurança

- ✅ **Sempre teste em Testnet primeiro**
- ✅ **Use apenas fundos que pode perder**
- ✅ **Monitore constantemente o sistema**
- ✅ **Mantenha backups regulares**
- ✅ **Não compartilhe suas chaves API**

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - consulte o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **Binance API** pela infraestrutura de trading
- **React Team** pelo framework frontend
- **Flask Team** pelo framework backend
- **Comunidade Open Source** pelas bibliotecas utilizadas

---

<div align="center">

**Desenvolvido com ❤️ para a comunidade de trading automatizado**

[![GitHub stars](https://img.shields.io/github/stars/thiagoborgh/MoCoVe.svg?style=social&label=Star)](https://github.com/thiagoborgh/MoCoVe)
[![GitHub forks](https://img.shields.io/github/forks/thiagoborgh/MoCoVe.svg?style=social&label=Fork)](https://github.com/thiagoborgh/MoCoVe/fork)
[![GitHub watchers](https://img.shields.io/github/watchers/thiagoborgh/MoCoVe.svg?style=social&label=Watch)](https://github.com/thiagoborgh/MoCoVe)

[🚀 **Acessar Demo Live**](https://mocove-ai-trading.surge.sh) • [📖 **Documentação**](DOCUMENTATION.md) • [🤝 **Contribuir**](CONTRIBUTING.md)

</div>
