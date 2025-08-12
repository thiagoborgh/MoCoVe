#!/usr/bin/env python3
"""
Backend de Diagnóstico - MoCoVe
Versão simplificada sem Binance para diagnosticar problemas
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import logging
import os
from datetime import datetime

# Configuração
app = Flask(__name__)
CORS(app)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = 'memecoin.db'

@app.route('/api/status')
def status():
    """Status simples sem Binance"""
    logger.info("Endpoint status chamado")
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'exchange_connected': False,  # Sem Binance para teste
        'testnet_mode': True,
        'default_symbol': 'DOGEUSDT',
        'total_trades': 0
    })

@app.route('/api/trades')
def get_trades():
    """Trades do banco de dados"""
    logger.info("Endpoint trades chamado")
    try:
        if not os.path.exists(DB_PATH):
            return jsonify([])
        
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, action, amount, price, timestamp, profit_loss
            FROM trades 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''')
        
        trades = []
        for row in cursor.fetchall():
            trades.append({
                'symbol': row[0],
                'action': row[1], 
                'amount': row[2],
                'price': row[3],
                'timestamp': row[4],
                'profit_loss': row[5]
            })
        
        conn.close()
        logger.info(f"Retornando {len(trades)} trades")
        return jsonify(trades)
    
    except Exception as e:
        logger.error(f"Erro ao buscar trades: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/prices')
def get_prices():
    """Preços do banco de dados"""
    logger.info("Endpoint prices chamado")
    symbol = request.args.get('symbol', 'DOGEUSDT')
    limit = request.args.get('limit', 50)
    
    try:
        if not os.path.exists(DB_PATH):
            return jsonify([])
            
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT price, timestamp FROM prices 
            WHERE coin_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (symbol, limit))
        
        prices = []
        for row in cursor.fetchall():
            prices.append({
                'price': row[0],
                'timestamp': row[1]
            })
        
        conn.close()
        logger.info(f"Retornando {len(prices)} preços para {symbol}")
        return jsonify(prices)
    
    except Exception as e:
        logger.error(f"Erro ao buscar preços: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/volatility')
def get_volatility():
    """Volatilidade simples"""
    logger.info("Endpoint volatility chamado")
    return jsonify({
        'symbol': 'DOGEUSDT',
        'volatility': 2.5,
        'samples': 10,
        'status': 'normal',
        'message': 'Modo diagnóstico'
    })

@app.route('/api/settings')
def get_settings():
    """Configurações simples"""
    logger.info("Endpoint settings chamado")
    return jsonify({
        'symbol': 'DOGEUSDT',
        'amount': '10.00',
        'volatility_threshold': '0.05'
    })

@app.route('/api/market_data')
def get_market_data():
    """Dados de mercado simulados"""
    logger.info("Endpoint market_data chamado")
    return jsonify({
        'symbol': 'DOGEUSDT',
        'price': '0.22500',
        'change_24h': '2.34',
        'volume': '1234567',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/')
def index():
    """Página principal"""
    try:
        return app.send_static_file('index.html')
    except:
        return '''
        <html><body>
        <h1>MoCoVe - Diagnóstico</h1>
        <p>Backend funcionando em modo diagnóstico</p>
        <p>APIs disponíveis:</p>
        <ul>
            <li><a href="/api/status">/api/status</a></li>
            <li><a href="/api/trades">/api/trades</a></li>
            <li><a href="/api/volatility">/api/volatility</a></li>
            <li><a href="/api/settings">/api/settings</a></li>
        </ul>
        </body></html>
        '''

if __name__ == '__main__':
    logger.info("Iniciando Backend de Diagnóstico")
    logger.info("Sem integração Binance - apenas dados locais")
    
    # Configurar Flask para servir arquivos estáticos
    app.static_folder = '../frontend'
    app.static_url_path = ''
    
    app.run(host='0.0.0.0', port=5000, debug=False)
