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

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
DB_PATH = os.getenv('DB_PATH', '../memecoin.db')
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
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM trades 
            ORDER BY date DESC 
            LIMIT 50
        ''')
        
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
