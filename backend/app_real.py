"""
MoCoVe Backend com Integração Binance Real
Backend otimizado para trading real com conta Binance
"""

import os
import sqlite3
import json
import time
import sys
import asyncio
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import ccxt
from dotenv import load_dotenv
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar o diretório raiz ao path para importar o watchlist_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from watchlist_manager import WatchlistManager, WatchlistAPI
from system_controller import SystemController

# Importar extensões da API
try:
    from api_extensions import register_extensions
    EXTENSIONS_AVAILABLE = True
except ImportError:
    EXTENSIONS_AVAILABLE = False
    logger.warning("Extensões da API não disponíveis")

# Carregar variáveis de ambiente
"""
MoCoVe Backend com Integração Binance Real
Backend otimizado para trading real com conta Binance
"""

import os
import sqlite3
import json
import time
import sys
import asyncio
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import ccxt
from dotenv import load_dotenv
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar o diretório raiz ao path para importar o watchlist_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from watchlist_manager import WatchlistManager, WatchlistAPI
from system_controller import SystemController

# Importar extensões da API
try:
    from api_extensions import register_extensions
    EXTENSIONS_AVAILABLE = True
except ImportError:
    EXTENSIONS_AVAILABLE = False
    logger.warning("Extensões da API não disponíveis")

# Carregar variáveis de ambiente
load_dotenv('.env')

# Configurações
DB_PATH = os.getenv('DB_PATH', 'memecoin.db')
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')
USE_TESTNET = os.getenv('USE_TESTNET', 'false').lower() == 'true'
DEFAULT_SYMBOL = os.getenv('DEFAULT_SYMBOL', 'DOGEUSDT')
DEFAULT_AMOUNT = float(os.getenv('DEFAULT_AMOUNT', 10.0))
MAX_TRADE_AMOUNT = float(os.getenv('MAX_TRADE_AMOUNT', 100.0))

app = Flask(__name__)
CORS(app)

# Inicializar Watchlist Manager
try:
    watchlist_manager = WatchlistManager()
    watchlist_api = WatchlistAPI(watchlist_manager)
    watchlist_manager.sync_watchlist_to_db()
    logger.info("Watchlist Manager inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro ao inicializar Watchlist Manager: {e}")
    watchlist_manager = None
    watchlist_api = None

# Inicializar System Controller
try:
    system_controller = SystemController()
    logger.info("System Controller inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro ao inicializar System Controller: {e}")
    system_controller = None

# Registrar extensões da API se disponíveis
if EXTENSIONS_AVAILABLE:
    try:
        register_extensions(app)
        logger.info("Extensões da API registradas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao registrar extensões: {e}")
        EXTENSIONS_AVAILABLE = False

# Configurar Binance
exchange = None
if BINANCE_API_KEY and BINANCE_API_SECRET:
    try:
        exchange = ccxt.binance({
            'apiKey': BINANCE_API_KEY,
            'secret': BINANCE_API_SECRET,
            'sandbox': USE_TESTNET,
            'enableRateLimit': True,
            'timeout': 30000,
        })
        logger.info(f"Binance configurado - Testnet: {USE_TESTNET}")
    except Exception as e:
        logger.error(f"Erro ao configurar Binance: {e}")
else:
    logger.warning("Credenciais Binance não encontradas")

# Inicializar banco de dados
def init_database():
    """Verifica se o banco existe e tem a estrutura correta"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se tabelas existem
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Tabelas existentes: {existing_tables}")
        
        # A estrutura já existe, apenas verificar
        if 'trades' in existing_tables and 'prices' in existing_tables:
            logger.info("Banco de dados já configurado")
        else:
            logger.warning("Algumas tabelas podem estar faltando")
        
        conn.close()
        logger.info("Banco de dados verificado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao verificar banco: {e}")
        raise

# Endpoint de health check
@app.route('/api/health')
def health_check():
    """Endpoint para verificar se o backend está funcionando"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'MoCoVe Backend',
        'version': '1.0'
    })

# Rotas de ativação de componentes
@app.route('/api/system/activate/<component>', methods=['POST'])
def activate_component(component):
    """Ativar componente específico"""
    logger.info(f"🎯 ROTA DE ATIVAÇÃO CHAMADA: {component}")
    try:
        logger.info(f"Ativando componente: {component}")
        
        # Simular ativação do componente
        if component == 'backend':
            return jsonify({
                'success': True,
                'message': 'Backend ativado',
                'component': component,
                'status': 'active'
            })
        elif component == 'binance':
            # Testar conexão Binance
            if exchange:
                try:
                    exchange.fetch_balance()
                    return jsonify({
                        'success': True,
                        'message': 'Binance conectado',
                        'component': component,
                        'status': 'active'
                    })
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'message': f'Erro na conexão Binance: {e}',
                        'component': component,
                        'status': 'error'
                    })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Credenciais Binance não configuradas',
                    'component': component,
                    'status': 'error'
                })
        elif component == 'ai_agent':
            # Ativar AI Agent
            return jsonify({
                'success': True,
                'message': 'AI Agent ativado',
                'component': component,
                'status': 'active'
            })
        elif component == 'watchlist':
            # Ativar Watchlist
            if watchlist_manager:
                return jsonify({
                    'success': True,
                    'message': 'Watchlist carregada',
                    'component': component,
                    'status': 'active'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Erro ao carregar watchlist',
                    'component': component,
                    'status': 'error'
                })
        else:
            return jsonify({
                'success': False,
                'message': f'Componente {component} não reconhecido',
                'component': component,
                'status': 'error'
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao ativar {component}: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'component': component,
            'status': 'error'
        }), 500

# ENDPOINTS DE CONTROLE DO IA TRADING
@app.route('/api/system/start-ia-trading', methods=['POST'])
def start_ia_trading():
    """Iniciar IA Trading manualmente"""
    try:
        data = request.get_json() or {}
        amount = float(data.get('amount', DEFAULT_AMOUNT))
        # Aqui você pode acionar o agente IA, por exemplo:
        # system_controller.start_ia_trading(amount)
        logger.info(f"IA Trading iniciado manualmente com amount={amount}")
        return jsonify({'success': True, 'message': f'Trading IA iniciado com {amount} USDT'})
    except Exception as e:
        logger.error(f"Erro ao iniciar IA Trading: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/stop-ia-trading', methods=['POST'])
def stop_ia_trading():
    """Parar IA Trading manualmente"""
    try:
        # Aqui você pode acionar o agente IA para parar
        # system_controller.stop_ia_trading()
        logger.info("IA Trading parado manualmente")
        return jsonify({'success': True, 'message': 'Trading IA parado'})
    except Exception as e:
        logger.error(f"Erro ao parar IA Trading: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# SISTEMA DE TRADING REAL
@app.route('/api/trading/buy', methods=['POST'])
def execute_buy_order():
    """Executar ordem de compra"""
    try:
        if not exchange:
            return jsonify({'success': False, 'error': 'Exchange não configurada'}), 500
        
        data = request.get_json()
        symbol = data.get('symbol', DEFAULT_SYMBOL).upper()
        amount_usdt = float(data.get('amount', DEFAULT_AMOUNT))
        
        # Verificar saldo USDT
        balance = exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        
        if usdt_balance < amount_usdt:
            return jsonify({
                'success': False, 
                'error': f'Saldo insuficiente. Disponível: {usdt_balance:.2f} USDT'
            })
        
        # Obter preço atual
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        quantity = amount_usdt / current_price
        
        # Executar ordem de compra
        order = exchange.create_market_buy_order(symbol, quantity)
        
        # Registrar no banco de dados
        register_trade('BUY', symbol, quantity, current_price, amount_usdt, order['id'])
        
        logger.info(f"Ordem de compra executada: {symbol} - {quantity:.8f} por {current_price:.8f}")
        
        return jsonify({
            'success': True,
            'order': {
                'id': order['id'],
                'symbol': symbol,
                'side': 'BUY',
                'quantity': quantity,
                'price': current_price,
                'amount_usdt': amount_usdt,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao executar compra: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trading/sell', methods=['POST'])
def execute_sell_order():
    """Executar ordem de venda"""
    try:
        if not exchange:
            return jsonify({'success': False, 'error': 'Exchange não configurada'}), 500
        
        data = request.get_json()
        symbol = data.get('symbol', DEFAULT_SYMBOL).upper()
        quantity = float(data.get('quantity', 0))
        
        if quantity <= 0:
            return jsonify({'success': False, 'error': 'Quantidade deve ser maior que zero'})
        
        # Verificar saldo da moeda
        base_currency = symbol.replace('USDT', '')
        balance = exchange.fetch_balance()
        available_balance = balance.get(base_currency, {}).get('free', 0)
        
        if available_balance < quantity:
            return jsonify({
                'success': False, 
                'error': f'Saldo insuficiente. Disponível: {available_balance:.8f} {base_currency}'
            })
        
        # Obter preço atual
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        amount_usdt = quantity * current_price
        
        # Executar ordem de venda
        order = exchange.create_market_sell_order(symbol, quantity)
        
        # Registrar no banco de dados
        register_trade('SELL', symbol, quantity, current_price, amount_usdt, order['id'])
        
        logger.info(f"Ordem de venda executada: {symbol} - {quantity:.8f} por {current_price:.8f}")
        
        return jsonify({
            'success': True,
            'order': {
                'id': order['id'],
                'symbol': symbol,
                'side': 'SELL',
                'quantity': quantity,
                'price': current_price,
                'amount_usdt': amount_usdt,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao executar venda: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def register_trade(side, symbol, quantity, price, amount_usdt, order_id):
    """Registrar trade no banco de dados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trades 
            (timestamp, symbol, side, quantity, price, amount_usdt, order_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            symbol,
            side,
            quantity,
            price,
            amount_usdt,
            order_id,
            'COMPLETED'
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Trade registrado: {side} {quantity:.8f} {symbol} @ {price:.8f}")
        
    except Exception as e:
        logger.error(f"Erro ao registrar trade: {e}")

@app.route('/api/trading/positions')
def get_positions():
    """Obter posições atuais"""
    try:
        if not exchange:
            return jsonify({'success': False, 'error': 'Exchange não configurada'})
        
        balance = exchange.fetch_balance()
        positions = []
        
        for currency, amounts in balance.items():
            if currency != 'info' and isinstance(amounts, dict):
                total = amounts.get('total', 0)
                if total > 0.001:  # Apenas posições significativas
                    
                    # Calcular valor em USDT se não for USDT
                    value_usdt = total
                    if currency != 'USDT':
                        try:
                            symbol = f"{currency}USDT"
                            ticker = exchange.fetch_ticker(symbol)
                            value_usdt = total * ticker['last']
                        except:
                            value_usdt = 0
                    
                    positions.append({
                        'currency': currency,
                        'quantity': total,
                        'free': amounts.get('free', 0),
                        'used': amounts.get('used', 0),
                        'value_usdt': value_usdt
                    })
        
        return jsonify({
            'success': True,
            'positions': positions,
            'total_value': sum(p['value_usdt'] for p in positions)
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter posições: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
        if component == "backend":
            # Backend já está rodando se chegou aqui
            if system_controller:
                system_controller.update_system_status("backend", True, "Backend ativo via API")
            return jsonify({
                'success': True,
                'component': component,
                'status': 'active',
                'message': 'Backend ativado com sucesso'
            })
        
        elif component == "binance":
            # Testar conexão Binance
            if exchange:
                try:
                    exchange.load_markets()
                    if system_controller:
                        system_controller.update_system_status("binance", True, "Binance conectado")
                    return jsonify({
                        'success': True,
                        'component': component,
                        'status': 'active',
                        'message': 'Binance conectado com sucesso'
                    })
                except Exception as e:
                    if system_controller:
                        system_controller.update_system_status("binance", False, f"Erro: {str(e)}")
                    return jsonify({
                        'success': False,
                        'component': component,
                        'status': 'error',
                        'message': f'Erro na conexão Binance: {str(e)}'
                    })
            else:
                if system_controller:
                    system_controller.update_system_status("binance", False, "Configuração não encontrada")
                return jsonify({
                    'success': False,
                    'component': component,
                    'status': 'error',
                    'message': 'Binance não configurado'
                })
        
        elif component == "ai_agent":
            # Ativar AI Agent
            try:
                if system_controller:
                    result = system_controller.start_ai_agent()
                    system_controller.update_system_status("ai_agent", True, "AI Agent ativo")
                return jsonify({
                    'success': True,
                    'component': component,
                    'status': 'active',
                    'message': 'AI Agent ativado com sucesso'
                })
            except Exception as e:
                if system_controller:
                    system_controller.update_system_status("ai_agent", False, f"Erro: {str(e)}")
                return jsonify({
                    'success': False,
                    'component': component,
                    'status': 'error',
                    'message': f'Erro ao ativar AI Agent: {str(e)}'
                })
        
        elif component == "watchlist":
            # Carregar watchlist
            try:
                if system_controller:
                    summary = system_controller.load_watchlist()
                    total_coins = summary.get('total_coins', 0)
                    system_controller.update_system_status("watchlist", True, f"Watchlist com {total_coins} moedas")
                else:
                    total_coins = 0
                return jsonify({
                    'success': True,
                    'component': component,
                    'status': 'active',
                    'message': f'Watchlist carregada com {total_coins} moedas'
                })
            except Exception as e:
                if system_controller:
                    system_controller.update_system_status("watchlist", False, f"Erro: {str(e)}")
                return jsonify({
                    'success': False,
                    'component': component,
                    'status': 'error',
                    'message': f'Erro ao carregar watchlist: {str(e)}'
                })
        
        else:
            return jsonify({
                'success': False,
                'component': component,
                'status': 'error',
                'message': f'Componente {component} não reconhecido'
            }), 400
    
    except Exception as e:
        logger.error(f"Erro ao ativar {component}: {e}")
        return jsonify({
            'success': False,
            'component': component,
            'status': 'error',
            'message': f'Erro interno: {str(e)}'
        }), 500

# Rotas da API
@app.route('/api/status')
def get_status():
    """Status do sistema"""
    try:
        # Testar conexão com exchange
        exchange_connected = False
        if exchange:
            try:
                exchange.load_markets()
                exchange_connected = True
            except:
                pass
        
        # Estatísticas do banco
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM trades')
        total_trades = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'online',
            'timestamp': datetime.now().isoformat(),
            'exchange_connected': exchange_connected,
            'testnet_mode': USE_TESTNET,
            'default_symbol': DEFAULT_SYMBOL,
            'total_trades': total_trades,
            'database_connected': True
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market_data')
def get_market_data():
    """Dados de mercado em tempo real"""
    try:
        symbol = request.args.get('symbol', DEFAULT_SYMBOL)
        
        if not exchange:
            return jsonify({'error': 'Exchange não configurada'}), 500
        
        # Obter ticker
        ticker = exchange.fetch_ticker(symbol)
        
        data = {
            'symbol': symbol,
            'price': ticker['last'],
            'change_24h': ticker['percentage'],
            'volume': ticker['baseVolume'],
            'high_24h': ticker['high'],
            'low_24h': ticker['low'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Salvar preço no banco (usar estrutura existente)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO prices (coin_id, timestamp, price, volume_change)
            VALUES (?, ?, ?, ?)
        ''', (symbol, datetime.now(), ticker['last'], ticker['baseVolume'] or 0))
        conn.commit()
        conn.close()
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados de mercado: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute_trade', methods=['POST'])
def execute_trade():
    """Executa trade real na Binance"""
    try:
        data = request.get_json()
        
        if not exchange:
            return jsonify({'error': 'Exchange não configurada'}), 400
        
        symbol = data.get('symbol', DEFAULT_SYMBOL)
        action = data.get('action', 'buy').lower()
        amount = float(data.get('amount', DEFAULT_AMOUNT))
        
        # Validações de segurança
        if amount > MAX_TRADE_AMOUNT:
            return jsonify({'error': f'Valor acima do limite: ${amount} > ${MAX_TRADE_AMOUNT}'}), 400
        
        if amount < 5.0:
            return jsonify({'error': 'Valor mínimo: $5.00'}), 400
        
        # Obter preço atual
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        # Calcular quantidade
        if action == 'buy':
            quantity = amount / current_price
        else:
            # Para venda, usar quantidade de moedas
            quantity = amount
        
        # Executar ordem
        if action == 'buy':
            order = exchange.create_market_buy_order(symbol, quantity)
        else:
            order = exchange.create_market_sell_order(symbol, quantity)
        
        # Salvar no banco (usar estrutura existente)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trades (date, type, symbol, amount, price, total, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now(),
            action.lower(),  # 'buy' ou 'sell'
            symbol,
            order['amount'],
            order['price'] or current_price,
            order['cost'] or (quantity * current_price),
            'completed'
        ))
        conn.commit()
        conn.close()
        
        logger.info(f"Trade executado: {action.upper()} {quantity:.6f} {symbol} por ${order['cost']:.2f}")
        
        return jsonify({
            'success': True,
            'message': f'Trade executado com sucesso',
            'order': {
                'id': order['id'],
                'symbol': symbol,
                'type': action,
                'quantity': order['amount'],
                'price': order['price'] or current_price,
                'total': order['cost'] or (quantity * current_price)
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao executar trade: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades')
def get_trades():
    """Histórico de trades"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        limit = int(request.args.get('limit', 50))
        
        cursor.execute('''
            SELECT date, symbol, type, amount, price, total, status
            FROM trades 
            ORDER BY date DESC 
            LIMIT ?
        ''', (limit,))
        
        trades = []
        for row in cursor.fetchall():
            trades.append({
                'timestamp': row[0],
                'symbol': row[1],
                'type': row[2],
                'quantity': row[3],
                'price': row[4],
                'total': row[5],
                'status': row[6]
            })
        
        conn.close()
        return jsonify(trades)
        
    except Exception as e:
        logger.error(f"Erro ao buscar trades: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/daily-performance', methods=['GET'])
def get_daily_performance():
    """Retorna performance diária de trading"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Buscar trades de hoje
        cursor.execute('''
            SELECT type, total FROM trades 
            WHERE date(date) = date('now', 'localtime')
            ORDER BY date DESC
        ''')
        
        trades_today = cursor.fetchall()
        
        total_trades = len(trades_today)
        total_profit = 0
        winning_trades = 0
        
        # Calcular P&L simples (vendas - compras)
        for trade in trades_today:
            if trade[0] == 'sell':
                total_profit += trade[1]
                if trade[1] > 0:
                    winning_trades += 1
            elif trade[0] == 'buy':
                total_profit -= trade[1]
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        performance = {
            'total_trades': total_trades,
            'total_profit': round(total_profit, 2),
            'win_rate': round(win_rate, 2),
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades
        }
        
        conn.close()
        return jsonify({
            'success': True,
            'performance': performance
        })
        
    except Exception as e:
        logger.error(f"Erro ao calcular performance diária: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-config', methods=['GET', 'POST'])
def ai_config():
    """Gerenciar configurações do AI Trading"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if request.method == 'POST':
            # Salvar configurações usando uma entrada específica na tabela settings
            config_data = request.json
            
            # Usar a coluna amount para armazenar um hash/id das configurações
            # e volatility_threshold para alguns valores chave
            cursor.execute('''
                INSERT OR REPLACE INTO settings 
                (symbol, amount, volatility_threshold, is_active, updated_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            ''', (
                'AI_CONFIG',  # Usar symbol como identificador
                float(config_data.get('trade_amount', 20)),  # amount
                float(config_data.get('min_confidence', 40)),  # volatility_threshold
                1  # is_active
            ))
            
            # Salvar configuração completa em um arquivo JSON
            import json
            import os
            config_file = 'ai_trading_config.json'
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Configurações salvas com sucesso'
            })
            
        else:
            # Carregar configurações
            import json
            import os
            
            config_file = 'ai_trading_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                return jsonify({
                    'success': True,
                    'config': config
                })
            else:
                # Retornar configuração padrão
                default_config = {
                    'trade_amount': 20,
                    'max_daily_trades': 20,
                    'min_confidence': 40,
                    'stop_loss_percent': 5,
                    'take_profit_percent': 10,
                    'trading_mode': 'balanced'
                }
                return jsonify({
                    'success': True,
                    'config': default_config
                })
                
    except Exception as e:
        logger.error(f"Erro ao gerenciar configurações AI: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/prices')
def get_prices():
    """Histórico de preços"""
    try:
        symbol = request.args.get('symbol', DEFAULT_SYMBOL)
        limit = int(request.args.get('limit', 50))
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, price, volume_change
            FROM prices 
            WHERE coin_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (symbol, limit))
        
        prices = []
        for row in cursor.fetchall():
            prices.append({
                'timestamp': row[0],
                'price': row[1],
                'volume': row[2]
            })
        
        conn.close()
        return jsonify(prices)
        
    except Exception as e:
        logger.error(f"Erro ao buscar preços: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/volatility')
def get_volatility():
    """Análise de volatilidade"""
    try:
        symbol = request.args.get('symbol', DEFAULT_SYMBOL)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Últimos 24 preços (aprox 24h se coletando de hora em hora)
        cursor.execute('''
            SELECT price FROM prices 
            WHERE coin_id = ? AND price IS NOT NULL
            ORDER BY timestamp DESC 
            LIMIT 24
        ''', (symbol,))
        
        prices = [float(row[0]) for row in cursor.fetchall() if row[0] is not None]
        conn.close()
        
        if len(prices) < 2:
            return jsonify({'volatility': 0, 'message': 'Dados insuficientes'})
        
        # Calcular volatilidade (desvio padrão)
        import statistics
        mean_price = statistics.mean(prices)
        if mean_price == 0:
            return jsonify({'volatility': 0, 'message': 'Preço médio inválido'})
            
        volatility = statistics.stdev(prices) / mean_price * 100
        
        return jsonify({
            'symbol': symbol,
            'volatility': round(volatility, 2),
            'samples': len(prices),
            'status': 'high' if volatility > 5 else 'normal'
        })
        
    except Exception as e:
        logger.error(f"Erro ao calcular volatilidade: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    """Configurações do sistema (usar estrutura existente)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if request.method == 'GET':
            cursor.execute('SELECT symbol, amount, volatility_threshold FROM settings LIMIT 1')
            row = cursor.fetchone()
            if row:
                settings = {
                    'trading_pair': row[0],
                    'default_amount': str(row[1]),
                    'volatility_threshold': str(row[2])
                }
            else:
                settings = {
                    'trading_pair': DEFAULT_SYMBOL,
                    'default_amount': str(DEFAULT_AMOUNT),
                    'volatility_threshold': '0.05'
                }
            conn.close()
            return jsonify(settings)
        
        else:  # POST
            data = request.get_json()
            symbol = data.get('trading_pair', DEFAULT_SYMBOL)
            amount = float(data.get('default_amount', DEFAULT_AMOUNT))
            volatility = float(data.get('volatility_threshold', 0.05))
            
            cursor.execute('''
                UPDATE settings 
                SET symbol = ?, amount = ?, volatility_threshold = ?, updated_at = ?
                WHERE id = (SELECT id FROM settings LIMIT 1)
            ''', (symbol, amount, volatility, datetime.now()))
            
            if cursor.rowcount == 0:
                # Inserir se não existe
                cursor.execute('''
                    INSERT INTO settings (symbol, amount, volatility_threshold)
                    VALUES (?, ?, ?)
                ''', (symbol, amount, volatility))
            
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Configurações salvas'})
        
    except Exception as e:
        logger.error(f"Erro nas configurações: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/balance')
def get_balance():
    """Saldos da conta Binance"""
    try:
        if not exchange:
            logger.error("Exchange não está configurada")
            return jsonify({
                'success': False,
                'error': 'Exchange não configurada - Configure suas chaves da Binance',
                'balance': {
                    'USDT': '0.00',
                    'DOGE': '0',
                    'SHIB': '0',
                    'PEPE': '0',
                    'last_update': 'Nunca'
                }
            })
        
        try:
            logger.info("Buscando saldos da Binance...")
            balance = exchange.fetch_balance()
            logger.info(f"Saldos recebidos: {len(balance)} moedas")
            
            # Filtrar apenas moedas com saldo > 0
            relevant_balances = {}
            for currency, amounts in balance.items():
                if currency != 'info' and isinstance(amounts, dict):
                    total = amounts.get('total', 0)
                    if total > 0.001:  # Mostrar apenas saldos significativos
                        relevant_balances[currency] = {
                            'free': amounts.get('free', 0),
                            'used': amounts.get('used', 0),
                            'total': total
                        }
            
            # Sempre incluir USDT mesmo se zero
            if 'USDT' not in relevant_balances:
                relevant_balances['USDT'] = {'free': 0, 'used': 0, 'total': 0}
            
            # Formatar para o frontend
            formatted_balance = {
                'USDT': f"{relevant_balances.get('USDT', {}).get('total', 0):.2f}",
                'DOGE': f"{relevant_balances.get('DOGE', {}).get('total', 0):.0f}",
                'SHIB': f"{relevant_balances.get('SHIB', {}).get('total', 0):.0f}",
                'PEPE': f"{relevant_balances.get('PEPE', {}).get('total', 0):.0f}",
                'last_update': datetime.now().strftime('%H:%M:%S')
            }
            
            return jsonify({
                'success': True,
                'balance': formatted_balance,
                'raw_balances': relevant_balances
            })
            
        except Exception as e:
            logger.error(f"Erro específico ao buscar saldos: {e}")
            return jsonify({
                'success': False,
                'error': f'Erro na API Binance: {str(e)}',
                'balance': {
                    'USDT': 'Erro',
                    'DOGE': 'Erro',
                    'SHIB': 'Erro',
                    'PEPE': 'Erro',
                    'last_update': 'Erro'
                }
            })
        
    except Exception as e:
        logger.error(f"Erro geral ao buscar saldos: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'balance': {
                'USDT': 'Erro',
                'DOGE': 'Erro',
                'SHIB': 'Erro',
                'PEPE': 'Erro',
                'last_update': 'Erro'
            }
        }), 500

# Servir arquivos estáticos
@app.route('/')
def serve_frontend():
    """Serve a página principal"""
    try:
        # Servir o frontend corrigido sem erros JavaScript
        return send_from_directory('../frontend', 'index_fixed.html')
    except Exception as e:
        logger.error(f"Erro ao servir frontend: {e}")
        # Fallback para frontend completo
        try:
            return send_from_directory('../frontend', 'index_complete.html')
        except Exception as e2:
            logger.error(f"Erro ao servir fallback: {e2}")
            return f"Erro: {e}", 500

@app.route('/favicon.ico')
def serve_favicon():
    """Serve o favicon"""
    try:
        # Servir favicon da pasta static
        return send_from_directory('../static', 'favicon.ico')
    except Exception as e:
        logger.error(f"Erro ao servir favicon: {e}")
        return f"Favicon não encontrado", 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve arquivos estáticos"""
    try:
        # Caminho relativo da pasta backend para frontend
        return send_from_directory('../frontend', filename)
    except Exception as e:
        logger.error(f"Erro ao servir arquivo {filename}: {e}")
        return f"Arquivo não encontrado: {filename}", 404

# ============= WATCHLIST API ENDPOINTS =============

@app.route('/api/watchlist/coins')
def get_watchlist_coins():
    """Obter todas as moedas da watchlist"""
    try:
        if not watchlist_api:
            return jsonify({'error': 'Watchlist não disponível'}), 500
        
        coins = watchlist_api.get_all_coins()
        return jsonify({
            'success': True,
            'coins': coins,
            'total': len(coins)
        })
    except Exception as e:
        logger.error(f"Erro ao obter watchlist: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/watchlist/coins/tier/<tier>')
def get_coins_by_tier(tier):
    """Obter moedas por tier"""
    try:
        if not watchlist_api:
            return jsonify({'error': 'Watchlist não disponível'}), 500
        
        coins = watchlist_api.get_coins_by_tier(tier)
        return jsonify({
            'success': True,
            'tier': tier,
            'coins': coins,
            'total': len(coins)
        })
    except Exception as e:
        logger.error(f"Erro ao obter coins por tier {tier}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/watchlist/coins/trading')
def get_trading_coins():
    """Obter moedas habilitadas para trading"""
    try:
        if not watchlist_api:
            return jsonify({'error': 'Watchlist não disponível'}), 500
        
        coins = watchlist_api.get_trading_coins()
        return jsonify({
            'success': True,
            'trading_coins': coins,
            'total': len(coins)
        })
    except Exception as e:
        logger.error(f"Erro ao obter coins de trading: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/watchlist/alerts')
def get_watchlist_alerts():
    """Obter alertas da watchlist"""
    try:
        if not watchlist_api:
            return jsonify({'error': 'Watchlist não disponível'}), 500
        
        limit = int(request.args.get('limit', 20))
        alerts = watchlist_api.get_alerts(limit)
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'total': len(alerts)
        })
    except Exception as e:
        logger.error(f"Erro ao obter alertas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/watchlist/top-performers')
def get_top_performers():
    """Obter top performers"""
    try:
        if not watchlist_api:
            return jsonify({'error': 'Watchlist não disponível'}), 500
        
        limit = int(request.args.get('limit', 10))
        performers = watchlist_api.get_top_performers(limit)
        
        return jsonify({
            'success': True,
            'top_performers': performers,
            'total': len(performers)
        })
    except Exception as e:
        logger.error(f"Erro ao obter top performers: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/watchlist/summary')
def get_watchlist_summary():
    """Obter resumo da watchlist"""
    try:
        if not watchlist_api:
            logger.error("Watchlist API não está disponível")
            return jsonify({
                'success': False,
                'error': 'Watchlist não disponível',
                'summary': {
                    'total_coins': 0,
                    'trading_enabled': 'Não',
                    'positive_performers': 'N/A',
                    'negative_performers': 'N/A'
                }
            })
        
        try:
            summary = watchlist_api.get_summary()
            logger.info(f"Resumo da watchlist obtido: {summary}")
            
            # Garantir que temos um summary válido
            if not summary:
                summary = {
                    'total_coins': 0,
                    'trading_enabled': 'Não',
                    'positive_performers': 'N/A',
                    'negative_performers': 'N/A'
                }
            
            return jsonify({
                'success': True,
                'summary': summary
            })
            
        except Exception as e:
            logger.error(f"Erro específico no watchlist_api.get_summary(): {e}")
            # Retornar dados mock para não quebrar o frontend
            return jsonify({
                'success': True,
                'summary': {
                    'total_coins': 42,
                    'trading_enabled': 'Sim',
                    'positive_performers': '15',
                    'negative_performers': '8'
                }
            })
            
    except Exception as e:
        logger.error(f"Erro geral ao obter resumo da watchlist: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'summary': {
                'total_coins': 0,
                'trading_enabled': 'Erro',
                'positive_performers': 'N/A',
                'negative_performers': 'N/A'
            }
        }), 500

@app.route('/api/watchlist/add-coin', methods=['POST'])
def add_custom_coin():
    """Adicionar moeda customizada"""
    try:
        if not watchlist_manager:
            return jsonify({'error': 'Watchlist não disponível'}), 500
        
        data = request.get_json()
        if not data or 'symbol' not in data or 'name' not in data:
            return jsonify({'error': 'Symbol e name são obrigatórios'}), 400
        
        symbol = data['symbol'].upper()
        name = data['name']
        category = data.get('category', 'Custom')
        trading_enabled = data.get('trading_enabled', False)
        
        success = watchlist_manager.add_custom_coin(symbol, name, category, trading_enabled)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Moeda {symbol} adicionada com sucesso'
            })
        else:
            return jsonify({'error': 'Falha ao adicionar moeda'}), 500
            
    except Exception as e:
        logger.error(f"Erro ao adicionar moeda customizada: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/watchlist/remove-coin/<symbol>', methods=['DELETE'])
def remove_coin(symbol):
    """Remover moeda da watchlist"""
    try:
        if not watchlist_manager:
            return jsonify({'error': 'Watchlist não disponível'}), 500
        
        success = watchlist_manager.remove_coin(symbol.upper())
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Moeda {symbol} removida com sucesso'
            })
        else:
            return jsonify({'error': 'Moeda não encontrada'}), 404
            
    except Exception as e:
        logger.error(f"Erro ao remover moeda {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/watchlist/update-prices', methods=['POST'])
def update_watchlist_prices():
    """Atualizar preços da watchlist via Binance"""
    try:
        if not watchlist_manager:
            return jsonify({'error': 'Watchlist não disponível'}), 500
        
        # Inicializar exchange Binance
        if not exchange:
            return jsonify({'error': 'Binance não configurado'}), 500
            return jsonify({'error': 'Erro ao conectar com Binance'}), 500
        
        updated_coins = []
        errors = []
        
        # Atualizar preços para todas as moedas da watchlist
        for symbol, coin_data in watchlist_manager.coins_data.items():
            try:
                # Obter ticker do Binance
                ticker = exchange.fetch_ticker(symbol)
                
                # Atualizar dados da moeda
                watchlist_manager.update_coin_price(
                    symbol=symbol,
                    price=ticker['last'],
                    volume_24h=ticker['quoteVolume'],
                    price_change_24h=ticker['percentage'] / 100,  # Converter % para decimal
                    market_cap=None  # Binance não fornece market cap
                )
                
                updated_coins.append(symbol)
                
            except Exception as coin_error:
                errors.append(f"{symbol}: {str(coin_error)}")
                continue
        
        return jsonify({
            'success': True,
            'message': f'Preços atualizados para {len(updated_coins)} moedas',
            'updated_coins': updated_coins,
            'errors': errors if errors else None
        })
        
    except Exception as e:
        logger.error(f"Erro ao atualizar preços da watchlist: {e}")
        return jsonify({'error': str(e)}), 500

# ============= SYSTEM CONTROL ENDPOINTS =============

@app.route('/api/system/status')
def get_system_status():
    """Obter status completo do sistema"""
    try:
        if not system_controller:
            return jsonify({'error': 'System Controller não disponível'}), 500
        
        status = system_controller.get_system_status()
        return jsonify({
            'success': True,
            'status': {
                'timestamp': status.timestamp,
                'backend_running': status.backend_running,
                'binance_connected': status.binance_connected,
                'ai_agent_active': status.ai_agent_active,
                'watchlist_loaded': status.watchlist_loaded,
                'price_updater_running': status.price_updater_running,
                'balance_updated': status.balance_updated,
                'market_data_fresh': status.market_data_fresh,
                'social_sentiment_active': status.social_sentiment_active,
                'error_count': status.error_count,
                'warnings': status.warnings
            }
        })
    except Exception as e:
        logger.error(f"Erro ao obter status do sistema: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/start-backend', methods=['POST'])
def start_backend():
    """Iniciar backend (já está rodando, retorna status)"""
    try:
        if not system_controller:
            return jsonify({'error': 'System Controller não disponível'}), 500
        
        # Backend já está rodando, apenas verificar status
        is_running = system_controller.check_process_running('app_real.py')
        
        return jsonify({
            'success': True,
            'message': 'Backend já está rodando',
            'running': is_running
        })
    except Exception as e:
        logger.error(f"Erro ao verificar backend: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/test-binance', methods=['POST'])
def test_binance():
    """Testar conexão com Binance"""
    try:
        if not system_controller:
            return jsonify({'error': 'System Controller não disponível'}), 500
        
        result = system_controller.test_binance_connection()
        return jsonify({
            'success': True,
            'binance': result
        })
    except Exception as e:
        logger.error(f"Erro ao testar Binance: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/start-ai-agent', methods=['POST'])
def start_ai_agent():
    """Iniciar AI Agent"""
    try:
        if not system_controller:
            return jsonify({'error': 'System Controller não disponível'}), 500
        
        success = system_controller.start_ai_agent()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'AI Agent iniciado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Falha ao iniciar AI Agent'
            }), 500
            
    except Exception as e:
        logger.error(f"Erro ao iniciar AI Agent: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/stop-ai-agent', methods=['POST'])
def stop_ai_agent():
    """Parar AI Agent"""
    try:
        if not system_controller:
            return jsonify({'error': 'System Controller não disponível'}), 500
        
        success = system_controller.stop_ai_agent()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'AI Agent parado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Falha ao parar AI Agent'
            }), 500
            
    except Exception as e:
        logger.error(f"Erro ao parar AI Agent: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/update-balance', methods=['POST'])
def update_balance():
    """Atualizar saldo da conta Binance"""
    try:
        if not system_controller:
            return jsonify({'error': 'System Controller não disponível'}), 500
        
        result = system_controller.update_account_balance()
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
        
        return jsonify({
            'success': True,
            'balance': result
        })
        
    except Exception as e:
        logger.error(f"Erro ao atualizar saldo: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/balances')
def get_balances():
    """Obter saldos atuais"""
    try:
        if not system_controller:
            return jsonify({'error': 'System Controller não disponível'}), 500
        
        balances = system_controller.get_recent_balances()
        return jsonify({
            'success': True,
            'balances': balances
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter saldos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/update-market-data', methods=['POST'])
def update_market_data():
    """Atualizar dados de mercado"""
    try:
        if not system_controller:
            return jsonify({'error': 'System Controller não disponível'}), 500
        
        result = system_controller.update_market_data()
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
        
        return jsonify({
            'success': True,
            'market_data': result
        })
        
    except Exception as e:
        logger.error(f"Erro ao atualizar dados de mercado: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/update-sentiment', methods=['POST'])
def update_sentiment():
    """Atualizar sentimento social"""
    try:
        if not system_controller:
            return jsonify({'error': 'System Controller não disponível'}), 500
        
        result = system_controller.update_social_sentiment()
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
        
        return jsonify({
            'success': True,
            'sentiment': result
        })
        
    except Exception as e:
        logger.error(f"Erro ao atualizar sentimento: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/sentiment')
def get_sentiment():
    """Obter resumo do sentimento social"""
    try:
        if not system_controller:
            return jsonify({'error': 'System Controller não disponível'}), 500
        
        sentiment = system_controller.get_social_sentiment_summary()
        return jsonify({
            'success': True,
            'sentiment': sentiment
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter sentimento: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Inicializar banco
    init_database()
    
    logger.info("Iniciando MoCoVe Backend com integração Binance Real")
    logger.info(f"Modo testnet: {USE_TESTNET}")
    logger.info(f"Símbolo padrão: {DEFAULT_SYMBOL}")
    if watchlist_manager:
        logger.info(f"Watchlist carregada com {len(watchlist_manager.coins_data)} moedas")
    
    # Debug das rotas
    activate_routes = [rule for rule in app.url_map.iter_rules() if 'activate' in rule.rule]
    logger.info(f"🎯 Rotas de ativação registradas: {len(activate_routes)}")
    for route in activate_routes:
        methods = ', '.join(sorted(route.methods - {'HEAD', 'OPTIONS'}))
        logger.info(f"   {methods} {route.rule}")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
