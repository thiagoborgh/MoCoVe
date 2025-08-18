# 📊 Sistema de Monitoramento de Performance do Portfólio

## Visão Geral

O sistema de monitoramento de performance foi implementado para acompanhar a desvalorização/valorização das criptomoedas baseado no **preço real de compra**, oferecendo insights muito mais precisos que apenas monitorar variações de 24h.

## 🎯 Funcionalidades Principais

### 1. Monitoramento Baseado no Preço de Compra
- **Problema resolvido**: Anteriormente só tínhamos variação de 24h, que não refletia o real P&L do investidor
- **Solução**: Calcula performance baseada no preço exato da compra vs preço atual
- **Resultado**: Performance real das posições em tempo real

### 2. Alertas Inteligentes
- **Stop Loss**: Alerta quando posição cai mais de 10%
- **Take Profit**: Alerta quando posição sobe mais de 15%
- **Recomendações**: Sistema sugere VENDER ou CONSIDERAR VENDA

### 3. Categorização de Performance
- 🚀 **Excelente**: +10% ou mais
- 📈 **Boa**: +5% a +10%
- ✅ **Positiva**: 0% a +5%
- ⚠️ **Pequena Perda**: 0% a -5%
- 📉 **Perda**: -5% a -10%
- 🚨 **Perda Pesada**: -10% ou menos

## 🔧 Componentes do Sistema

### 1. PortfolioMonitor (portfolio_monitor.py)
```python
# Classe principal que gerencia o portfólio
monitor = PortfolioMonitor()

# Adicionar posição manualmente
monitor.add_position("DOGEUSDT", 0.08, 125.0, "2025-08-18T10:00:00")

# Obter performance
portfolio = monitor.get_portfolio_performance()
print(f"P&L Total: ${portfolio['total_pnl']:.2f}")

# Verificar alertas
alerts = monitor.check_alerts()
```

### 2. Integração com Agente de Trading
```python
# O agente automaticamente:
# - Adiciona posições ao comprar
# - Remove posições ao vender
# - Verifica alertas a cada 5 ciclos
# - Mostra performance a cada 10 ciclos
```

### 3. API Backend
```
GET /api/portfolio/performance
```
Retorna:
```json
{
    "success": true,
    "portfolio": {
        "total_positions": 3,
        "total_invested": 25.50,
        "total_current_value": 27.82,
        "total_pnl": 2.32,
        "portfolio_performance_pct": 9.10,
        "positions": [...]
    },
    "alerts": [...]
}
```

### 4. Dashboard Integrado
- **Visão Geral**: Total investido, valor atual, P&L, performance %
- **Posições**: Lista com performance individual e indicadores visuais
- **Alertas**: Alertas ativos com recomendações
- **Atualização**: Automática a cada 15 segundos

## 🚀 Como Usar

### Uso Automático (Recomendado)
1. **Inicie o backend**: `python backend/app.py`
2. **Inicie o agente**: `python ai_trading_agent_robust.py`
3. **Abra o dashboard**: `frontend/dashboard_pro.html`

O sistema funcionará automaticamente:
- Compras são adicionadas ao portfólio
- Vendas removem posições
- Performance é calculada em tempo real
- Alertas são emitidos automaticamente

### Uso Manual
```bash
# Testar o sistema
python test_portfolio_monitor.py

# Gerenciar posições manualmente
python portfolio_monitor.py
```

### Gerenciamento de Moedas Compradas
```bash
# Gerenciar lista de moedas já compradas
python manage_purchased_coins.py
```

## 📊 Exemplos de Output

### Console do Agente
```
📊 === PERFORMANCE DO PORTFÓLIO ===
📊 Posições ativas: 3
📊 Total investido: $25.50
📊 Valor atual: $27.82
📊 P&L Total: $+2.32 (+9.10%)

📊 === PERFORMANCE POR POSIÇÃO ===
📊 🚀 DOGEUSDT: +12.50% | $+1.25 | 1 dias
📊 📈 BTCUSDT: +8.20% | $+0.82 | 2 dias
📊 ✅ ETHUSDT: +2.50% | $+0.25 | 1 dias

🎯 ALERTA TAKE PROFIT: DOGEUSDT subiu 12.50% - CONSIDERAR VENDA
```

### Dashboard
```
Portfolio Performance
├── Total Investido: $25.50
├── Valor Atual: $27.82
├── P&L Total: $+2.32
└── Performance: +9.10%

Posições Ativas
├── 🚀 DOGEUSDT: +12.50% | $+1.25 | 1d
├── 📈 BTCUSDT: +8.20% | $+0.82 | 2d
└── ✅ ETHUSDT: +2.50% | $+0.25 | 1d

⚠️ Alertas Ativos
└── 🎯 DOGEUSDT: +12.50% - CONSIDERAR VENDA
```

## ⚙️ Configuração

### Limites de Alerta (portfolio_monitor.py)
```python
self.stop_loss_threshold = -10.0   # -10%
self.take_profit_threshold = 15.0  # +15%
```

### Arquivo de Posições
- **Local**: `portfolio_positions.json`
- **Backup automático**: Sim
- **Carregamento**: Automático do histórico de trades

## 🔄 Fluxo Completo

1. **Agente analisa mercado** → Encontra oportunidade de compra
2. **Executa compra na Binance** → Trade real executado
3. **Salva no banco de dados** → Histórico permanente
4. **Adiciona ao Portfolio Monitor** → Tracking de performance
5. **Monitora em tempo real** → Cálculo contínuo de P&L
6. **Emite alertas** → Stop loss / Take profit
7. **Mostra no dashboard** → Visualização em tempo real

## 🎛️ Controles Disponíveis

### Via Script
```bash
# Mostrar performance atual
python -c "from portfolio_monitor import PortfolioMonitor; m=PortfolioMonitor(); m.get_portfolio_performance()"

# Reset de posições
python -c "from portfolio_monitor import PortfolioMonitor; m=PortfolioMonitor(); m.positions.clear(); m.save_positions()"
```

### Via Agente
```python
agent = SimpleAgent()
agent.show_portfolio_performance()  # Mostrar performance
agent.check_portfolio_alerts()      # Verificar alertas
```

## 🎯 Benefícios

1. **Precisão**: Performance baseada no preço real de compra
2. **Tempo Real**: Atualização contínua durante trading
3. **Alertas Proativos**: Nunca perca oportunidades de lucro ou pare perdas
4. **Integração Completa**: Funciona automaticamente com o agente
5. **Visualização Clara**: Dashboard com indicadores visuais intuitivos
6. **Histórico Persistente**: Dados mantidos entre execuções

## 🔍 Monitoramento

O sistema mantém logs detalhados de todas as operações:
- Adição/remoção de posições
- Cálculos de performance
- Alertas emitidos
- Erros e problemas

Para debugging, verifique:
- Console do agente de trading
- Logs do Portfolio Monitor
- Response da API `/api/portfolio/performance`

## 📈 Próximos Passos

O sistema está completo e funcional. Possíveis melhorias futuras:
- Gráficos de performance histórica
- Mais tipos de alertas (RSI, volume, etc.)
- Exportação de relatórios
- Integração com mais exchanges