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

# Importar o sistema de monitoramento de portfólio
try:
    from portfolio_monitor import PortfolioMonitor
    PORTFOLIO_MONITOR_AVAILABLE = True
except ImportError:
    print("⚠️ Portfolio Monitor não disponível")
    PORTFOLIO_MONITOR_AVAILABLE = False

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Arquivo .env carregado com sucesso")
except ImportError:
    print("⚠️ python-dotenv não instalado. Usando variáveis de ambiente do sistema")
except Exception as e:
    print(f"⚠️ Erro ao carregar .env: {e}")

# Setup básico de logging com flush imediato
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ai_trading_agent_robust.log", encoding="utf-8", mode="a"),
    ],
    force=True  # Force reconfiguration if already configured
)

# Configurar o logger para fazer flush imediato
log = logging.getLogger("AITradingAgent")
log.setLevel(logging.INFO)

# Garantir que os handlers façam flush imediato
for handler in log.handlers:
    if isinstance(handler, logging.FileHandler):
        handler.flush()

# Também configurar o handler de arquivo para fazer flush automático
file_handler = None
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.FileHandler):
        file_handler = handler
        break

if file_handler:
    # Forçar flush a cada log
    original_emit = file_handler.emit
    def flush_emit(record):
        original_emit(record)
        file_handler.flush()
    file_handler.emit = flush_emit

class SimpleAgent:
    def __init__(self):
        self.api_base = "http://localhost:5000"
        self.is_running = True
        self.cycle_count = 0
        
        # Verificar se backend está disponível antes de continuar
        self.validate_backend_connection()
        
        # Configuração da Binance via ccxt
        self.api_key = os.getenv('BINANCE_API_KEY', '')
        self.api_secret = os.getenv('BINANCE_API_SECRET', '')
        self.use_testnet = os.getenv('USE_TESTNET', 'true').lower() == 'true'
        self.enable_real_trading = os.getenv('ENABLE_REAL_TRADING', 'false').lower() == 'true'

        # Log para depuração das variáveis de ambiente
        log.info(f"[DEBUG] BINANCE_API_KEY: {'SET' if self.api_key else 'NOT SET'} ({self.api_key[:4]}...)")
        log.info(f"[DEBUG] BINANCE_API_SECRET: {'SET' if self.api_secret else 'NOT SET'} ({self.api_secret[:4]}...)")
        log.info(f"[DEBUG] USE_TESTNET: {self.use_testnet}")
        log.info(f"[DEBUG] ENABLE_REAL_TRADING: {self.enable_real_trading}")

        # Lista de moedas para análise (carregada da watchlist)
        self.active_coins = []
        self.load_watchlist()
        
        # 🛡️ Controle de moedas já compradas - NOVA FUNCIONALIDADE
        self.purchased_coins = set()  # Set para evitar compras duplicadas
        # Controle de moedas já compradas - NOVA FUNCIONALIDADE
        self.purchased_coins = set()  # Set para evitar compras duplicadas
        
        # 📊 Monitor de Performance do Portfólio
        if PORTFOLIO_MONITOR_AVAILABLE:
            try:
                self.portfolio_monitor = PortfolioMonitor(self.api_base)
                log.info("📊 Portfolio Monitor inicializado")
            except Exception as e:
                log.warning(f"📊 Erro ao inicializar Portfolio Monitor: {e}")
                self.portfolio_monitor = None
        else:
            self.portfolio_monitor = None
            log.warning("📊 Portfolio Monitor não disponível")
            
        # Carregar histórico após inicializar portfolio monitor
        self.load_purchased_coins()  # Carrega moedas já compradas do histórico

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
                log.info(f"🔗 Inicializando conexão Binance (Testnet: {self.use_testnet})...")
                self.binance = ccxt.binance({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'sandbox': self.use_testnet,
                    'enableRateLimit': True,
                    'options': {'defaultType': 'spot'},
                    'urls': {
                        'api': {
                            'public': 'https://testnet.binance.vision/api' if self.use_testnet else 'https://api.binance.com/api',
                            'private': 'https://testnet.binance.vision/api' if self.use_testnet else 'https://api.binance.com/api'
                        }
                    } if self.use_testnet else {}
                })
                # Testar conexão
                balance = self.binance.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                self.can_trade = True
                log.info(f"✅ Binance conectada! Saldo USDT: ${usdt_balance:.2f}")
            except Exception as e:
                log.error(f"❌ Erro ao conectar Binance: {e}")
                self.binance = None
                self.can_trade = False
        self.trade_amount = float(os.getenv('DEFAULT_AMOUNT', 10.0))
        
    def validate_backend_connection(self):
        """Valida se o backend está disponível antes de iniciar o agent"""
        log.info("🔗 Verificando conexão com backend...")
        try:
            response = requests.get(f"{self.api_base}/api/system/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                log.info("✅ Backend conectado e funcionando")
                if data.get('status', {}).get('database'):
                    log.info("✅ Banco de dados disponível")
                else:
                    log.warning("⚠️ Banco de dados pode estar indisponível")
            else:
                log.warning(f"⚠️ Backend respondeu com status {response.status_code}")
        except requests.exceptions.ConnectionError:
            log.warning("⚠️ Backend não está rodando - algumas funcionalidades podem ser limitadas")
            log.info("💡 Certifique-se de que o backend está rodando: python backend/app.py")
        except Exception as e:
            log.warning(f"⚠️ Erro ao verificar backend: {e}")

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
    
    def load_purchased_coins(self):
        """Carrega lista de moedas já compradas do histórico de trades"""
        log.info("🛡️ Carregando moedas já compradas do histórico...")
        try:
            # Fazer várias tentativas de conexão com delays curtos
            for attempt in range(2):  # Reduzir para 2 tentativas para não travar a inicialização
                try:
                    response = requests.get(f"{self.api_base}/api/trades", timeout=5)  # Timeout menor
                    if response.status_code == 200:
                        trades = response.json()
                        # Adicionar todas as moedas que tiveram compras (buy) na lista de compradas
                        for trade in trades:
                            if trade.get('type') == 'buy':
                                symbol = trade.get('symbol')
                                if symbol:
                                    self.purchased_coins.add(symbol)
                                    
                        if self.purchased_coins:
                            log.info(f"🛡️ Controle de duplicatas: {len(self.purchased_coins)} moedas já compradas: {', '.join(list(self.purchased_coins)[:5])}...")
                        else:
                            log.info("🛡️ Controle de duplicatas: Nenhuma moeda comprada anteriormente")
                        return  # Sucesso, sair da função
                    else:
                        log.warning(f"Tentativa {attempt+1}: API retornou status {response.status_code}")
                        
                except requests.exceptions.ConnectionError as e:
                    log.warning(f"Tentativa {attempt+1}: Backend não disponível no momento")
                    if attempt < 1:  # Se não é a última tentativa
                        time.sleep(2)  # Esperar menos tempo
                    
                except Exception as e:
                    log.warning(f"Tentativa {attempt+1}: Erro inesperado: {e}")
                    break
                    
        except Exception as e:
            log.warning(f"Erro geral ao carregar moedas compradas: {e}")
            
        log.info("🛡️ Controle de duplicatas: Iniciando com lista vazia (backend indisponível)")
    
    def add_purchased_coin(self, symbol):
        """Adiciona uma moeda à lista de compradas"""
        self.purchased_coins.add(symbol)
        log.info(f"🛡️ {symbol} adicionada à lista de moedas compradas")
    
    def reset_purchased_coins(self):
        """Limpa a lista de moedas compradas (útil para reiniciar o controle)"""
        self.purchased_coins.clear()
        log.info("🛡️ Lista de moedas compradas foi resetada")
        
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
        
        # Detectar quedas para possível venda (mais conservador)
        elif change_24h <= -2:
            return "sell", min(confidence + 0.4, 0.9), f"� PROTEÇÃO: {change_24h:.2f}% - Venda preventiva!"
        elif change_24h <= -1:
            return "sell", min(confidence + 0.3, 0.8), f"⚠️ ALERTA: {change_24h:.2f}% - Minimizar perdas!"
        elif change_24h <= -0.5:
            return "sell", min(confidence + 0.2, 0.7), f"📉 Declínio: {change_24h:.2f}% - Monitorar de perto"
        
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
                    
                    # 🛡️ CONTROLE DE COMPRAS DUPLICADAS - Se é uma compra, verificar se já compramos esta moeda
                    if action == "buy" and symbol in self.purchased_coins:
                        log.info(f"🚫 {symbol}: JÁ COMPRADA - Pulando para evitar duplicata")
                        continue
                    
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
        
        # Log detalhado para debug
        log.info(f"[DEBUG] execute_trade chamado: {symbol} {action} confidence={confidence}")
        log.info(f"[DEBUG] can_trade={self.can_trade}, binance={self.binance is not None}")
        log.info(f"[DEBUG] trade_amount=${self.trade_amount}")
        
        if not self.enable_real_trading:
            # Modo simulação quando ENABLE_REAL_TRADING=false
            price = opportunity['price']
            if action == 'buy':
                amount = self.trade_amount / float(price)
                value = self.trade_amount
            else:
                # Simular venda total da posição
                try:
                    if self.binance:
                        balance = self.binance.fetch_balance()
                        coin_symbol = symbol.replace('USDT', '')
                        coin_balance = balance.get(coin_symbol, {}).get('free', 0)
                        amount = float(coin_balance) if coin_balance > 0 else 0
                        value = amount * float(price)
                    else:
                        # Simulação sem conexão - usar valor estimado
                        amount = self.trade_amount / float(price)
                        value = self.trade_amount
                except:
                    amount = self.trade_amount / float(price)
                    value = self.trade_amount
                    
            log.info(f"💰 [SIMULAÇÃO] {action.upper()} {symbol}")
            log.info(f"   Preço: ${price:.8f} | Quantidade: {amount:.4f} | Valor: ${value:.2f}")
            if action == 'sell' and value > self.trade_amount:
                log.info(f"   🔥 VENDA TOTAL simulada - Valor muito maior que trade padrão!")
            log.info(f"   Confiança: {confidence:.2f} | Razão: {opportunity.get('reason', 'N/A')}")
            log.info(f"   ⚠️ ENABLE_REAL_TRADING=False - Trade não executado")
            return
        
        if not self.can_trade or self.binance is None:
            log.error(f"❌ [ERRO_CONEXÃO] {action.upper()} {symbol} - Falha na conexão Binance")
            return
        
        try:
            # Validações de segurança
            if self.trade_amount < 5:
                log.warning(f"⚠️ Valor muito baixo para trade: ${self.trade_amount}")
                return
            
            # Verificar saldo antes de executar
            balance = self.binance.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            
            if action == 'buy' and usdt_balance < self.trade_amount:
                log.warning(f"⚠️ Saldo USDT insuficiente: ${usdt_balance:.2f} < ${self.trade_amount}")
                return
            elif action == 'sell':
                # Para vendas, verificar se temos a moeda para vender
                coin_symbol = symbol.replace('USDT', '')
                coin_balance = balance.get(coin_symbol, {}).get('free', 0)
                if coin_balance <= 0:
                    log.warning(f"⚠️ Sem saldo de {coin_symbol} para vender: {coin_balance}")
                    return
                log.info(f"✅ Saldo disponível para venda: {coin_balance} {coin_symbol}")
            
            # Preparar ordem
            order_type = 'market'
            side = 'buy' if action == 'buy' else 'sell'
            
            # Garantir que é um par USDT válido
            if not symbol.endswith('USDT'):
                log.error(f"❌ ERRO: {symbol} não é um par USDT válido!")
                return
            
            # Calcular quantidade
            price = opportunity['price']
            if side == 'buy':
                # Compra: usar valor em USDT para calcular quantidade da moeda
                amount = self.trade_amount / float(price)
            else:
                # Venda: VENDER TODA A POSIÇÃO da moeda (não apenas $5.10)
                try:
                    # Obter saldo atual da moeda específica
                    balance = self.binance.fetch_balance()
                    coin_symbol = symbol.replace('USDT', '')  # Ex: DOGE de DOGEUSDT
                    coin_balance = balance.get(coin_symbol, {}).get('free', 0)
                    
                    if coin_balance > 0:
                        amount = float(coin_balance)
                        log.info(f"💼 VENDA TOTAL: {coin_balance} {coin_symbol} (valor estimado: ${amount * float(price):.2f})")
                    else:
                        log.warning(f"⚠️ Sem saldo de {coin_symbol} para vender")
                        return
                except Exception as e:
                    log.error(f"❌ Erro ao obter saldo para venda: {e}")
                    # Fallback para valor fixo se não conseguir obter saldo
                    amount = self.trade_amount / float(price)
                    log.warning(f"⚠️ Usando valor fixo para venda: ${self.trade_amount}")
                
            # Log da ordem antes de executar
            log.info(f"🚀 EXECUTANDO ORDEM REAL:")
            log.info(f"   Símbolo: {symbol} | Ação: {side.upper()}")
            log.info(f"   Preço: ${price:.8f} | Quantidade: {amount:.6f}")
            if side == 'buy':
                log.info(f"   Valor estimado: ${self.trade_amount:.2f} USDT")
            else:
                estimated_value = amount * float(price)
                log.info(f"   Valor estimado: ${estimated_value:.2f} USDT (VENDA TOTAL)")
            log.info(f"   Confiança: {confidence:.2f}")
            
            # Executar ordem na Binance
            result = self.binance.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=round(amount, 6),  # Mais precisão
                params={'test': False}  # Garantir que não é teste
            )
            
            # Log de sucesso
            log.info(f"✅ ORDEM EXECUTADA COM SUCESSO!")
            log.info(f"   ID: {result.get('id', 'N/A')}")
            log.info(f"   Status: {result.get('status', 'N/A')}")
            log.info(f"   Quantidade: {result.get('amount', 'N/A')}")
            log.info(f"   Valor: ${result.get('cost', 'N/A')}")
            
            # Salvar trade no banco de dados
            self.save_trade_to_db(symbol, action, amount, price, self.trade_amount, result)
            
        except Exception as e:
            log.error(f"❌ ERRO AO EXECUTAR ORDEM REAL: {e}")
            log.info(f"💰 [SIMULAÇÃO FALLBACK] {action.upper()} {symbol} (confiança: {confidence:.2f})")
    
    def save_trade_to_db(self, symbol, action, amount, price, total, order_result):
        """Salva o trade executado no banco de dados"""
        try:
            import requests
            from datetime import datetime
            
            # Dados do trade para enviar ao backend
            trade_data = {
                'date': datetime.now().isoformat(),
                'type': action,
                'symbol': symbol,
                'amount': float(amount),
                'price': float(price), 
                'total': float(total),
                'status': 'completed'
            }
            
            # Enviar para o backend via API
            response = requests.post(f"{self.api_base}/api/trades", json=trade_data, timeout=5)
            
            if response.status_code == 201:
                log.info(f"💾 Trade salvo no banco: {action.upper()} {symbol} - ${total:.2f}")
                
                # 🛡️ Se foi uma compra bem-sucedida, adicionar à lista de moedas compradas
                if action == 'buy':
                    self.add_purchased_coin(symbol)
                    
                    # 📊 Adicionar posição ao Portfolio Monitor
                    if self.portfolio_monitor:
                        self.portfolio_monitor.add_position(
                            symbol=symbol,
                            buy_price=float(price),
                            quantity=float(amount),
                            buy_date=trade_data['date'],
                            trade_id=order_result.get('id', str(int(time.time())))
                        )
                        log.info(f"📊 Posição adicionada ao Portfolio Monitor: {symbol}")
                        log.info(f"   🚀 Trailing Stop ativo: 1% de queda do pico máximo")
                
                # 📊 Se foi uma venda, remover posição do Portfolio Monitor
                elif action == 'sell' and self.portfolio_monitor:
                    self.portfolio_monitor.remove_position(symbol)
                    log.info(f"📊 Posição removida do Portfolio Monitor: {symbol}")
                    
            else:
                log.error(f"❌ Erro ao salvar trade: {response.status_code}")
                
        except Exception as e:
            log.error(f"❌ Erro ao salvar trade no banco: {e}")
    
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
                    
                    # Status e verificações periódicas
                    if self.cycle_count % 5 == 0:
                        # Verificar alertas de portfolio a cada 5 ciclos (CRÍTICO para stop-loss 1%)
                        alerts = self.check_portfolio_alerts()
                        if alerts:
                            log.warning(f"🚨 {len(alerts)} alertas de portfolio verificados!")
                    
                    if self.cycle_count % 10 == 0:
                        # Mostrar performance completa a cada 10 ciclos
                        log.info(f"Status: {self.cycle_count} ciclos completados")
                        self.show_portfolio_performance()
                    
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
    
    def show_purchased_coins(self):
        """Mostra a lista atual de moedas compradas"""
        if self.purchased_coins:
            log.info(f"🛡️ Moedas compradas ({len(self.purchased_coins)}): {', '.join(sorted(self.purchased_coins))}")
        else:
            log.info("🛡️ Nenhuma moeda comprada registrada")
        return list(self.purchased_coins)
    
    def remove_purchased_coin(self, symbol):
        """Remove uma moeda da lista de compradas (permite recompra)"""
        if symbol in self.purchased_coins:
            self.purchased_coins.remove(symbol)
            log.info(f"🛡️ {symbol} removida da lista de moedas compradas - recompra permitida")
            return True
        else:
            log.warning(f"🛡️ {symbol} não estava na lista de moedas compradas")
            return False
    
    def show_portfolio_performance(self):
        """Mostra performance atual do portfólio"""
        if not self.portfolio_monitor:
            log.warning("📊 Portfolio Monitor não disponível")
            return None
            
        try:
            portfolio = self.portfolio_monitor.get_portfolio_performance()
            
            log.info("📊 === PERFORMANCE DO PORTFÓLIO ===")
            log.info(f"📊 Posições ativas: {portfolio['total_positions']}")
            log.info(f"📊 Total investido: ${portfolio['total_invested']:.2f}")
            log.info(f"📊 Valor atual: ${portfolio['total_current_value']:.2f}")
            log.info(f"📊 P&L Total: ${portfolio['total_pnl']:.2f} ({portfolio['portfolio_performance_pct']:+.2f}%)")
            
            if portfolio['positions']:
                log.info("📊 === PERFORMANCE POR POSIÇÃO ===")
                for pos in portfolio['positions'][:5]:  # Mostrar top 5
                    status_emoji = {
                        'excellent': '🚀',
                        'good': '📈', 
                        'positive': '✅',
                        'slight_loss': '⚠️',
                        'loss': '📉',
                        'heavy_loss': '🚨'
                    }.get(pos['status'], '❓')
                    
                    log.info(f"📊 {status_emoji} {pos['symbol']}: {pos['performance_pct']:+.2f}% | "
                           f"${pos['pnl_usd']:+.2f} | {pos['days_held']} dias")
            
            return portfolio
            
        except Exception as e:
            log.error(f"📊 Erro ao obter performance: {e}")
            return None
    
    def check_portfolio_alerts(self):
        """Verifica alertas de stop-loss e take-profit"""
        if not self.portfolio_monitor:
            return []
            
        try:
            alerts = self.portfolio_monitor.check_alerts()
            for alert in alerts:
                if alert['type'] == 'trailing_stop':
                    log.warning(f"� ALERTA TRAILING STOP: {alert['message']}")
                    # EXECUTAR VENDA AUTOMÁTICA POR TRAILING STOP
                    self.execute_trailing_stop_sale(alert)
                elif alert['type'] == 'take_profit':
                    log.info(f"🎯 ALERTA TAKE PROFIT: {alert['message']}")
                    
            return alerts
        except Exception as e:
            log.error(f"📊 Erro ao verificar alertas: {e}")
            return []
    
    def execute_trailing_stop_sale(self, alert):
        """Executa venda automática por trailing stop"""
        try:
            symbol = alert['symbol']
            current_price = alert.get('current_price', 0)
            peak_price = alert.get('peak_price', 0)
            drop_from_peak = alert.get('drop_from_peak_pct', 0)
            peak_performance = alert.get('peak_performance_pct', 0)
            
            if current_price <= 0:
                log.error(f"❌ Preço inválido para trailing stop: {symbol}")
                return
                
            log.warning(f"🚀 EXECUTANDO TRAILING STOP AUTOMÁTICO: {symbol}")
            log.warning(f"   💎 Pico atingido: ${peak_price:.8f} (+{peak_performance:.2f}%)")
            log.warning(f"   📉 Preço atual: ${current_price:.8f}")
            log.warning(f"   🔻 Queda do pico: {abs(drop_from_peak):.2f}%")
            log.warning(f"   🛡️ PROTEGENDO LUCROS - Venda total da posição")
            
            # Criar oportunidade artificial para venda
            opportunity = {
                'symbol': symbol,
                'action': 'sell',
                'price': current_price,
                'confidence': 0.99,  # Confiança máxima para trailing stop
                'change_24h': drop_from_peak,
                'reason': f"🚀 TRAILING STOP: Caiu {abs(drop_from_peak):.2f}% do pico de +{peak_performance:.2f}%"
            }
            
            # Executar venda total
            self.execute_trade(opportunity)
            
        except Exception as e:
            log.error(f"❌ Erro ao executar trailing stop para {alert.get('symbol', 'N/A')}: {e}")

    def execute_stop_loss_sale(self, alert):
        """Executa venda automática por stop-loss de 1%"""
        try:
            symbol = alert['symbol']
            current_price = alert.get('current_price', 0)
            
            if current_price <= 0:
                log.error(f"❌ Preço inválido para stop-loss: {symbol}")
                return
                
            log.warning(f"🚨 EXECUTANDO STOP-LOSS AUTOMÁTICO: {symbol}")
            log.warning(f"   Perda atual: {alert['performance_pct']:.2f}%")
            log.warning(f"   Preço atual: ${current_price:.8f}")
            
            # Criar oportunidade artificial para venda
            opportunity = {
                'symbol': symbol,
                'action': 'sell',
                'price': current_price,
                'confidence': 0.99,  # Confiança máxima para stop-loss
                'change_24h': alert['performance_pct'],
                'reason': f"🚨 STOP-LOSS AUTOMÁTICO: {alert['performance_pct']:.2f}% de perda"
            }
            
            # Executar venda total
            self.execute_trade(opportunity)
            
        except Exception as e:
            log.error(f"❌ Erro ao executar stop-loss para {alert.get('symbol', 'N/A')}: {e}")

    def check_portfolio_alerts(self):
        """Verifica alertas de stop-loss e take-profit"""
        if not self.portfolio_monitor:
            return []
            
        try:
            alerts = self.portfolio_monitor.check_alerts()
            for alert in alerts:
                if alert['type'] == 'stop_loss':
                    log.warning(f"🚨 ALERTA STOP LOSS: {alert['message']}")
                elif alert['type'] == 'take_profit':
                    log.info(f"🎯 ALERTA TAKE PROFIT: {alert['message']}")
            return alerts
        except Exception as e:
            log.error(f"📊 Erro ao verificar alertas: {e}")
            return []

def main():
    agent = SimpleAgent()
    agent.run()

if __name__ == "__main__":
    main()
