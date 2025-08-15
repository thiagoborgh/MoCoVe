"""
MoCoVe Backend - Sistema de Trading Automatizado de Memecoins
Backend Flask com endpoints para monitoramento, negociação e configuração
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import ccxt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
import pathlib
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
DB_PATH = os.getenv('DB_PATH', str(PROJECT_ROOT / 'memecoin.db'))
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')
USE_TESTNET = os.getenv('USE_TESTNET', 'true').lower() == 'true'

app = Flask(__name__)
CORS(app)

# Configurar Binance (Testnet)
exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_API_SECRET,
    'sandbox': USE_TESTNET,  # True para testnet
    'enableRateLimit': True,
})

# Inicializar banco de dados
def init_database():
    """Inicializa o banco de dados SQLite com as tabelas necessárias"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de preços
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            price REAL NOT NULL,
            volume REAL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de negociações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATETIME NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('buy', 'sell')),
            symbol TEXT NOT NULL,
            amount REAL NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'completed',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de configurações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            amount REAL NOT NULL,
            volatility_threshold REAL NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Configuração padrão se não existir
    cursor.execute('SELECT COUNT(*) FROM settings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO settings (symbol, amount, volatility_threshold)
            VALUES ('DOGE/BUSD', 100, 0.05)
        ''')
    
    conn.commit()
    conn.close()
    logger.info("Banco de dados inicializado com sucesso")

# Funções auxiliares
def get_db_connection():
    """Retorna conexão com o banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
    return conn

def calculate_volatility(prices: List[float]) -> float:
    """Calcula volatilidade baseada nos últimos preços"""
    if len(prices) < 2:
        return 0.0
    
    returns = []
    for i in range(1, len(prices)):
        if prices[i-1] != 0:
            return_val = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(abs(return_val))
    
    return np.mean(returns) if returns else 0.0

def get_latest_prices(symbol: str, limit: int = 10) -> List[float]:
    """Obtém os últimos preços de um símbolo"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT price FROM prices 
        WHERE symbol = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (symbol, limit))
    
    prices = [row['price'] for row in cursor.fetchall()]
    conn.close()
    
    return prices[::-1]  # Reverter para ordem cronológica

# Endpoints da API

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Retorna lista de negociações"""
    try:
        # Pega o parâmetro 'limit' da query string, padrão 50
        limit = request.args.get('limit', default=50, type=int)
        if not limit or limit < 1 or limit > 500:
            limit = 50

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT * FROM trades 
            ORDER BY date DESC 
            LIMIT ?
        ''', (limit,))

        trades = []
        for row in cursor.fetchall():
            trades.append({
                'id': row['id'],
                'date': row['date'],
                'type': row['type'],
                'symbol': row['symbol'],
                'amount': row['amount'],
                'price': row['price'],
                'total': row['total'],
                'status': row['status']
            })

        conn.close()
        return jsonify(trades)

    except Exception as e:
        logger.error(f"Erro ao buscar negociações: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/daily-performance', methods=['GET'])
def get_daily_performance():
    """Retorna performance diária de trading"""
    try:
        conn = get_db_connection()
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
            if trade['type'] == 'sell':
                total_profit += trade['total']
                if trade['total'] > 0:
                    winning_trades += 1
            elif trade['type'] == 'buy':
                total_profit -= trade['total']
        
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
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if request.method == 'POST':
            # Salvar configurações
            config_data = request.json
            
            # Criar ou atualizar configuração
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, datetime('now'))
            ''', ('ai_trading_config', str(config_data)))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Configurações salvas com sucesso'
            })
            
        else:
            # Carregar configurações
            cursor.execute('''
                SELECT value FROM settings 
                WHERE key = 'ai_trading_config'
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                import ast
                config = ast.literal_eval(result['value'])
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

@app.route('/api/prices', methods=['GET'])
def get_prices():
    """Retorna histórico de preços"""
    try:
        symbol = request.args.get('symbol', 'DOGE/BUSD')
        limit = int(request.args.get('limit', 50))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM prices 
            WHERE symbol = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (symbol, limit))
        
        prices = []
        for row in cursor.fetchall():
            prices.append({
                'id': row['id'],
                'symbol': row['symbol'],
                'timestamp': row['timestamp'],
                'price': row['price'],
                'volume': row['volume']
            })
        
        conn.close()
        return jsonify(prices[::-1])  # Ordem cronológica
        
    except Exception as e:
        logger.error(f"Erro ao buscar preços: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/volatility', methods=['GET'])
def get_volatility():
    """Retorna volatilidade atual"""
    try:
        symbol = request.args.get('symbol', 'DOGE/BUSD')
        prices = get_latest_prices(symbol, 10)
        
        volatility = calculate_volatility(prices)
        current_price = prices[-1] if prices else 0
        
        # Verificar se volatilidade está acima do threshold
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT volatility_threshold FROM settings WHERE symbol = ?', (symbol,))
        result = cursor.fetchone()
        threshold = result['volatility_threshold'] if result else 0.05
        conn.close()
        
        is_high = volatility > threshold
        
        return jsonify({
            'symbol': symbol,
            'volatility': volatility,
            'threshold': threshold,
            'is_high': is_high,
            'current_price': current_price,
            'price_count': len(prices)
        })
        
    except Exception as e:
        logger.error(f"Erro ao calcular volatilidade: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    """GET: Retorna configurações / POST: Atualiza configurações"""
    try:
        if request.method == 'GET':
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM settings WHERE is_active = 1 ORDER BY id DESC LIMIT 1')
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return jsonify({
                    'id': result['id'],
                    'symbol': result['symbol'],
                    'amount': result['amount'],
                    'volatility_threshold': result['volatility_threshold'],
                    'is_active': bool(result['is_active'])
                })
            else:
                return jsonify({'error': 'Nenhuma configuração encontrada'}), 404
                
        elif request.method == 'POST':
            data = request.get_json()
            symbol = data.get('symbol', 'DOGE/BUSD')
            amount = float(data.get('amount', 100))
            volatility_threshold = float(data.get('volatility_threshold', 0.05))
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Desativar configurações anteriores
            cursor.execute('UPDATE settings SET is_active = 0')
            
            # Inserir nova configuração
            cursor.execute('''
                INSERT INTO settings (symbol, amount, volatility_threshold, is_active, updated_at)
                VALUES (?, ?, ?, 1, ?)
            ''', (symbol, amount, volatility_threshold, datetime.now()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Configurações atualizadas: {symbol}, {amount}, {volatility_threshold}")
            
            return jsonify({
                'message': 'Configurações atualizadas com sucesso',
                'symbol': symbol,
                'amount': amount,
                'volatility_threshold': volatility_threshold
            })
            
    except Exception as e:
        logger.error(f"Erro ao lidar com configurações: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute_trade', methods=['POST'])
def execute_trade():
    """Executa uma negociação manual"""
    try:
        data = request.get_json()
        trade_type = data.get('type')  # 'buy' ou 'sell'
        symbol = data.get('symbol', 'DOGE/BUSD')
        amount = float(data.get('amount', 0))

        # Valor mínimo por trade
        MIN_TRADE_AMOUNT = 5.10
        if amount < MIN_TRADE_AMOUNT:
            return jsonify({'error': f'Valor mínimo por trade é ${MIN_TRADE_AMOUNT:.2f}'}), 400

        if not trade_type or amount <= 0:
            return jsonify({'error': 'Tipo de negociação e quantidade são obrigatórios'}), 400
        
        # Buscar preço atual (simulado para testnet)
        ticker = exchange.fetch_ticker(symbol.replace('/', ''))
        current_price = ticker['last']
        
        if not current_price:
            return jsonify({'error': 'Não foi possível obter o preço atual'}), 500
        
        # Para testnet, simular ordem
        if USE_TESTNET:
            order = {
                'id': f'test_{datetime.now().timestamp()}',
                'symbol': symbol,
                'type': 'market',
                'side': trade_type,
                'amount': amount,
                'price': current_price,
                'status': 'closed',
                'filled': amount,
                'cost': amount * current_price
            }
        else:
            # Para produção, executar ordem real
            if trade_type == 'buy':
                order = exchange.create_market_buy_order(symbol, amount)
            else:
                order = exchange.create_market_sell_order(symbol, amount)
        
        # Registrar no banco de dados
        total = amount * current_price
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trades (date, type, symbol, amount, price, total)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now(), trade_type, symbol, amount, current_price, total))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Negociação executada: {trade_type} {amount} {symbol} @ {current_price}")
        
        return jsonify({
            'success': True,
            'order': order,
            'message': f'Ordem de {trade_type} executada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao executar negociação: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market_data', methods=['GET'])
def get_market_data():
    """Retorna dados de mercado em tempo real"""
    try:
        symbol = request.args.get('symbol', 'DOGE/BUSD')
        
        # Buscar dados do exchange
        ticker = exchange.fetch_ticker(symbol.replace('/', ''))
        
        # Salvar preço no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO prices (symbol, timestamp, price, volume)
            VALUES (?, ?, ?, ?)
        ''', (symbol, datetime.now(), ticker['last'], ticker['baseVolume'] or 0))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'symbol': symbol,
            'price': ticker['last'],
            'high': ticker['high'],
            'low': ticker['low'],
            'volume': ticker['baseVolume'],
            'change': ticker['change'],
            'percentage': ticker['percentage'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados de mercado: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Retorna status do sistema"""
    try:
        # Verificar conexão com exchange
        exchange_status = True
        try:
            exchange.fetch_status()
        except:
            exchange_status = False
        
        # Contar registros no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM prices')
        prices_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM trades')
        trades_count = cursor.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'status': 'online',
            'exchange_connected': exchange_status,
            'testnet_mode': USE_TESTNET,
            'database': {
                'prices_count': prices_count,
                'trades_count': trades_count
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Retorna status detalhado do sistema"""
    try:
        # Verificar se o AI trading está ativo verificando logs recentes
        ai_agent_active = True  # Temporariamente sempre true para debugging
        log_path = r'C:\Users\Thiago Borgueti\MoCoVe\ai_trading_agent_robust.log'
        
        if os.path.exists(log_path):
            try:
                # Verificar se há logs dos últimos 2 minutos
                import time
                file_mod_time = os.path.getmtime(log_path)
                current_time = time.time()
                # Se o arquivo foi modificado nos últimos 120 segundos, considerar ativo
                time_diff = current_time - file_mod_time
                ai_agent_active = time_diff < 120
                logger.info(f"AI Agent log check: exists={os.path.exists(log_path)}, time_diff={time_diff:.0f}s, active={ai_agent_active}")
            except Exception as e:
                logger.error(f"Erro ao verificar AI agent: {e}")
                ai_agent_active = False
        else:
            logger.warning(f"AI Agent log file not found: {log_path}")
            ai_agent_active = False
        
        # Verificar conexão com exchange
        exchange_connected = True
        try:
            if hasattr(exchange, 'fetch_status'):
                exchange.fetch_status()
        except:
            exchange_connected = False
        
        return jsonify({
            'success': True,
            'status': {
                'api_server': True,
                'database': True,
                'binance_connection': exchange_connected,
                'ai_agent_active': ai_agent_active,
                'trading_enabled': True
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar status do sistema: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/balance', methods=['GET'])
def get_balance():
    """Retorna saldo da conta"""
    try:
        if USE_TESTNET:
            # Simular saldo para testnet
            balance = {
                'USDT': {'free': 1000.0, 'used': 50.0, 'total': 1050.0},
                'DOGE': {'free': 5000.0, 'used': 0.0, 'total': 5000.0}
            }
        else:
            balance = exchange.fetch_balance()
        
        return jsonify({
            'success': True,
            'balance': balance,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter saldo: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/watchlist/summary', methods=['GET'])
def get_watchlist_summary():
    """Retorna resumo da watchlist"""
    try:
        # Simulado por agora
        summary = {
            'total_coins': 5,
            'monitored': 3,
            'active_trades': 1,
            'top_performer': {'symbol': 'DOGE', 'change': 2.5}
        }
        
        return jsonify({
            'success': True,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter resumo da watchlist: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trading/positions', methods=['GET'])
def get_positions():
    """Retorna posições atuais"""
    try:
        # Simulado por agora
        positions = [
            {
                'symbol': 'DOGE/USDT',
                'side': 'long',
                'size': 1000.0,
                'entry_price': 0.08,
                'current_price': 0.082,
                'pnl': 20.0,
                'pnl_pct': 2.5
            }
        ]
        
        return jsonify({
            'success': True,
            'positions': positions,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter posições: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/market_data/top_performers', methods=['GET'])
def get_top_performers():
    """Retorna top performers do mercado"""
    try:
        # Simulado por agora
        performers = [
            {'symbol': 'DOGE', 'change_24h': 2.5, 'price': 0.082},
            {'symbol': 'SHIB', 'change_24h': 1.8, 'price': 0.000015},
            {'symbol': 'PEPE', 'change_24h': -1.2, 'price': 0.0000012}
        ]
        
        return jsonify({
            'success': True,
            'performers': performers,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter top performers: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sentiment/summary', methods=['GET'])
def get_sentiment_summary():
    """Retorna resumo do sentimento social"""
    try:
        # Simulado por agora
        sentiments = [
            {'platform': 'Twitter', 'sentiment': 'Positive', 'score': 0.7},
            {'platform': 'Reddit', 'sentiment': 'Neutral', 'score': 0.5},
            {'platform': 'Telegram', 'sentiment': 'Positive', 'score': 0.8}
        ]
        
        return jsonify({
            'success': True,
            'sentiments': sentiments,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter sentimento: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-config', methods=['GET', 'POST'])
def handle_ai_config():
    """Gerencia configurações da IA"""
    try:
        if request.method == 'GET':
            # Configuração padrão da IA
            config = {
                'trading_enabled': True,
                'symbol': 'DOGE/USDT',
                'monitoring_interval': 30,
                'min_confidence': 0.7,
                'max_position_size': 50.0,
                'max_daily_trades': 10,
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.03,
                'min_trade_interval': 300,
                'risk_level': 'medium',
                'strategies_enabled': {
                    'trend_following': True,
                    'mean_reversion': False,
                    'momentum': True
                },
                'notifications': {
                    'trade_executed': True,
                    'error_alerts': True,
                    'daily_summary': False
                }
            }
            
            return jsonify({
                'success': True,
                'config': config,
                'timestamp': datetime.now().isoformat()
            })
            
        elif request.method == 'POST':
            # Salvar configuração (por agora só simula)
            data = request.get_json()
            config = data.get('config', {})
            
            # Aqui você salvaria a configuração no banco de dados
            logger.info(f"Configuração da IA atualizada: {config}")
            
            return jsonify({
                'success': True,
                'message': 'Configuração salva com sucesso',
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Erro ao gerenciar configurações AI: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-robust-log', methods=['GET'])
def get_ai_robust_log():
    """Retorna os logs do AI Agent robusto"""
    try:
        log_file = os.path.join(PROJECT_ROOT, 'ai_trading_agent_robust.log')
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # Pegar apenas as últimas 2000 linhas para não sobrecarregar
            lines = log_content.split('\n')
            if len(lines) > 2000:
                lines = lines[-2000:]
                log_content = '\n'.join(lines)
            
            return jsonify({
                'success': True,
                'log': log_content,
                'file_size': len(log_content),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': True,
                'log': 'Log file not found - AI Agent may not have started yet.',
                'file_size': 0,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Erro ao ler logs do AI Agent: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/model/info', methods=['GET'])
def get_model_info():
    """Retorna informações sobre o modelo treinado"""
    try:
        metadata_file = os.path.join(PROJECT_ROOT, 'artifacts', 'memecoin_model_metadata.json')
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return jsonify({
                'success': True,
                'model_info': metadata,
                'model_exists': True,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': True,
                'model_info': {
                    'status': 'not_trained',
                    'message': 'Modelo ainda não foi treinado'
                },
                'model_exists': False,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Erro ao obter informações do modelo: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trading/history', methods=['GET'])
def get_trading_history():
    """Retorna histórico de trades executados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Buscar trades mais recentes
        cursor.execute('''
            SELECT id, symbol, side, amount, price, timestamp, status, profit_loss
            FROM trades 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''')
        
        trades = []
        for row in cursor.fetchall():
            trades.append({
                'id': row[0],
                'symbol': row[1],
                'side': row[2],
                'amount': row[3],
                'price': row[4],
                'timestamp': row[5],
                'status': row[6],
                'profit_loss': row[7]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'trades': trades,
            'count': len(trades),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter histórico de trades: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/market/data/<symbol>', methods=['GET'])
def get_market_data_by_symbol(symbol):
    """Retorna dados de mercado para um símbolo específico"""
    try:
        # Para testnet, simular dados
        if USE_TESTNET:
            # Simular dados de mercado realistas
            base_price = 0.225 if symbol == 'DOGEUSDT' else 1.0
            current_price = base_price + (np.random.random() - 0.5) * 0.01
            
            market_data = {
                'symbol': symbol,
                'price': round(current_price, 6),
                'change_24h': round((np.random.random() - 0.5) * 0.1, 4),
                'volume_24h': round(np.random.random() * 1000000, 2),
                'high_24h': round(current_price * 1.05, 6),
                'low_24h': round(current_price * 0.95, 6),
                'bid': round(current_price * 0.999, 6),
                'ask': round(current_price * 1.001, 6),
                'timestamp': datetime.now().isoformat()
            }
        else:
            # Dados reais da Binance
            ticker = exchange.fetch_ticker(symbol)
            market_data = {
                'symbol': symbol,
                'price': ticker['last'],
                'change_24h': ticker['percentage'],
                'volume_24h': ticker['quoteVolume'],
                'high_24h': ticker['high'],
                'low_24h': ticker['low'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'timestamp': datetime.now().isoformat()
            }
        
        return jsonify({
            'success': True,
            'market_data': market_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter dados de mercado para {symbol}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/metrics', methods=['GET'])
def get_system_metrics():
    """Retorna métricas detalhadas do sistema"""
    try:
        # Calcular uptime do arquivo de log
        log_file = os.path.join(PROJECT_ROOT, 'ai_trading_agent_robust.log')
        uptime_hours = 0
        last_activity = None
        
        if os.path.exists(log_file):
            stat = os.stat(log_file)
            file_age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)
            uptime_hours = file_age.total_seconds() / 3600
            last_activity = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        # Contar trades no banco
        total_trades = 0
        successful_trades = 0
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM trades')
            total_trades = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'filled'")
            successful_trades = cursor.fetchone()[0]
            
            conn.close()
        except:
            pass
        
        metrics = {
            'uptime_hours': round(uptime_hours, 2),
            'last_activity': last_activity,
            'total_trades': total_trades,
            'successful_trades': successful_trades,
            'success_rate': round((successful_trades / max(total_trades, 1)) * 100, 2),
            'ai_cycles_completed': max(total_trades, 0),
            'system_load': round(np.random.random() * 30 + 10, 2),  # Simulated
            'memory_usage': round(np.random.random() * 40 + 30, 2),  # Simulated
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas do sistema: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-trading/toggle', methods=['POST'])
def toggle_ai_trading():
    """Liga/desliga o AI Trading Agent"""
    try:
        data = request.get_json()
        enable = data.get('enable', True)
        
        if enable:
            # Iniciar AI Agent
            import subprocess
            import sys
            
            agent_path = os.path.join(PROJECT_ROOT, 'ai_trading_agent_robust.py')
            
            if os.path.exists(agent_path):
                # Verificar se já está rodando
                log_file = os.path.join(PROJECT_ROOT, 'ai_trading_agent_robust.log')
                is_running = False
                
                if os.path.exists(log_file):
                    stat = os.stat(log_file)
                    last_modified = datetime.fromtimestamp(stat.st_mtime)
                    time_diff = (datetime.now() - last_modified).total_seconds()
                    is_running = time_diff < 120  # Ativo se modificado nos últimos 2 minutos
                
                if is_running:
                    return jsonify({
                        'success': True,
                        'message': 'AI Trading Agent já está ativo',
                        'status': 'running'
                    })
                
                # Iniciar o agent em background
                try:
                    subprocess.Popen([
                        sys.executable, agent_path
                    ], cwd=PROJECT_ROOT, 
                       stdout=subprocess.DEVNULL, 
                       stderr=subprocess.DEVNULL)
                    
                    logger.info("AI Trading Agent iniciado com sucesso")
                    return jsonify({
                        'success': True,
                        'message': 'AI Trading Agent iniciado com sucesso',
                        'status': 'starting'
                    })
                    
                except Exception as e:
                    logger.error(f"Erro ao iniciar AI Agent: {str(e)}")
                    return jsonify({
                        'success': False,
                        'error': f'Erro ao iniciar AI Agent: {str(e)}'
                    }), 500
            else:
                return jsonify({
                    'success': False,
                    'error': 'Arquivo do AI Agent não encontrado'
                }), 404
        else:
            # Parar AI Agent (isso é mais complexo, por agora apenas informamos)
            return jsonify({
                'success': True,
                'message': 'Para parar o AI Agent, feche o processo manualmente',
                'status': 'stop_requested'
            })
            
    except Exception as e:
        logger.error(f"Erro ao controlar AI trading: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-trading/status', methods=['GET'])
def get_ai_trading_status():
    """Retorna o status atual do AI Trading Agent"""
    try:
        log_file = os.path.join(PROJECT_ROOT, 'ai_trading_agent_robust.log')
        
        status = {
            'is_running': False,
            'last_activity': None,
            'uptime_minutes': 0,
            'message': 'AI Agent inativo'
        }
        
        if os.path.exists(log_file):
            stat = os.stat(log_file)
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            time_diff = (datetime.now() - last_modified).total_seconds()
            
            status['last_activity'] = last_modified.isoformat()
            status['uptime_minutes'] = int(time_diff / 60)
            
            if time_diff < 120:  # Ativo se modificado nos últimos 2 minutos
                status['is_running'] = True
                status['message'] = f'AI Agent ativo - última atividade há {int(time_diff)}s'
            else:
                status['message'] = f'AI Agent inativo - última atividade há {int(time_diff / 60)} minutos'
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar status do AI trading: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trading/mode', methods=['GET', 'POST'])
def trading_mode():
    """GET: Retorna modo atual / POST: Altera modo de trading"""
    global USE_TESTNET, exchange  # Declarar no início da função
    
    try:
        if request.method == 'GET':
            # Retorna o modo atual baseado nas variáveis de ambiente
            return jsonify({
                'success': True,
                'config': {
                    'testnet_mode': USE_TESTNET,
                    'current_mode': 'testnet' if USE_TESTNET else 'real',
                    'has_credentials': bool(BINANCE_API_KEY and BINANCE_API_SECRET)
                },
                'timestamp': datetime.now().isoformat()
            })
            
        elif request.method == 'POST':
            data = request.get_json()
            new_testnet_mode = data.get('testnet_mode', True)
            
            # Verificar se tem credenciais para modo real
            if not new_testnet_mode and not (BINANCE_API_KEY and BINANCE_API_SECRET):
                return jsonify({
                    'success': False,
                    'error': 'Credenciais Binance não configuradas. Configure as variáveis BINANCE_API_KEY e BINANCE_API_SECRET.'
                }), 400
            
            # Alterar o modo de trading dinamicamente
            try:
                # Atualizar variável global
                USE_TESTNET = new_testnet_mode
                
                # Reconfigurar o exchange com o novo modo
                exchange = ccxt.binance({
                    'apiKey': BINANCE_API_KEY,
                    'secret': BINANCE_API_SECRET,
                    'sandbox': USE_TESTNET,
                    'enableRateLimit': True,
                })
                
                # Atualizar arquivo .env para persistir a mudança
                env_path = os.path.join(PROJECT_ROOT, '.env')
                if os.path.exists(env_path):
                    # Ler o arquivo .env atual
                    with open(env_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Atualizar a linha USE_TESTNET
                    updated_lines = []
                    found_testnet = False
                    
                    for line in lines:
                        if line.startswith('USE_TESTNET='):
                            updated_lines.append(f'USE_TESTNET={"true" if new_testnet_mode else "false"}\n')
                            found_testnet = True
                        else:
                            updated_lines.append(line)
                    
                    # Se não encontrou a linha, adicionar
                    if not found_testnet:
                        updated_lines.append(f'USE_TESTNET={"true" if new_testnet_mode else "false"}\n')
                    
                    # Escrever de volta
                    with open(env_path, 'w', encoding='utf-8') as f:
                        f.writelines(updated_lines)
                
                mode_text = 'testnet' if new_testnet_mode else 'real'
                logger.info(f"Modo de trading alterado para: {mode_text}")
                
                return jsonify({
                    'success': True,
                    'message': f'Modo alterado para {mode_text} com sucesso!',
                    'config': {
                        'testnet_mode': new_testnet_mode,
                        'current_mode': mode_text,
                        'has_credentials': bool(BINANCE_API_KEY and BINANCE_API_SECRET)
                    }
                })
                
            except Exception as e:
                logger.error(f"Erro ao alterar modo de trading: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Erro ao alterar modo: {str(e)}'
                }), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint trading/mode: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Servir arquivos estáticos do frontend
@app.route('/')
def serve_frontend():
    """Serve a página principal do frontend"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve arquivos estáticos do frontend"""
    return send_from_directory('../frontend', filename)

# Inicialização
if __name__ == '__main__':
    init_database()
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Iniciando MoCoVe Backend na porta {port}")
    logger.info(f"Modo testnet: {USE_TESTNET}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
