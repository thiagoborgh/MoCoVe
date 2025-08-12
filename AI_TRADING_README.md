# 🤖 MoCoVe AI Trading Agent

## 📖 Visão Geral

O **MoCoVe AI Trading Agent** é um sistema de trading automatizado baseado em inteligência artificial que monitora o mercado de criptomoedas 24/7 e executa trades automaticamente baseado em análise técnica avançada e machine learning.

## ✨ Características Principais

### 🧠 Inteligência Artificial
- **Análise Multi-Indicador**: Combina múltiplos indicadores técnicos
- **Machine Learning**: Aprende com padrões históricos
- **Confiança Calculada**: Cada sinal tem um score de confiança
- **Adaptação Dinâmica**: Ajusta estratégias baseado em volatilidade

### 📊 Indicadores Técnicos
- **Médias Móveis**: SMA e EMA para tendências
- **RSI**: Identificação de sobrecompra/sobrevenda
- **Bandas de Bollinger**: Detecção de extremos de preço
- **Análise de Volume**: Confirmação de sinais
- **Volatilidade**: Filtro de risco

### 🛡️ Gerenciamento de Risco
- **Limites de Trade**: Valor máximo por operação
- **Stop Loss/Take Profit**: Proteção automática
- **Limite Diário**: Máximo de trades por dia
- **Intervalo Entre Trades**: Evita overtrading
- **Níveis de Risco**: Conservative, Moderate, Aggressive

### 📈 Estratégias Implementadas
1. **Crossover de Médias**: Sinais de entrada/saída
2. **Mean Reversion**: Reversão à média
3. **Trend Following**: Seguimento de tendência
4. **Breakout Detection**: Detecção de rompimentos
5. **Volatility Trading**: Aproveitamento de volatilidade

## 🚀 Como Usar

### 1. Configuração Inicial
```bash
# Iniciar configurador
python ai_agent_config.py
```

### 2. Iniciar Sistema Completo
```bash
# Launcher principal
python start_ai_trading.py
```

### 3. Monitoramento
```bash
# Dashboard em tempo real
python ai_agent_monitor.py
```

### 4. Agente Standalone
```bash
# Apenas o agente
python ai_trading_agent.py
```

## ⚙️ Configurações

### Níveis de Risco

#### 🟢 Conservative (Recomendado para iniciantes)
- Confiança mínima: 80%
- Valor máximo por trade: $25
- Máximo 5 trades/dia
- Stop loss: 1.5%
- Take profit: 2%

#### 🟡 Moderate (Balanceado)
- Confiança mínima: 70%
- Valor máximo por trade: $50
- Máximo 10 trades/dia
- Stop loss: 2%
- Take profit: 3%

#### 🔴 Aggressive (Apenas usuários experientes)
- Confiança mínima: 60%
- Valor máximo por trade: $100
- Máximo 20 trades/dia
- Stop loss: 3%
- Take profit: 5%

### Configurações Personalizadas
```json
{
  "trading_enabled": true,
  "symbol": "DOGEUSDT",
  "monitoring_interval": 30,
  "min_confidence": 0.7,
  "max_position_size": 50.0,
  "max_daily_trades": 10,
  "stop_loss_pct": 0.02,
  "take_profit_pct": 0.03
}
```

## 📊 Como Funciona

### 1. Coleta de Dados
- Preços em tempo real via API Binance
- Histórico de preços (últimas 50 velas)
- Volume e volatilidade
- Dados de mercado 24h

### 2. Análise Técnica
```python
# Exemplo de análise
indicators = {
    'sma_short': 10_period_average,
    'sma_long': 20_period_average,
    'rsi': relative_strength_index,
    'bollinger_bands': upper_middle_lower,
    'volatility': price_volatility
}
```

### 3. Geração de Sinais
- **Buy Signal**: Múltiplos indicadores altistas
- **Sell Signal**: Múltiplos indicadores baixistas
- **Hold**: Sinais mistos ou baixa confiança

### 4. Execução de Trades
- Verificação de limites de risco
- Cálculo do valor do trade
- Execução via API
- Logging detalhado

## 🛡️ Segurança

### ⚠️ Avisos Importantes
- **TRADING REAL**: Opera com dinheiro real
- **RISCO DE PERDA**: Mercados são voláteis
- **MONITORAMENTO**: Sempre supervisione o agente
- **LIMITES**: Configure limites apropriados
- **TESTES**: Comece com valores pequenos

### 🔒 Medidas de Proteção
- Limites máximos por trade
- Limite de perda diária
- Intervalo mínimo entre trades
- Validação de saldos
- Logs detalhados de todas operações

## 📋 Logs e Monitoramento

### Logs do Agente
```
2025-08-08 14:30:15 - INFO - 🤖 SINAL: BUY | DOGEUSDT
2025-08-08 14:30:15 - INFO -    💰 Preço: $0.224150
2025-08-08 14:30:15 - INFO -    📊 Confiança: 0.75
2025-08-08 14:30:15 - INFO -    💵 Valor: $37.50
2025-08-08 14:30:15 - INFO -    🎯 Razão: Crossover altista das médias; RSI oversold
2025-08-08 14:30:15 - INFO -    ⚡ Executado: ✅ SIM
```

### Dashboard em Tempo Real
- Status do sistema
- Preço atual e variação
- Trades do dia
- P&L estimado
- Logs recentes

## 🔧 Solução de Problemas

### Problemas Comuns

#### ❌ "Failed to fetch"
- Verificar se backend está rodando
- Conferir conectividade com Binance

#### ❌ "Insufficient balance"
- Verificar saldos na conta
- Reduzir valor do trade

#### ❌ "Confidence too low"
- Mercado sem sinais claros
- Aguardar melhores oportunidades

### Reinicialização
```bash
# Parar tudo
Ctrl+C

# Reiniciar sistema
python start_ai_trading.py
```

## 📈 Estratégias Avançadas

### Otimização de Parâmetros
- Backtesting com dados históricos
- Ajuste de períodos de médias móveis
- Calibração de limites RSI
- Otimização de stop loss/take profit

### Múltiplos Símbolos
```python
# Configurar para múltiplas moedas
symbols = ["DOGEUSDT", "BTCUSDT", "ETHUSDT"]
```

### Análise de Sentimento
- Integração com análise de sentimento
- Filtros de notícias
- Análise de redes sociais

## 📞 Suporte

### Em Caso de Emergência
1. **Parar Agente**: Ctrl+C no terminal
2. **Acesso Manual**: https://binance.com
3. **Verificar Posições**: Interface web Binance
4. **Fechar Posições**: Manualmente se necessário

### Contatos
- 📧 Logs detalhados em `ai_trading_agent.log`
- 🔍 Monitor em tempo real disponível
- 📊 Dashboard web em `http://localhost:5000`

## 🎯 Roadmap

### Próximas Funcionalidades
- [ ] Backtesting automático
- [ ] Análise de sentimento
- [ ] Trading de múltiplos pares
- [ ] Interface web para controle
- [ ] Alertas por email/telegram
- [ ] Machine learning avançado

### Melhorias Planejadas
- [ ] Otimização automática de parâmetros
- [ ] Estratégias de arbitragem
- [ ] Copy trading
- [ ] Paper trading para testes

---

## ⚖️ Disclaimer

**O trading de criptomoedas envolve riscos significativos. Este software é fornecido "como está" sem garantias. Você é responsável por todas as decisões de trading e perdas potenciais. Sempre faça sua própria pesquisa e nunca invista mais do que pode perder.**

---

🤖 **MoCoVe AI Trading Agent** - Transformando análise técnica em resultados automatizados!
