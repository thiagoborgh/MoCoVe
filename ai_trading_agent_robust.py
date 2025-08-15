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
        self.symbol = os.getenv('DEFAULT_SYMBOL', 'DOGE/USDT')
        self.trade_amount = float(os.getenv('DEFAULT_AMOUNT', 10.0))
        
    def get_market_data(self, symbol="DOGEUSDT"):
        """Obtém dados de mercado"""
        try:
            url = f"{self.api_base}/api/market_data"
            response = requests.get(url, params={"symbol": symbol}, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Garantir que temos valores numéricos
            if isinstance(data, dict):
                # Converter campos importantes para float
                for field in ['price', 'change', 'percentage', 'change_24h', 'volume']:
                    if field in data and data[field] is not None:
                        try:
                            data[field] = float(data[field])
                        except (ValueError, TypeError):
                            data[field] = 0.0
                    elif field not in data:
                        data[field] = 0.0
                
                # Normalizar campo change_24h se não existir
                if 'change_24h' not in data and 'percentage' in data:
                    data['change_24h'] = data['percentage']
                elif 'change_24h' not in data and 'change' in data:
                    data['change_24h'] = data['change']
            
            return data
        except Exception as e:
            log.error(f"Erro ao obter market data: {e}")
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
        
        # Decisão baseada em múltiplos fatores
        if change_24h > 3 and confidence >= 0.5:
            return "buy", confidence, f"Alta significativa: {change_24h:.2f}%, confiança: {confidence:.2f}"
        elif change_24h < -3 and confidence >= 0.5:
            return "sell", confidence, f"Queda significativa: {change_24h:.2f}%, confiança: {confidence:.2f}"
        elif abs(change_24h) > 1:
            return "hold", confidence * 0.5, f"Movimento moderado: {change_24h:.2f}%"
        else:
            return "hold", 0.1, f"Mercado estável: {change_24h:.2f}%"
    
    def run_cycle(self):
        """Executa um ciclo de análise e realiza ordens reais se necessário"""
        self.cycle_count += 1
        log.info(f"=== CICLO {self.cycle_count} ===")
        try:
            # Obter dados
            market_data = self.get_market_data()
            if not market_data:
                log.warning("Falha ao obter dados de mercado")
                return
            prices = self.get_prices()
            # Análise
            action, confidence, reason = self.analyze_market(market_data, prices)
            price = market_data.get("price", 0)
            log.info(f"Preço: ${price:.8f} | Ação: {action.upper()} | Confiança: {confidence:.2f} | Razão: {reason}")
            # Executar ordem com validações de segurança
            min_confidence = 0.6  # Aumentar limite mínimo
            if action in ["buy", "sell"] and confidence >= min_confidence:
                if not self.can_trade or self.binance is None:
                    log.info(f"[SIMULAÇÃO] {action.upper()} - Modo simulação ativo (confiança: {confidence:.2f})")
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
                    amount = self.trade_amount / float(price) if side == 'buy' else self.trade_amount
                    
                    log.info(f"Enviando ordem REAL: {side.upper()} {self.symbol} quantidade: {amount:.4f}")
                    result = self.binance.create_order(
                        symbol=self.symbol,
                        type=order_type,
                        side=side,
                        amount=round(amount, 4)
                    )
                    log.info(f"✅ Ordem executada com sucesso: {result['id']}")
                    
                except Exception as e:
                    log.error(f"❌ Erro ao executar ordem real: {e}")
                    log.info(f"[SIMULAÇÃO FALLBACK] {action.upper()} executado com confiança {confidence:.2f}")
            elif action in ["buy", "sell"]:
                log.info(f"[SKIP] {action.upper()} - Confiança baixa: {confidence:.2f} < {min_confidence}")
        except Exception as e:
            log.error(f"Erro no ciclo {self.cycle_count}: {e}")
    
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
