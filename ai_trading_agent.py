#!/usr/bin/env python3
"""
MoCoVe AI Trading Agent - Versão Mesclada e Otimizada
Agente de IA com os melhores recursos dos dois agentes anteriores
Sem modo teste - TRADING REAL ATIVO
"""

import asyncio
import time
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
import threading
import signal
import sys

# Importar configurações otimizadas
try:
    from ai_trading_config import *
except ImportError:
    # Configurações otimizadas padrão
    MIN_CONFIDENCE = 0.4  # Mais permissivo que 0.7
    MAX_DAILY_TRADES = 20
    MIN_TRADE_INTERVAL = 180  # 3 minutos
    MAX_POSITION_SIZE = 25.0  # Mais conservador
    STOP_LOSS_PCT = 0.015  # 1.5%
    TAKE_PROFIT_PCT = 0.025  # 2.5%
    RSI_OVERSOLD = 35  # Mais permissivo
    RSI_OVERBOUGHT = 65  # Mais permissivo
    VOLATILITY_THRESHOLD = 3.0
    MIN_PRICE_HISTORY = 10  # Menos restritivo
    MONITORING_INTERVAL = 20  # Mais frequente
    DEFAULT_SYMBOL = 'DOGEUSDT'
    TEST_MODE = False  # MODO REAL - SEM TESTES
    VERBOSE_LOGGING = True

# Configuração de logging sem emojis para compatibilidade Windows
logging.basicConfig(
    level=logging.DEBUG if VERBOSE_LOGGING else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_trading_agent.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """Sinal de trading gerado pelo agente"""
    action: str  # 'buy', 'sell', 'hold'
    symbol: str
    confidence: float  # 0.0 a 1.0
    reason: str
    price: float
    amount: float
    timestamp: datetime
    indicators: Dict

@dataclass
class MarketState:
    """Estado atual do mercado"""
    symbol: str
    current_price: float
    price_history: List[float]
    volume_24h: float
    change_24h: float
    volatility: float
    timestamp: datetime

class TechnicalAnalyzer:
    """Analisador técnico para indicadores de trading"""
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> float:
        """Média móvel simples"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        return sum(prices[-period:]) / period
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """Média móvel exponencial"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Índice de Força Relativa"""
        if len(prices) < period + 1:
            return 50.0
        
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [max(0, change) for change in changes]
        losses = [max(0, -change) for change in changes]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20) -> Tuple[float, float, float]:
        """Bandas de Bollinger"""
        if len(prices) < period:
            current_price = prices[-1] if prices else 0
            return current_price, current_price, current_price
        
        sma = TechnicalAnalyzer.calculate_sma(prices, period)
        variance = sum([(p - sma) ** 2 for p in prices[-period:]]) / period
        std_dev = variance ** 0.5
        
        upper_band = sma + (2 * std_dev)
        lower_band = sma - (2 * std_dev)
        
        return upper_band, sma, lower_band

class OptimizedAITradingStrategy:
    """Estratégia de trading otimizada com melhores parâmetros"""
    
    def __init__(self):
        self.min_confidence = MIN_CONFIDENCE  # 0.4 - mais permissivo
        self.max_daily_trades = MAX_DAILY_TRADES  # 20 trades
        self.daily_trade_count = 0
        self.last_trade_time = None
        self.min_trade_interval = MIN_TRADE_INTERVAL  # 3 minutos
        
        # Parâmetros de risco otimizados
        self.max_position_size = MAX_POSITION_SIZE  # $25
        self.stop_loss_pct = STOP_LOSS_PCT  # 1.5%
        self.take_profit_pct = TAKE_PROFIT_PCT  # 2.5%
        
        logger.info(f"Estrategia otimizada inicializada - Confianca min: {self.min_confidence}")
        
    def analyze_market(self, market_state: MarketState) -> TradingSignal:
        """Análise otimizada do mercado com períodos menores"""
        prices = market_state.price_history
        current_price = market_state.current_price
        
        # Verificação mais permissiva de dados
        if len(prices) < MIN_PRICE_HISTORY:
            logger.warning(f"Dados insuficientes: {len(prices)} < {MIN_PRICE_HISTORY}")
            return TradingSignal(
                action='hold',
                symbol=market_state.symbol,
                confidence=0.0,
                reason=f'Dados insuficientes ({len(prices)} pontos)',
                price=current_price,
                amount=0.0,
                timestamp=datetime.now(),
                indicators={}
            )
        
        # Calcular indicadores com períodos otimizados (menores)
        sma_short = TechnicalAnalyzer.calculate_sma(prices, 5)  # Era 10
        sma_long = TechnicalAnalyzer.calculate_sma(prices, 10)  # Era 20
        ema_short = TechnicalAnalyzer.calculate_ema(prices, 6)  # Era 12
        ema_long = TechnicalAnalyzer.calculate_ema(prices, 12)  # Era 26
        rsi = TechnicalAnalyzer.calculate_rsi(prices, 10)  # Era 14
        bb_upper, bb_middle, bb_lower = TechnicalAnalyzer.calculate_bollinger_bands(prices, 15)  # Era 20
        
        indicators = {
            'sma_short': sma_short,
            'sma_long': sma_long,
            'ema_short': ema_short,
            'ema_long': ema_long,
            'rsi': rsi,
            'bb_upper': bb_upper,
            'bb_middle': bb_middle,
            'bb_lower': bb_lower,
            'volatility': market_state.volatility,
            'volume_24h': market_state.volume_24h,
            'change_24h': market_state.change_24h,
            'current_price': current_price
        }
        
        # Sistema de pontuação otimizado
        buy_score = 0.0
        sell_score = 0.0
        total_weight = 0.0
        reasons = []
        
        # 1. Crossover de médias móveis (peso alto)
        if sma_short > sma_long and ema_short > ema_long:
            weight = 3.0
            buy_score += weight
            total_weight += weight
            reasons.append("Crossover altista das medias")
        elif sma_short < sma_long and ema_short < ema_long:
            weight = 3.0
            sell_score += weight
            total_weight += weight
            reasons.append("Crossover baixista das medias")
        else:
            total_weight += 3.0
        
        # 2. RSI com limites otimizados
        if rsi < RSI_OVERSOLD:  # 35 em vez de 30
            weight = 2.0
            buy_score += weight
            total_weight += weight
            reasons.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > RSI_OVERBOUGHT:  # 65 em vez de 70
            weight = 2.0
            sell_score += weight
            total_weight += weight
            reasons.append(f"RSI overbought ({rsi:.1f})")
        else:
            total_weight += 2.0
            reasons.append(f"RSI neutro ({rsi:.1f})")
        
        # 3. Bandas de Bollinger
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
        if bb_position <= 0.2:  # Próximo da banda inferior
            weight = 2.0
            buy_score += weight
            total_weight += weight
            reasons.append("Preco proximo a banda inferior")
        elif bb_position >= 0.8:  # Próximo da banda superior
            weight = 2.0
            sell_score += weight
            total_weight += weight
            reasons.append("Preco proximo a banda superior")
        else:
            total_weight += 2.0
            reasons.append(f"Preco no meio das bandas ({bb_position:.2f})")
        
        # 4. Tendência de preço recente
        if len(prices) >= 3:
            recent_trend = (current_price - prices[-3]) / prices[-3] * 100
            if recent_trend > 0.5:  # Subindo mais de 0.5%
                weight = 2.0
                buy_score += weight
                total_weight += weight
                reasons.append(f"Tendencia altista ({recent_trend:.2f}%)")
            elif recent_trend < -0.5:  # Caindo mais de 0.5%
                weight = 2.0
                sell_score += weight
                total_weight += weight
                reasons.append(f"Tendencia baixista ({recent_trend:.2f}%)")
            else:
                total_weight += 2.0
                reasons.append(f"Tendencia lateral ({recent_trend:.2f}%)")
        
        # 5. Volume e mudança 24h
        if market_state.change_24h > 1:  # Subindo mais de 1% em 24h
            weight = 1.0
            buy_score += weight
            total_weight += weight
            reasons.append(f"Alta 24h ({market_state.change_24h:.2f}%)")
        elif market_state.change_24h < -1:  # Caindo mais de 1% em 24h
            weight = 1.0
            sell_score += weight
            total_weight += weight
            reasons.append(f"Queda 24h ({market_state.change_24h:.2f}%)")
        else:
            total_weight += 1.0
        
        # Calcular confiança final
        if buy_score > sell_score:
            action = 'buy'
            confidence = buy_score / total_weight if total_weight > 0 else 0
            reason = f"Sinais de compra (Score: {buy_score:.1f}/{total_weight:.1f}): {'; '.join(reasons)}"
        elif sell_score > buy_score:
            action = 'sell'
            confidence = sell_score / total_weight if total_weight > 0 else 0
            reason = f"Sinais de venda (Score: {sell_score:.1f}/{total_weight:.1f}): {'; '.join(reasons)}"
        else:
            action = 'hold'
            confidence = 0.5
            reason = f"Sinais equilibrados: {'; '.join(reasons)}"
        
        # Ajuste de confiança baseado na volatilidade
        if market_state.volatility > VOLATILITY_THRESHOLD:
            confidence *= 0.8  # Reduz confiança em alta volatilidade
            reason += f" | Alta volatilidade ({market_state.volatility:.2f}%)"
        
        # Calcular valor do trade
        if action in ['buy', 'sell'] and confidence >= self.min_confidence:
            base_amount = min(self.max_position_size, 15.0)  # Base de $15
            amount = base_amount * confidence
        else:
            amount = 0.0
        
        signal = TradingSignal(
            action=action,
            symbol=market_state.symbol,
            confidence=confidence,
            reason=reason,
            price=current_price,
            amount=amount,
            timestamp=datetime.now(),
            indicators=indicators
        )
        
        # Log detalhado no modo verbose
        if VERBOSE_LOGGING:
            logger.debug(f"Analise: {action.upper()} | Conf: {confidence:.3f} | Scores: B:{buy_score:.1f} S:{sell_score:.1f}")
        
        return signal
    
    def should_execute_trade(self, signal: TradingSignal) -> bool:
        """Verifica se deve executar o trade"""
        now = datetime.now()
        
        # Verificar confiança mínima
        if signal.confidence < self.min_confidence:
            if VERBOSE_LOGGING:
                logger.debug(f"Confianca insuficiente: {signal.confidence:.3f} < {self.min_confidence}")
            return False
        
        # Verificar limite diário de trades
        if self.daily_trade_count >= self.max_daily_trades:
            logger.info(f"Limite diario de trades atingido: {self.daily_trade_count}")
            return False
        
        # Verificar intervalo mínimo entre trades
        if (self.last_trade_time and 
            (now - self.last_trade_time).total_seconds() < self.min_trade_interval):
            if VERBOSE_LOGGING:
                logger.debug(f"Aguardando intervalo minimo entre trades")
            return False
        
        # Verificar se é ação válida
        if signal.action not in ['buy', 'sell']:
            return False
        
        return True

    def analyze_market_conditions(self, prices, volumes, symbol):
        """Análise aprofundada das condições de mercado"""
        try:
            if len(prices) < 20:
                return 0, []
            
            buy_signals = 0
            sell_signals = 0
            reasons = []
            total_signals = 0
            
            current_price = prices[-1]
            
            # 1. Análise de Bollinger Bands
            if len(prices) >= 20:
                sma_20 = sum(prices[-20:]) / 20
                std_20 = (sum([(p - sma_20) ** 2 for p in prices[-20:]]) / 20) ** 0.5
                upper_band = sma_20 + (std_20 * 2)
                lower_band = sma_20 - (std_20 * 2)
                
                if current_price <= lower_band:
                    buy_signals += 1
                    reasons.append("Preço na banda inferior de Bollinger")
                elif current_price >= upper_band:
                    sell_signals += 1
                    reasons.append("Preço na banda superior de Bollinger")
                total_signals += 1
        
            # 2. Tendência de preço
            if len(prices) >= 5:
                price_trend = (current_price - prices[-5]) / prices[-5] * 100
                if price_trend > 1:  # Subindo mais de 1%
                    buy_signals += 1
                    reasons.append(f"Tendência altista ({price_trend:.2f}%)")
                elif price_trend < -1:  # Caindo mais de 1%
                    sell_signals += 1
                    reasons.append(f"Tendência baixista ({price_trend:.2f}%)")
                total_signals += 1
        
            # 3. Volatilidade
            if len(volumes) >= 5:
                recent_volatility = sum(volumes[-5:]) / 5
                avg_volatility = sum(volumes) / len(volumes)
                if recent_volatility > avg_volatility * 1.5:  # Alta volatilidade
                    # Reduz confiança em sinais
                    buy_signals *= 0.8
                    sell_signals *= 0.8
                    reasons.append(f"Alta volatilidade detectada")
        
            # Determinar ação
            if total_signals > 0:
                if buy_signals > sell_signals:
                    action = 'buy'
                    confidence = min(buy_signals / total_signals, 1.0)
                    reason = f"Sinais de compra: {'; '.join(reasons)}"
                elif sell_signals > buy_signals:
                    action = 'sell'
                    confidence = min(sell_signals / total_signals, 1.0)
                    reason = f"Sinais de venda: {'; '.join(reasons)}"
                else:
                    action = 'hold'
                    confidence = 0.5
                    reason = "Sinais mistos, mantendo posição"
            else:
                action = 'hold'
                confidence = 0.3
                reason = "Dados insuficientes para análise"
        
            # Calcular valor do trade
            if action in ['buy', 'sell'] and confidence >= self.min_confidence:
                # Valor baseado na confiança, limitado pelo risco
                base_amount = min(self.max_position_size, 20.0)  # Base de $20
                amount = base_amount * confidence
            else:
                amount = 0.0
                
            return confidence, reasons
            
        except Exception as e:
            self.logger.error(f"Erro na análise de mercado: {e}")
            return 0.0, ["Erro na análise"]
        
        return TradingSignal(
            action=action,
            symbol=market_state.symbol,
            confidence=confidence,
            reason=reason,
            price=current_price,
            amount=amount,
            timestamp=datetime.now(),
            indicators=indicators
        )
    
    def should_execute_trade(self, signal: TradingSignal) -> bool:
        """Verifica se deve executar o trade baseado nas regras de risco"""
        now = datetime.now()
        
        # Verificar confiança mínima
        if signal.confidence < self.min_confidence:
            logger.info(f"Confiança insuficiente: {signal.confidence:.2f} < {self.min_confidence}")
            return False
        
        # Verificar limite diário de trades
        if self.daily_trade_count >= self.max_daily_trades:
            logger.info(f"Limite diário de trades atingido: {self.daily_trade_count}")
            return False
        
        # Verificar intervalo mínimo entre trades
        if (self.last_trade_time and 
            (now - self.last_trade_time).total_seconds() < self.min_trade_interval):
            logger.info(f"Intervalo mínimo entre trades não atingido")
            return False
        
        # Verificar se é ação válida
        if signal.action not in ['buy', 'sell']:
            return False
        
        return True

class OptimizedAITradingAgent:
    """Agente principal otimizado de trading automatizado"""
    
    def __init__(self, api_base: str = "http://localhost:5000"):
        self.api_base = api_base
        self.strategy = OptimizedAITradingStrategy()
        self.is_running = False
        self.monitoring_interval = MONITORING_INTERVAL  # 20 segundos - mais frequente
        self.symbol = DEFAULT_SYMBOL  # DOGEUSDT
        
        # Histórico
        self.trade_history = []
        self.signal_history = []
        
        # Estado
        self.current_position = None
        self.position_entry_price = 0.0
        self.position_amount = 0.0
        
        # Estatísticas
        self.total_trades = 0
        self.profitable_trades = 0
        self.total_profit = 0.0
        
        logger.info(f"Agente otimizado inicializado - Simbolo: {self.symbol}")
        
    def get_market_data(self) -> Optional[MarketState]:
        """Coleta dados do mercado com fallback melhorado"""
        try:
            # Dados de mercado básicos
            market_data = {'price': 0.1, 'volume': 1000000, 'change_24h': 0.5}
            
            try:
                market_response = requests.get(
                    f"{self.api_base}/api/market_data",
                    params={'symbol': self.symbol},
                    timeout=5
                )
                
                if market_response.status_code == 200:
                    market_data = market_response.json()
            except:
                logger.warning("Usando dados de mercado simulados")
            
            # Histórico de preços com fallback
            price_history = []
            try:
                prices_response = requests.get(
                    f"{self.api_base}/api/prices",
                    params={'symbol': self.symbol.replace('USDT', '/BUSD'), 'limit': 30},
                    timeout=5
                )
                
                if prices_response.status_code == 200:
                    prices_data = prices_response.json()
                    price_history = [float(p['price']) for p in prices_data if p.get('price')]
            except:
                pass
            
            # Gerar histórico simulado se necessário
            if len(price_history) < MIN_PRICE_HISTORY:
                base_price = float(market_data.get('price', 0.1))
                if base_price > 0:
                    # Gerar histórico simulado com pequenas variações
                    import random
                    price_history = []
                    current = base_price
                    for i in range(MIN_PRICE_HISTORY + 5):
                        variation = random.uniform(-0.02, 0.02)  # ±2% de variação
                        current = current * (1 + variation)
                        price_history.append(current)
                    
                    logger.info(f"Gerado historico simulado com {len(price_history)} pontos")
            
            # Volatilidade
            volatility = 2.0  # Padrão baixo
            try:
                volatility_response = requests.get(
                    f"{self.api_base}/api/volatility",
                    params={'symbol': self.symbol.replace('USDT', '/BUSD')},
                    timeout=5
                )
                
                if volatility_response.status_code == 200:
                    vol_data = volatility_response.json()
                    volatility = vol_data.get('volatility', 2.0)
            except:
                pass
            
            return MarketState(
                symbol=self.symbol,
                current_price=float(market_data.get('price', 0.1)),
                price_history=price_history,
                volume_24h=float(market_data.get('volume', 1000000)),
                change_24h=float(market_data.get('change_24h', 0.5)),
                volatility=volatility,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Erro ao coletar dados do mercado: {e}")
            return None
            
            prices_data = prices_response.json()
            price_history = [float(p['price']) for p in prices_data if p['price']]
            
            # Buscar volatilidade
            volatility_response = requests.get(
                f"{self.api_base}/api/volatility",
                params={'symbol': self.symbol.replace('USDT', '/BUSD')},
                timeout=10
            )
            
            volatility = 0.0
            if volatility_response.status_code == 200:
                vol_data = volatility_response.json()
                volatility = vol_data.get('volatility', 0.0)
            
            return MarketState(
                symbol=self.symbol,
                current_price=float(market_data.get('price', 0)),
                price_history=price_history,
                volume_24h=float(market_data.get('volume', 0)),
                change_24h=float(market_data.get('change_24h', 0)),
                volatility=volatility,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Erro ao coletar dados do mercado: {e}")
            return None
    
    def execute_trade(self, signal: TradingSignal) -> bool:
        """Executa um trade REAL via API - SEM MODO TESTE"""
        try:
            # MODO REAL - executar trade via API
            trade_data = {
                'symbol': signal.symbol,
                'action': signal.action,
                'amount': signal.amount
            }
            
            logger.info(f"EXECUTANDO TRADE REAL: {signal.action.upper()} {signal.amount:.2f} USDT @ ${signal.price:.6f}")
            logger.info(f"Confianca: {signal.confidence:.3f} | Razao: {signal.reason}")
            
            response = requests.post(
                f"{self.api_base}/api/trading/buy" if signal.action == "buy" else f"{self.api_base}/api/trading/sell",
                json=trade_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Trade executado com sucesso: {signal.action} {signal.amount:.2f} {signal.symbol}")
                logger.info(f"Resultado da API: {result}")
                
                self.total_trades += 1
                self.strategy.daily_trade_count += 1
                self.strategy.last_trade_time = datetime.now()
                
                # Atualizar posição
                if signal.action == 'buy':
                    self.current_position = 'long'
                    self.position_entry_price = signal.price
                    self.position_amount = signal.amount
                elif signal.action == 'sell' and self.current_position == 'long':
                    # Calcular lucro/prejuízo
                    profit = (signal.price - self.position_entry_price) * (self.position_amount / self.position_entry_price)
                    self.total_profit += profit
                    if profit > 0:
                        self.profitable_trades += 1
                    
                    logger.info(f"P&L: ${profit:.2f}")
                    self.current_position = None
                    self.position_entry_price = 0.0
                    self.position_amount = 0.0
                
                # Salvar no histórico
                self.trade_history.append({
                    'timestamp': signal.timestamp,
                    'action': signal.action,
                    'symbol': signal.symbol,
                    'price': signal.price,
                    'amount': signal.amount,
                    'confidence': signal.confidence,
                    'reason': signal.reason,
                    'result': result
                })
                
                return True
            else:
                logger.error(f"Erro ao executar trade: HTTP {response.status_code}")
                logger.error(f"Resposta: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Excecao ao executar trade: {e}")
            return False
    
    def log_signal(self, signal: TradingSignal, executed: bool):
        """Log detalhado do sinal gerado"""
        logger.info(f"🤖 SINAL: {signal.action.upper()} | {signal.symbol}")
        logger.info(f"   💰 Preço: ${signal.price:.6f}")
        logger.info(f"   📊 Confiança: {signal.confidence:.2f}")
        logger.info(f"   💵 Valor: ${signal.amount:.2f}")
        logger.info(f"   🎯 Razão: {signal.reason}")
        logger.info(f"   ⚡ Executado: {'✅ SIM' if executed else '❌ NÃO'}")
        
        if signal.indicators:
            logger.info(f"   📈 RSI: {signal.indicators.get('rsi', 0):.1f}")
            logger.info(f"   📊 Volatilidade: {signal.indicators.get('volatility', 0):.2f}%")
    
    def print_status(self):
        """Imprime status atual do agente"""
        win_rate = (self.profitable_trades / max(self.total_trades, 1)) * 100
        
        print("\n" + "="*60)
        print("🤖 AI TRADING AGENT - STATUS")
        print("="*60)
        print(f"📊 Total de Trades: {self.total_trades}")
        print(f"✅ Trades Lucrativos: {self.profitable_trades}")
        print(f"📈 Taxa de Acerto: {win_rate:.1f}%")
        print(f"💰 Lucro Total: ${self.total_profit:.2f}")
        print(f"🎯 Posição Atual: {self.current_position or 'Nenhuma'}")
        if self.current_position:
            print(f"   💵 Preço de Entrada: ${self.position_entry_price:.6f}")
            print(f"   📊 Valor da Posição: ${self.position_amount:.2f}")
        print(f"📅 Trades Hoje: {self.strategy.daily_trade_count}/{self.strategy.max_daily_trades}")
        print("="*60)
    
    async def run_monitoring_cycle(self):
        """Ciclo principal de monitoramento"""
        try:
            # Coleta dados do mercado
            market_state = self.get_market_data()
            if not market_state:
                logger.warning("Não foi possível obter dados do mercado")
                return
            
            # Gera sinal de trading
            signal = self.strategy.analyze_market(market_state)
            
            # Salva sinal no histórico
            self.signal_history.append(signal)
            
            # Verifica se deve executar trade
            should_execute = self.strategy.should_execute_trade(signal)
            
            # Log do sinal
            if signal.action != 'hold' or signal.confidence > 0.6:
                self.log_signal(signal, should_execute)
            
            # Executa trade se necessário
            if should_execute:
                success = self.execute_trade(signal)
                if success:
                    self.print_status()
            
        except Exception as e:
            logger.error(f"Erro no ciclo de monitoramento: {e}")
    
    async def run(self):
        """Executa o agente otimizado"""
        logger.info("Iniciando AI Trading Agent Otimizado")
        logger.info(f"Simbolo: {self.symbol}")
        logger.info(f"Intervalo: {self.monitoring_interval}s")
        logger.info(f"Confianca minima: {self.strategy.min_confidence}")
        logger.info(f"Valor maximo por trade: ${self.strategy.max_position_size}")
        logger.info(f"MODO REAL - Trades reais serao executados!")
        
        self.is_running = True
        
        while self.is_running:
            try:
                await self.run_monitoring_cycle()
                await asyncio.sleep(self.monitoring_interval)
                
            except KeyboardInterrupt:
                logger.info("Parando agente por solicitacao do usuario")
                break
            except Exception as e:
                logger.error(f"Erro no loop principal: {e}")
                await asyncio.sleep(5)
        
        logger.info("AI Trading Agent Otimizado finalizado")
        self.print_status()
    
    def stop(self):
        """Para o agente"""
        self.is_running = False

async def main():
    """Função principal"""
    # Criar e executar agente otimizado
    agent = OptimizedAITradingAgent()
    
    try:
        await agent.run()
    except KeyboardInterrupt:
        print("\nParando agente...")
        agent.stop()
    finally:
        agent.print_status()

if __name__ == "__main__":
    print("MoCoVe AI Trading Agent - VERSAO OTIMIZADA E MESCLADA")
    print("=" * 60)
    print("Configuracoes otimizadas para melhor performance")
    print("Confianca minima reduzida para 40%")
    print("MODO REAL - Trades reais serao executados!")
    print("Use Ctrl+C para parar a qualquer momento")
    print("=" * 60)
    
    asyncio.run(main())

if __name__ == "__main__":
    print("🤖 MoCoVe AI Trading Agent")
    print("=" * 50)
    print("⚠️  ATENÇÃO: Este agente fará trades reais!")
    print("💰 Certifique-se de que os limites estão configurados")
    print("🛑 Use Ctrl+C para parar a qualquer momento")
    print("=" * 50)
    
    asyncio.run(main())
