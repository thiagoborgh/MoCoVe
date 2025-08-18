#!/usr/bin/env python3
"""
AI Trading Agent - Versão Robusta
"""

import time
import requests
import logging
import os
from datetime import datetime
try:
    import ccxt
except ImportError:
    print("⚠️ ccxt não instalado. Execute: pip install ccxt")
    ccxt = None

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Arquivo .env carregado com sucesso")
except ImportError:
    print("⚠️ python-dotenv não instalado. Usando variáveis de ambiente do sistema")
except Exception as e:
    print(f"⚠️ Erro ao carregar .env: {e}")

# Setup básico de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ai_trading_agent_robust.log", encoding="utf-8"),
    ],
)

log = logging.getLogger("AITradingAgent")

class SimpleAgent:
    def __init__(self):
        self.api_base = "http://localhost:5000"
        self.is_running = True
        self.cycle_count = 0
        # Configuração da Binance via ccxt
        self.api_key = os.getenv('BINANCE_API_KEY', '')
        self.api_secret = os.getenv('BINANCE_API_SECRET', '')
        self.use_testnet = os.getenv('USE_TESTNET', 'true').lower() == 'true'

        # Log para depuração das variáveis de ambiente
        log.info(f"[DEBUG] BINANCE_API_KEY: {'SET' if self.api_key else 'NOT SET'} ({self.api_key[:4]}...)")
        log.info(f"[DEBUG] BINANCE_API_SECRET: {'SET' if self.api_secret else 'NOT SET'} ({self.api_secret[:4]}...)")
        log.info(f"[DEBUG] USE_TESTNET: {self.use_testnet}")

        # Lista de moedas para análise (carregada da watchlist)
        self.active_coins = []
        self.load_watchlist()

        if ccxt is None:
            log.error("ccxt não disponível. Trading real desabilitado.")
            self.binance = None
            self.can_trade = False
        elif not self.api_key or not self.api_secret:
            log.warning("Credenciais Binance não configuradas. Modo simulação ativo.")
            self.binance = None
            self.can_trade = False
        else:
            try:
                self.binance = ccxt.binance({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'sandbox': self.use_testnet,
                    'enableRateLimit': True,
                    'options': {'defaultType': 'spot'},
                })
                self.can_trade = True
                log.info(f"Binance configurado. Testnet: {self.use_testnet}")
            except Exception as e:
                log.error(f"Erro ao configurar Binance: {e}")
                self.binance = None
                self.can_trade = False
        self.trade_amount = float(os.getenv('DEFAULT_AMOUNT', 10.0))
        
    def load_watchlist(self):
        """Carrega moedas habilitadas para trading da watchlist"""
        try:
            import json
            with open('coin_watchlist_expanded.json', 'r', encoding='utf-8') as f:
                watchlist = json.load(f)
            
            # Extrair moedas com trading_enabled=True
            active_coins = []
            
            # Memecoins
            for tier in ['tier1', 'tier2', 'tier3', 'trending']:
                if tier in watchlist.get('memecoins', {}):
                    for coin in watchlist['memecoins'][tier]:
                        if coin.get('trading_enabled', False):
                            active_coins.append(coin['symbol'])
            
            # Altcoins 
            for category in ['defi', 'layer1', 'ai_tokens', 'gaming']:
                if category in watchlist.get('altcoins', {}):
                    for coin in watchlist['altcoins'][category]:
                        if coin.get('trading_enabled', False):
                            active_coins.append(coin['symbol'])
            
            self.active_coins = active_coins
            log.info(f"Carregadas {len(self.active_coins)} moedas ativas: {', '.join(self.active_coins[:5])}...")
            
        except Exception as e:
            log.error(f"Erro ao carregar watchlist: {e}")
            # Fallback para moedas padrão
            self.active_coins = ["DOGEUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT"]
            log.warning(f"Usando moedas padrão: {', '.join(self.active_coins)}")
        
    def get_market_data(self, symbol="DOGEUSDT"):
        """Obtém dados de mercado com fallback para dados históricos"""
        try:
            url = f"{self.api_base}/api/market_data"
            response = requests.get(url, params={"symbol": symbol}, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Garantir que temos valores numéricos
            if isinstance(data, dict):
                # Converter campos importantes para float
                for field in ['price', 'change', 'percentage', 'volume']:
                    if field in data and data[field] is not None:
                        try:
                            data[field] = float(data[field])
                        except (ValueError, TypeError):
                            data[field] = 0.0
                    elif field not in data:
                        data[field] = 0.0
                
                # Garantir que change_24h tenha o valor do percentage se existir
                if 'percentage' in data and data['percentage'] != 0:
                    data['change_24h'] = data['percentage']
                elif 'change_24h' not in data or data.get('change_24h') is None:
                    data['change_24h'] = 0.0
                
                # Se ainda não há variação real, calcular baseado em dados históricos
                if data.get('change_24h', 0) == 0 and data.get('percentage', 0) == 0:
                    calculated_change = self.calculate_price_change(symbol, data.get('price', 0))
                    if calculated_change is not None:
                        data['change_24h'] = calculated_change
                        data['percentage'] = calculated_change
                elif 'change_24h' not in data and 'change' in data:
                    data['change_24h'] = data['change']
            
            return data
        except Exception as e:
            log.error(f"Erro ao obter market data: {e}")
            return None
    
    def calculate_price_change(self, symbol, current_price):
        """Calcula variação baseada em dados históricos"""
        try:
            # Buscar preços históricos
            prices = self.get_prices(symbol, limit=24)  # Últimas 24 horas
            if prices and len(prices) > 0 and current_price > 0:
                first_price = float(prices[0].get('price', 0))
                if first_price > 0:
                    change_percent = ((current_price - first_price) / first_price) * 100
                    return round(change_percent, 2)
            
            # Se não há dados históricos, simular variação realista
            import random
            simulated_change = round((random.random() - 0.5) * 8, 2)  # -4% a +4%
            log.info(f"🎲 {symbol}: Variação simulada {simulated_change}% (sem dados históricos)")
            return simulated_change
            
        except Exception as e:
            log.error(f"Erro ao calcular variação para {symbol}: {e}")
            return None
    
    def get_prices(self, symbol="DOGEUSDT", limit=60):
        """Obtém histórico de preços"""
        try:
            url = f"{self.api_base}/api/prices"
            response = requests.get(url, params={"symbol": symbol, "limit": limit}, timeout=5)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return data
            return data.get("prices", [])
        except Exception as e:
            log.error(f"Erro ao obter prices: {e}")
            return []
    
    def analyze_market(self, market_data, prices):
        """Análise melhorada de mercado"""
        if not market_data or not prices:
            return "hold", 0.0, "Dados insuficientes"
        
        current_price = float(market_data.get("price", 0))
        change_24h = float(market_data.get("change_24h", 0))
        volume = float(market_data.get("volume", 0))
        
        # Análise de tendência com mais fatores
        confidence = 0.0
        
        # Fator 1: Mudança de preço
        if abs(change_24h) > 5:
            confidence += 0.4
        elif abs(change_24h) > 2:
            confidence += 0.2
        
        # Fator 2: Volume (se disponível)
        if volume > 1000000:  # Volume alto
            confidence += 0.2
        
        # Fator 3: Análise de preços recentes
        if len(prices) >= 3:
            try:
                # Garantir que temos valores numéricos
                numeric_prices = []
                for p in prices[-3:]:
                    if isinstance(p, dict):
                        # Se o preço é um dicionário, tentar extrair o valor do preço
                        price_val = p.get('price', p.get('close', p.get('value', 0)))
                    else:
                        price_val = p
                    
                    try:
                        numeric_prices.append(float(price_val))
                    except (ValueError, TypeError):
                        pass
                
                if len(numeric_prices) >= 3:
                    recent_trend = (numeric_prices[-1] - numeric_prices[-3]) / numeric_prices[-3] * 100
                    if abs(recent_trend) > 1:
                        confidence += 0.2
                        
            except Exception as e:
                log.warning(f"Erro ao calcular tendência: {e}")
        
        # Decisão baseada em múltiplos fatores - MELHORADA PARA DETECTAR OPORTUNIDADES
        
        # Detectar oportunidades de alta (como 9% que você viu na Binance)
        if change_24h >= 8:
            return "buy", min(confidence + 0.3, 0.9), f"🚀 ALTA FORTE: {change_24h:.2f}% - Oportunidade detectada!"
        elif change_24h >= 5:
            return "buy", min(confidence + 0.2, 0.8), f"📈 Alta significativa: {change_24h:.2f}%"
        elif change_24h >= 3:
            return "buy", confidence, f"📊 Alta moderada: {change_24h:.2f}%"
        
        # Detectar quedas para possível venda
        elif change_24h <= -8:
            return "sell", min(confidence + 0.3, 0.9), f"💥 QUEDA FORTE: {change_24h:.2f}% - Proteger capital!"
        elif change_24h <= -5:
            return "sell", min(confidence + 0.2, 0.8), f"📉 Queda significativa: {change_24h:.2f}%"
        elif change_24h <= -3:
            return "sell", confidence, f"⚠️ Queda moderada: {change_24h:.2f}%"
        
        # Movimento lateral
        elif abs(change_24h) > 1:
            return "hold", confidence * 0.3, f"📍 Movimento lateral: {change_24h:.2f}%"
        else:
            return "hold", 0.1, f"😴 Mercado estável: {change_24h:.2f}%"
    
    def run_cycle(self):
        """Executa um ciclo de análise em múltiplas moedas"""
        self.cycle_count += 1
        log.info(f"=== CICLO {self.cycle_count} - Analisando {len(self.active_coins)} moedas ===")
        
        opportunities = []
        
        try:
            # Analisar cada moeda da watchlist
            for symbol in self.active_coins:
                try:
                    # Obter dados
                    market_data = self.get_market_data(symbol)
                    if not market_data:
                        continue
                        
                    prices = self.get_prices(symbol)
                    
                    # Análise
                    action, confidence, reason = self.analyze_market(market_data, prices)
                    price = market_data.get("price", 0)
                    change_24h = market_data.get("change_24h", 0)
                    
                    log.info(f"{symbol}: ${price:.8f} | {change_24h:+.2f}% | {action.upper()} ({confidence:.2f}) - {reason}")
                    
                    # Coletar oportunidades
                    if action in ["buy", "sell"] and confidence >= 0.6:
                        opportunities.append({
                            'symbol': symbol,
                            'action': action,
                            'confidence': confidence,
                            'price': price,
                            'change_24h': change_24h,
                            'reason': reason
                        })
                        
                except Exception as e:
                    log.error(f"Erro ao analisar {symbol}: {e}")
                    continue
            
            # Processar oportunidades (ordenar por confiança)
            if opportunities:
                opportunities.sort(key=lambda x: x['confidence'], reverse=True)
                log.info(f"=== ENCONTRADAS {len(opportunities)} OPORTUNIDADES ===")
                
                for i, opp in enumerate(opportunities[:3], 1):  # Top 3 oportunidades
                    log.info(f"{i}. {opp['symbol']}: {opp['action'].upper()} | "
                           f"Confiança: {opp['confidence']:.2f} | "
                           f"Mudança 24h: {opp['change_24h']:+.2f}% | "
                           f"Razão: {opp['reason']}")
                
                # Executar apenas a melhor oportunidade
                best_opp = opportunities[0]
                self.execute_trade(best_opp)
            else:
                log.info("Nenhuma oportunidade de trading encontrada neste ciclo.")
                
        except Exception as e:
            log.error(f"Erro no ciclo {self.cycle_count}: {e}")
    
    def execute_trade(self, opportunity):
        """Executa ordem de trading para a oportunidade"""
        symbol = opportunity['symbol']
        action = opportunity['action']
        confidence = opportunity['confidence']
        
        if not self.can_trade or self.binance is None:
            log.info(f"[SIMULAÇÃO] {action.upper()} {symbol} - Modo simulação ativo (confiança: {confidence:.2f})")
            return
        
        try:
            # Validações de segurança
            if self.trade_amount < 10:
                log.warning(f"Valor muito baixo para trade: ${self.trade_amount}")
                return
            
            # Verificar saldo antes de executar
            balance = self.binance.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            
            if action == 'buy' and usdt_balance < self.trade_amount:
                log.warning(f"Saldo USDT insuficiente: {usdt_balance} < {self.trade_amount}")
                return
            
            order_type = 'market'
            side = 'buy' if action == 'buy' else 'sell'
            
            # Calcular quantidade
            price = opportunity['price']
            amount = self.trade_amount / float(price) if side == 'buy' else self.trade_amount
            
            log.info(f"Enviando ordem REAL: {side.upper()} {symbol} quantidade: {amount:.4f}")
            result = self.binance.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=round(amount, 4)
            )
            log.info(f"✅ Ordem executada com sucesso: {result['id']}")
            
        except Exception as e:
            log.error(f"❌ Erro ao executar ordem real: {e}")
            log.info(f"[SIMULAÇÃO FALLBACK] {action.upper()} {symbol} executado com confiança {confidence:.2f}")
    
    def run(self):
        """Loop principal do agente"""
        log.info("=== AGENTE IA TRADING INICIADO ===")
        
        retry_count = 0
        max_retries = 5
        
        try:
            while self.is_running:
                try:
                    self.run_cycle()
                    retry_count = 0  # Reset contador se ciclo foi bem-sucedido
                    
                    # Status a cada 10 ciclos
                    if self.cycle_count % 10 == 0:
                        log.info(f"Status: {self.cycle_count} ciclos completados")
                    
                    # Aguardar próximo ciclo
                    log.info("Aguardando 20 segundos...")
                    time.sleep(20)
                    
                except Exception as e:
                    retry_count += 1
                    log.error(f"Erro no ciclo {self.cycle_count}: {e}")
                    
                    if retry_count >= max_retries:
                        log.error(f"Muitos erros consecutivos ({max_retries}), reiniciando...")
                        time.sleep(60)  # Aguardar 1 minuto antes de reiniciar
                        retry_count = 0
                        continue
                    
                    # Aguardar um pouco antes de tentar novamente
                    wait_time = min(60, 10 * retry_count)
                    log.warning(f"Aguardando {wait_time}s antes de tentar novamente...")
                    time.sleep(wait_time)
                
        except KeyboardInterrupt:
            log.info("Agente interrompido pelo usuário")
        except Exception as e:
            log.error(f"Erro crítico: {e}")
        finally:
            self.is_running = False
            log.info("=== AGENTE FINALIZADO ===")

def main():
    agent = SimpleAgent()
    agent.run()

if __name__ == "__main__":
    main()
