#!/usr/bin/env python3
"""
Configuração do AI Trading Agent
Parâmetros ajustáveis para otimizar o trading
"""

# Configurações de Confiança
MIN_CONFIDENCE = 0.4  # Reduzido de 0.7 para 0.4 (mais permissivo)
MAX_DAILY_TRADES = 20  # Aumentado de 10 para 20
MIN_TRADE_INTERVAL = 180  # Reduzido de 300s para 180s (3 minutos)

# Configurações de Risco
MAX_POSITION_SIZE = 25.0  # Reduzido de 50 para 25 USDT (mais conservador)
STOP_LOSS_PCT = 0.015  # 1.5% stop loss
TAKE_PROFIT_PCT = 0.025  # 2.5% take profit

# Configurações de Análise
RSI_OVERSOLD = 35  # Mais permissivo (era 30)
RSI_OVERBOUGHT = 65  # Mais permissivo (era 70)
VOLATILITY_THRESHOLD = 3.0  # Mais permissivo (era 5.0)

# Configurações de Dados
MIN_PRICE_HISTORY = 10  # Reduzido de 20 para 10 pontos
MONITORING_INTERVAL = 20  # Reduzido de 30 para 20 segundos

# Configurações de Trading
SYMBOLS = ['DOGEUSDT', 'SHIBUSDT', 'PEPEUSDT']
DEFAULT_SYMBOL = 'DOGEUSDT'

# Pesos dos Indicadores (para ajuste fino)
WEIGHTS = {
    'sma_crossover': 2.5,  # Aumentado
    'ema_crossover': 2.0,  # Aumentado
    'rsi': 1.5,
    'bollinger': 1.5,
    'price_trend': 2.0,  # Aumentado
    'volume': 1.0
}

# Modo de teste
TEST_MODE = False  # MODO REAL - executa trades reais na Binance (MESCLADO)
VERBOSE_LOGGING = True
