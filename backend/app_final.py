"""
MoCoVe Backend - Sistema de Trading Automatizado de Memecoins (FINAL)
Backend Flask com endpoints essenciais + botão trading real
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
    'sandbox': USE_TESTNET,
    'enableRateLimit': True,
})

def init_database():
    """Inicializa o banco de dados SQLite com as tabelas necessárias"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de preços
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            volume REAL,
            change_24h REAL
        )
    ''')
    
    # Tabela de trades
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            amount REAL NOT NULL,
            price REAL NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'pending',
            profit_loss REAL DEFAULT 0.0
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Status geral do sistema"""
    try:
        # Verificar se o AI agent está ativo via timestamp do log
        ai_agent_active = False
        log_file = os.path.join(PROJECT_ROOT, 'ai_trading_agent_robust.log')
        
        if os.path.exists(log_file):
            # Se log foi modificado nos últimos 2 minutos, considera ativo
            stat = os.stat(log_file)
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            if (datetime.now() - last_modified).total_seconds() < 120:
                ai_agent_active = True
        
        # Verificar conexão Binance
        binance_connection = False
        if USE_TESTNET:
            binance_connection = True  # Testnet sempre conectado
        else:
            try:
                exchange.fetch_balance()
                binance_connection = True
            except:
                binance_connection = False
        
        status = {
            'api_server': True,
            'ai_agent_active': ai_agent_active,
            'binance_connection': binance_connection,
            'database_connected': os.path.exists(DB_PATH),
            'testnet_mode': USE_TESTNET,
            'last_check': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/balance', methods=['GET'])
def get_balance():
    """Retorna saldo da carteira"""
    try:
        if USE_TESTNET:
            # Simular saldo para testnet
            balance = {
                'USDT': {'free': 1000.00, 'used': 0.00, 'total': 1000.00},
                'DOGE': {'free': 4500.00, 'used': 0.00, 'total': 4500.00}
            }
        else:
            # Saldo real
            balance = exchange.fetch_balance()
        
        return jsonify({
            'success': True,
            'balance': balance,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter saldo: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-robust-log', methods=['GET'])
def get_ai_robust_log():
    """Retorna os logs do AI Agent robusto"""
    try:
        log_file = os.path.join(PROJECT_ROOT, 'ai_trading_agent_robust.log')
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # Pegar apenas as últimas 1000 linhas para não sobrecarregar
            lines = log_content.split('\n')
            if len(lines) > 1000:
                lines = lines[-1000:]
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

@app.route('/api/trading/mode', methods=['GET', 'POST'])
def trading_mode():
    """Gerenciar modo de trading (testnet/real)"""
    global exchange, USE_TESTNET
    config_file = os.path.join(PROJECT_ROOT, 'trading_config.json')
    
    if request.method == 'GET':
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            else:
                config = {'testnet_mode': USE_TESTNET, 'has_credentials': False}
            
            # Verificar se tem credenciais configuradas
            has_credentials = bool(BINANCE_API_KEY and BINANCE_API_SECRET)
            config['has_credentials'] = has_credentials
            config['testnet_mode'] = USE_TESTNET
            config['current_mode'] = 'testnet' if USE_TESTNET else 'real'
            
            return jsonify({
                'success': True,
                'config': config,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Erro ao obter modo de trading: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            new_testnet_mode = data.get('testnet_mode', True)
            
            # Verificar credenciais se for modo real
            if not new_testnet_mode and not (BINANCE_API_KEY and BINANCE_API_SECRET):
                return jsonify({
                    'success': False, 
                    'error': 'Credenciais Binance não configuradas. Configure as variáveis BINANCE_API_KEY e BINANCE_API_SECRET.'
                }), 400
            
            # Salvar configuração
            config = {
                'testnet_mode': new_testnet_mode,
                'last_updated': datetime.now().isoformat(),
                'has_credentials': bool(BINANCE_API_KEY and BINANCE_API_SECRET)
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Atualizar exchange
            USE_TESTNET = new_testnet_mode
            exchange = ccxt.binance({
                'apiKey': BINANCE_API_KEY,
                'secret': BINANCE_API_SECRET,
                'sandbox': USE_TESTNET,
                'enableRateLimit': True,
            })
            
            mode_text = 'Testnet' if new_testnet_mode else 'Real Trading'
            logger.info(f"Modo de trading alterado para: {mode_text}")
            
            return jsonify({
                'success': True,
                'message': f"Modo alterado para {mode_text}",
                'config': config,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Erro ao alterar modo de trading: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

# Servir arquivos estáticos do frontend
@app.route('/')
def serve_frontend():
    """Serve a página principal do frontend"""
    return send_from_directory('../frontend', 'dashboard_pro.html')

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
