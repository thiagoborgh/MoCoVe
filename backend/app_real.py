#!/usr/bin/env python3
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
import subprocess
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import ccxt
from dotenv import load_dotenv
import logging
import json as _json

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização do app Flask
app = Flask(__name__)
CORS(app)

# Adicionar o diretório raiz ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from watchlist_manager import WatchlistManager, WatchlistAPI
except ImportError:
    logger.warning("WatchlistManager não disponível")
    WatchlistManager = None
    WatchlistAPI = None

try:
    from system_controller import SystemController
except ImportError:
    logger.warning("SystemController não disponível")
    SystemController = None

# Importar extensões da API
try:
    from api_extensions import register_extensions
    EXTENSIONS_AVAILABLE = True
except ImportError:
    EXTENSIONS_AVAILABLE = False
    logger.warning("Extensões da API não disponíveis")

# Carregar variáveis de ambiente
from pathlib import Path
dotenv_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path)

# Configurações
DB_PATH = os.getenv('DB_PATH', 'memecoin.db')
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')
USE_TESTNET = os.getenv('USE_TESTNET', 'false').lower() == 'true'
DEFAULT_SYMBOL = os.getenv('DEFAULT_SYMBOL', 'DOGEUSDT')
DEFAULT_AMOUNT = float(os.getenv('DEFAULT_AMOUNT', 10.0))
MAX_TRADE_AMOUNT = float(os.getenv('MAX_TRADE_AMOUNT', 100.0))

# Variáveis globais para controle do AI Agent
ai_agent_process = None
ai_agent_active = False

# === Endpoints de Configuração da IA ===
@app.route('/api/ai-config', methods=['GET'])
def get_ai_config():
    """Retorna as configurações atuais da IA (ai_agent_config.json)"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'ai_agent_config.json')
    if not os.path.exists(config_path):
        # Criar configuração padrão se não existir
        default_config = {
            "trading_enabled": False,
            "symbol": "DOGEUSDT",
            "monitoring_interval": 30,
            "min_confidence": 0.7,
            "max_position_size": 50.0,
            "max_daily_trades": 10,
            "stop_loss_pct": 0.02,
            "take_profit_pct": 0.03,
            "min_trade_interval": 300,
            "risk_level": "conservative",
            "strategies_enabled": {
                "moving_averages": True,
                "rsi": True,
                "bollinger_bands": True,
                "trend_following": True,
                "volatility_filter": True
            },
            "notifications": {
                "trade_execution": True,
                "high_confidence_signals": True,
                "daily_summary": True
            }
        }
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                _json.dump(default_config, f, indent=2, ensure_ascii=False)
            return jsonify({'success': True, 'config': default_config})
        except Exception as e:
            logger.error(f"Erro ao criar config padrão: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = _json.load(f)
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        logger.error(f"Erro ao ler config IA: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-config', methods=['POST'])
def update_ai_config():
    """Atualiza as configurações da IA (ai_agent_config.json)"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'ai_agent_config.json')
    try:
        data = request.get_json()
        if not data or 'config' not in data:
            return jsonify({'success': False, 'error': 'Dados de configuração ausentes'}), 400
        with open(config_path, 'w', encoding='utf-8') as f:
            _json.dump(data['config'], f, indent=2, ensure_ascii=False)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erro ao atualizar config IA: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Endpoint do log do agente robusto IA
@app.route('/api/ai-robust-log')
def get_ai_robust_log():
    """Retorna as últimas linhas do log do AI Trading Agent Robusto"""
    log_path = os.path.join(os.path.dirname(__file__), '..', 'ai_trading_agent_robust.log')
    try:
        lines = []
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                # Pega as últimas 50 linhas
                lines = f.readlines()[-50:]
        return jsonify({
            'success': True,
            'log': '\n'.join([line.strip() for line in lines if line.strip()])
        })
    except Exception as e:
        logger.error(f"Erro ao ler log robusto: {e}")
        return jsonify({'success': False, 'error': str(e), 'log': ''}), 500

# === Controle do AI Agent ===
@app.route('/api/system/start-ai-agent', methods=['POST'])
def start_ai_agent():
    """Inicia o AI Trading Agent Robusto"""
    global ai_agent_process, ai_agent_active
    
    try:
        if ai_agent_process and ai_agent_process.poll() is None:
            return jsonify({'success': False, 'message': 'AI Agent já está rodando'})
        
        # Caminho para o agente robusto
        agent_script = os.path.join(os.path.dirname(__file__), '..', 'ai_trading_agent_robust.py')
        
        if not os.path.exists(agent_script):
            return jsonify({'success': False, 'message': 'Script do AI Agent não encontrado'})
        
        # Iniciar o processo
        ai_agent_process = subprocess.Popen([sys.executable, agent_script])
        ai_agent_active = True
        
        logger.info(f"AI Trading Agent iniciado com PID: {ai_agent_process.pid}")
        return jsonify({'success': True, 'message': 'AI Agent iniciado com sucesso', 'pid': ai_agent_process.pid})
        
    except Exception as e:
        logger.error(f"Erro ao iniciar AI Agent: {e}")
        ai_agent_active = False
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/system/stop-ai-agent', methods=['POST'])
def stop_ai_agent():
    """Para o AI Trading Agent"""
    global ai_agent_process, ai_agent_active
    
    try:
        if ai_agent_process and ai_agent_process.poll() is None:
            ai_agent_process.terminate()
            try:
                ai_agent_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                ai_agent_process.kill()
                ai_agent_process.wait()
            
            logger.info("AI Trading Agent parado")
            ai_agent_active = False
            ai_agent_process = None
            return jsonify({'success': True, 'message': 'AI Agent parado com sucesso'})
        else:
            ai_agent_active = False
            ai_agent_process = None
            return jsonify({'success': False, 'message': 'AI Agent não estava rodando'})
            
    except Exception as e:
        logger.error(f"Erro ao parar AI Agent: {e}")
        ai_agent_active = False
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/system/status')
def get_system_status():
    """Status completo do sistema"""
    global ai_agent_process, ai_agent_active
    
    # Verificar se o processo ainda está ativo
    if ai_agent_process and ai_agent_process.poll() is not None:
        ai_agent_active = False
        ai_agent_process = None
    
    try:
        # Verificar conexão Binance
        binance_connected = False
        try:
            if BINANCE_API_KEY and BINANCE_API_SECRET:
                exchange = ccxt.binance({
                    'apiKey': BINANCE_API_KEY,
                    'secret': BINANCE_API_SECRET,
                    'sandbox': USE_TESTNET
                })
                exchange.check_required_credentials()
                balance = exchange.fetch_balance()
                binance_connected = True
        except Exception as e:
            logger.warning(f"Binance não conectada: {e}")
        
        # Verificar se a watchlist está carregada
        watchlist_loaded = False
        if WatchlistManager:
            try:
                wm = WatchlistManager()
                watchlist_loaded = len(wm.watchlist) > 0
            except:
                pass
        
        status = {
            'success': True,
            'status': {
                'timestamp': datetime.now().isoformat(),
                'backend_running': True,
                'binance_connected': binance_connected,
                'ai_agent_active': ai_agent_active and (ai_agent_process and ai_agent_process.poll() is None),
                'watchlist_loaded': watchlist_loaded,
                'balance_updated': datetime.now().strftime('%H:%M:%S'),
                'market_data_fresh': True,
                'error_count': 0,
                'warnings': []
            }
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'status': {
                'timestamp': datetime.now().isoformat(),
                'backend_running': True,
                'binance_connected': False,
                'ai_agent_active': False,
                'watchlist_loaded': False,
                'balance_updated': "Erro",
                'market_data_fresh': False,
                'error_count': 1,
                'warnings': [str(e)]
            }
        })

# === Endpoints básicos ===
@app.route('/')
def serve_frontend():
    """Servir o frontend"""
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_from_directory(frontend_path, 'index_complete_dashboard_clean.html')

@app.route('/favicon.ico')
def favicon():
    """Servir favicon"""
    try:
        return send_from_directory(
            os.path.join(os.path.dirname(__file__), '..', 'static'), 
            'favicon.ico', 
            mimetype='image/vnd.microsoft.icon'
        )
    except:
        # Retornar um favicon vazio se não encontrar
        return '', 204

@app.route('/api/health')
def health_check():
    """Health check do backend"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# === Endpoints de trading simulado ===
@app.route('/api/market_data')
def get_market_data():
    """Dados de mercado simulados"""
    try:
        symbol = request.args.get('symbol', 'DOGEUSDT')
        
        # Dados simulados para teste
        market_data = {
            'symbol': symbol,
            'price': 0.08234,
            'change_24h': 2.5,
            'volume': 125000000,
            'high_24h': 0.08456,
            'low_24h': 0.07891,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(market_data)
        
    except Exception as e:
        logger.error(f"Erro ao obter market data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/prices')
def get_prices():
    """Histórico de preços simulado"""
    try:
        symbol = request.args.get('symbol', 'DOGEUSDT')
        limit = request.args.get('limit', 60, type=int)
        
        # Preços simulados
        base_price = 0.08234
        prices = []
        
        for i in range(limit):
            price = base_price + (i * 0.0001) + (0.001 * (i % 3 - 1))
            prices.append({
                'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(),
                'price': round(price, 6),
                'volume': 1000000 + (i * 10000)
            })
        
        return jsonify(prices)
        
    except Exception as e:
        logger.error(f"Erro ao obter prices: {e}")
        return jsonify([])
@app.route('/api/trades')
def get_trades():
    """Retorna lista de trades (simulado)"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        # Trades simulados para teste
        trades = [
            {
                'id': f'trade_{i}',
                'symbol': 'DOGEUSDT',
                'type': 'buy' if i % 2 == 0 else 'sell',
                'amount': 10.0 + (i * 0.5),
                'price': 0.08 + (i * 0.001),
                'timestamp': (datetime.now() - timedelta(hours=i)).isoformat()
            }
            for i in range(min(limit, 10))
        ]
        
        return jsonify(trades)
        
    except Exception as e:
        logger.error(f"Erro ao obter trades: {e}")
        return jsonify([])

@app.route('/api/trades/daily-performance')
def get_daily_performance():
    """Performance diária simulada"""
    try:
        performance = {
            'total_trades': 5,
            'total_profit': 12.50,
            'win_rate': 80.0,
            'best_trade': 8.75
        }
        return jsonify({'success': True, 'performance': performance})
        
    except Exception as e:
        logger.error(f"Erro ao calcular performance: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/balance')
def get_balance():
    """Saldo da conta (simulado)"""
    try:
        balance = {
            'USDT': '150.25',
            'DOGE': '1500.00',
            'SHIB': '0.00',
            'PEPE': '0.00',
            'last_update': datetime.now().strftime('%H:%M:%S')
        }
        return jsonify({'success': True, 'balance': balance})
        
    except Exception as e:
        logger.error(f"Erro ao obter saldo: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/watchlist/summary')
def get_watchlist_summary():
    """Resumo da watchlist"""
    try:
        summary = {
            'total_coins': 10,
            'trading_enabled': 8,
            'positive_performers': 6,
            'negative_performers': 2,
            'last_updated': datetime.now().isoformat()
        }
        return jsonify({'success': True, 'summary': summary})
        
    except Exception as e:
        logger.error(f"Erro ao obter watchlist: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Inicializar componentes
try:
    if WatchlistManager:
        watchlist_manager = WatchlistManager()
        watchlist_api = WatchlistAPI(watchlist_manager)
        logger.info("WatchlistManager inicializado")
except Exception as e:
    logger.error(f"Erro ao inicializar WatchlistManager: {e}")
    watchlist_manager = None
    watchlist_api = None

try:
    if SystemController:
        system_controller = SystemController()
        logger.info("SystemController inicializado")
except Exception as e:
    logger.error(f"Erro ao inicializar SystemController: {e}")
    system_controller = None

# Registrar extensões da API se disponíveis
if EXTENSIONS_AVAILABLE:
    try:
        register_extensions(app)
        logger.info("Extensões da API registradas")
    except Exception as e:
        logger.error(f"Erro ao registrar extensões: {e}")

if __name__ == '__main__':
    logger.info("🚀 Iniciando MoCoVe Backend...")
    logger.info(f"📊 Database: {DB_PATH}")
    logger.info(f"🔗 Binance: {'Testnet' if USE_TESTNET else 'Mainnet'}")
    logger.info(f"💰 Símbolo padrão: {DEFAULT_SYMBOL}")
    
    # Iniciar servidor
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("⏹️ Servidor parado pelo usuário")
        if ai_agent_process:
            ai_agent_process.terminate()
    except Exception as e:
        logger.error(f"❌ Erro no servidor: {e}")
