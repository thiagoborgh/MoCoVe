#!/usr/bin/env python3
"""
API Extensions para MoCoVe AI Trading System
Novas rotas para configuração do agente, sentimento social, etc.
"""

from flask import Blueprint, request, jsonify
import json
import os
import requests
from datetime import datetime, timedelta
import sqlite3
import logging

# Blueprint para as novas APIs
api_ext = Blueprint('api_ext', __name__)
logger = logging.getLogger(__name__)

# Configurações
CONFIG_FILE = "ai_agent_config.json"
SENTIMENT_CACHE_FILE = "sentiment_cache.json"

class AgentConfigManager:
    """Gerenciador de configurações do agente"""
    
    def __init__(self):
        self.default_config = {
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
            },
            "watchlist": [
                "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "XRPUSDT", "DOGEUSDT", "SHIBUSDT",
                "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT", "LTCUSDT", "BCHUSDT", "UNIUSDT", "PEPEUSDT",
                "FLOKIUSDT", "WIFUSDT", "BONKUSDT", "MEMEUSDT", "SAFEUSDT", "BRETTUSDT", "POPCATUSDT",
                "MEWUSDT", "AAVEUSDT", "COMPUSDT", "FETUSDT", "OPUSDT", "ARBUSDT", "SUIUSDT", "TIAUSDT",
                "SEIUSDT", "JUPUSDT", "PYTHUSDT", "RNDRUSDT", "INJUSDT", "STXUSDT", "ETCUSDT", "FILUSDT",
                "TRXUSDT", "NEARUSDT", "ATOMUSDT", "VETUSDT", "XLMUSDT", "ALGOUSDT", "GRTUSDT", "MKRUSDT",
                "SNXUSDT", "DYDXUSDT", "LDOUSDT", "APTUSDT", "IMXUSDT", "SANDUSDT", "AXSUSDT", "GMTUSDT",
                "ENJUSDT", "CHZUSDT", "CRVUSDT", "1INCHUSDT", "CAKEUSDT", "RUNEUSDT", "ZILUSDT", "XEMUSDT"
            ],
            "social_sentiment_weight": 0.2
        }
    
    def load_config(self):
        """Carrega configurações"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar config: {e}")
                return self.default_config.copy()
        return self.default_config.copy()
    
    def save_config(self, config):
        """Salva configurações"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar config: {e}")
            return False

class SocialSentimentAnalyzer:
    """Analisador de sentimento das redes sociais"""
    
    def __init__(self):
        self.cache_duration = 300  # 5 minutos
    
    def get_cached_sentiment(self):
        """Obtém sentimento do cache"""
        if os.path.exists(SENTIMENT_CACHE_FILE):
            try:
                with open(SENTIMENT_CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    
                cache_time = datetime.fromisoformat(data.get('timestamp', '2000-01-01'))
                if (datetime.now() - cache_time).total_seconds() < self.cache_duration:
                    return data.get('sentiment', {})
            except Exception as e:
                logger.error(f"Erro ao ler cache de sentimento: {e}")
        
        return None
    
    def save_sentiment_cache(self, sentiment):
        """Salva sentimento no cache"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'sentiment': sentiment
            }
            with open(SENTIMENT_CACHE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar cache de sentimento: {e}")
    
    def analyze_twitter_sentiment(self, symbol):
        """Analisa sentimento do Twitter (simulado)"""
        # Em produção, integrar com Twitter API
        import random
        return {
            'score': round(random.uniform(0.3, 0.9), 2),
            'mentions': random.randint(100, 1000),
            'trend': random.choice(['up', 'down', 'stable'])
        }
    
    def analyze_reddit_sentiment(self, symbol):
        """Analisa sentimento do Reddit (simulado)"""
        # Em produção, integrar com Reddit API
        import random
        return {
            'score': round(random.uniform(0.2, 0.8), 2),
            'posts': random.randint(50, 500),
            'trend': random.choice(['up', 'down', 'stable'])
        }
    
    def analyze_telegram_sentiment(self, symbol):
        """Analisa sentimento do Telegram (simulado)"""
        # Em produção, integrar com Telegram API
        import random
        return {
            'score': round(random.uniform(0.4, 0.95), 2),
            'messages': random.randint(200, 2000),
            'trend': random.choice(['up', 'down', 'stable'])
        }
    
    def get_overall_sentiment(self, symbol='DOGE'):
        """Obtém sentimento geral das redes sociais"""
        # Verificar cache primeiro
        cached = self.get_cached_sentiment()
        if cached:
            return cached
        
        try:
            twitter = self.analyze_twitter_sentiment(symbol)
            reddit = self.analyze_reddit_sentiment(symbol)
            telegram = self.analyze_telegram_sentiment(symbol)
            
            # Calcular sentimento médio ponderado
            weights = {'twitter': 0.4, 'reddit': 0.3, 'telegram': 0.3}
            overall_score = (
                twitter['score'] * weights['twitter'] +
                reddit['score'] * weights['reddit'] +
                telegram['score'] * weights['telegram']
            )
            
            sentiment = {
                'twitter': twitter,
                'reddit': reddit,
                'telegram': telegram,
                'overall': round(overall_score, 2),
                'timestamp': datetime.now().isoformat()
            }
            
            # Salvar no cache
            self.save_sentiment_cache(sentiment)
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Erro ao analisar sentimento: {e}")
            return {
                'twitter': {'score': 0.5, 'mentions': 0, 'trend': 'stable'},
                'reddit': {'score': 0.5, 'posts': 0, 'trend': 'stable'},
                'telegram': {'score': 0.5, 'messages': 0, 'trend': 'stable'},
                'overall': 0.5,
                'timestamp': datetime.now().isoformat()
            }

class MemecoinTracker:
    """Rastreador de memecoins"""
    
    def __init__(self):
        self.popular_memecoins = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "XRPUSDT", "DOGEUSDT", "SHIBUSDT",
            "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT", "LTCUSDT", "BCHUSDT", "UNIUSDT", "PEPEUSDT",
            "FLOKIUSDT", "WIFUSDT", "BONKUSDT", "MEMEUSDT", "SAFEUSDT", "BRETTUSDT", "POPCATUSDT",
            "MEWUSDT", "AAVEUSDT", "COMPUSDT", "FETUSDT", "OPUSDT", "ARBUSDT", "SUIUSDT", "TIAUSDT",
            "SEIUSDT", "JUPUSDT", "PYTHUSDT", "RNDRUSDT", "INJUSDT", "STXUSDT", "ETCUSDT", "FILUSDT",
            "TRXUSDT", "NEARUSDT", "ATOMUSDT", "VETUSDT", "XLMUSDT", "ALGOUSDT", "GRTUSDT", "MKRUSDT",
            "SNXUSDT", "DYDXUSDT", "LDOUSDT", "APTUSDT", "IMXUSDT", "SANDUSDT", "AXSUSDT", "GMTUSDT",
            "ENJUSDT", "CHZUSDT", "CRVUSDT", "1INCHUSDT", "CAKEUSDT", "RUNEUSDT", "ZILUSDT", "XEMUSDT"
        ]
    
    def get_memecoin_data(self, symbol):
        """Obtém dados de uma memecoin específica"""
        try:
            # Em produção, buscar dados reais da API
            import random
            
            base_price = {
                'DOGEUSDT': 0.224,
                'SHIBUSDT': 0.000024,
                'PEPEUSDT': 0.0000012,
                'FLOKIUSDT': 0.000045,
                'BONKUSDT': 0.000018,
                'WIFUSDT': 2.45,
                'BOMEUSDT': 0.012
            }.get(symbol, 0.001)
            
            change = random.uniform(-15, 20)
            volume = random.randint(1000000, 100000000)
            
            return {
                'symbol': symbol,
                'price': round(base_price * (1 + change/100), 8),
                'change_24h': round(change, 2),
                'volume_24h': volume,
                'market_cap': volume * base_price * random.randint(100, 1000),
                'sentiment_score': round(random.uniform(0.2, 0.9), 2),
                'social_mentions': random.randint(100, 5000),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter dados da memecoin {symbol}: {e}")
            return None
    
    def get_trending_memecoins(self):
        """Obtém lista de memecoins em alta"""
        trending = []
        
        for symbol in self.popular_memecoins:
            data = self.get_memecoin_data(symbol)
            if data:
                trending.append(data)
        
        # Ordenar por mudança de preço
        trending.sort(key=lambda x: x['change_24h'], reverse=True)
        
        return trending

# Instanciar classes
config_manager = AgentConfigManager()
sentiment_analyzer = SocialSentimentAnalyzer()
memecoin_tracker = MemecoinTracker()

@api_ext.route('/api/agent/config', methods=['GET'])
def get_agent_config():
    """Obtém configuração atual do agente"""
    config = config_manager.load_config()
    return jsonify(config)

@api_ext.route('/api/agent/config', methods=['POST'])
def update_agent_config():
    """Atualiza configuração do agente"""
    try:
        new_config = request.get_json()
        
        # Validar dados
        if not isinstance(new_config, dict):
            return jsonify({'error': 'Dados inválidos'}), 400
        
        # Carregar config atual e atualizar
        current_config = config_manager.load_config()
        current_config.update(new_config)
        
        # Salvar
        if config_manager.save_config(current_config):
            return jsonify({'message': 'Configuração atualizada com sucesso'})
        else:
            return jsonify({'error': 'Erro ao salvar configuração'}), 500
            
    except Exception as e:
        logger.error(f"Erro ao atualizar config: {e}")
        return jsonify({'error': str(e)}), 500

@api_ext.route('/api/agent/status', methods=['GET'])
def get_agent_status():
    """Obtém status do agente"""
    # Verificar se o agente está rodando (verificar arquivo de log ou processo)
    log_file = "ai_trading_agent.log"
    agent_running = False
    last_activity = None
    
    if os.path.exists(log_file):
        try:
            stat = os.stat(log_file)
            last_activity = datetime.fromtimestamp(stat.st_mtime)
            # Considerar ativo se log foi modificado nos últimos 5 minutos
            agent_running = (datetime.now() - last_activity).total_seconds() < 300
        except:
            pass
    
    return jsonify({
        'running': agent_running,
        'last_activity': last_activity.isoformat() if last_activity else None,
        'config': config_manager.load_config()
    })

@api_ext.route('/api/agent/start', methods=['POST'])
def start_agent():
    """Inicia o agente (simulado)"""
    # Em produção, iniciar processo do agente
    return jsonify({'message': 'Agente iniciado', 'status': 'starting'})

@api_ext.route('/api/agent/stop', methods=['POST'])
def stop_agent():
    """Para o agente (simulado)"""
    # Em produção, parar processo do agente
    return jsonify({'message': 'Agente parado', 'status': 'stopped'})

@api_ext.route('/api/sentiment', methods=['GET'])
def get_social_sentiment():
    """Obtém análise de sentimento das redes sociais"""
    symbol = request.args.get('symbol', 'DOGE')
    sentiment = sentiment_analyzer.get_overall_sentiment(symbol)
    return jsonify(sentiment)

@api_ext.route('/api/memecoins', methods=['GET'])
def get_memecoins():
    """Obtém dados das memecoins em alta"""
    trending = memecoin_tracker.get_trending_memecoins()
    return jsonify(trending)

@api_ext.route('/api/memecoins/<symbol>', methods=['GET'])
def get_memecoin_details(symbol):
    """Obtém detalhes de uma memecoin específica"""
    data = memecoin_tracker.get_memecoin_data(symbol.upper())
    if data:
        return jsonify(data)
    else:
        return jsonify({'error': 'Memecoin não encontrada'}), 404

@api_ext.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """Obtém lista de moedas monitoradas"""
    config = config_manager.load_config()
    watchlist = config.get('watchlist', ['DOGEUSDT'])
    
    # Obter dados de cada moeda na watchlist
    watchlist_data = []
    for symbol in watchlist:
        data = memecoin_tracker.get_memecoin_data(symbol)
        if data:
            watchlist_data.append(data)
    
    return jsonify(watchlist_data)

@api_ext.route('/api/watchlist', methods=['POST'])
def update_watchlist():
    """Atualiza lista de moedas monitoradas"""
    try:
        data = request.get_json()
        new_watchlist = data.get('watchlist', [])
        
        if not isinstance(new_watchlist, list):
            return jsonify({'error': 'Watchlist deve ser uma lista'}), 400
        
        # Atualizar configuração
        config = config_manager.load_config()
        config['watchlist'] = new_watchlist
        
        if config_manager.save_config(config):
            return jsonify({'message': 'Watchlist atualizada com sucesso'})
        else:
            return jsonify({'error': 'Erro ao salvar watchlist'}), 500
            
    except Exception as e:
        logger.error(f"Erro ao atualizar watchlist: {e}")
        return jsonify({'error': str(e)}), 500

@api_ext.route('/api/trades/stats', methods=['GET'])
def get_trade_stats():
    """Obtém estatísticas detalhadas dos trades"""
    try:
        conn = sqlite3.connect('memecoin.db')
        cursor = conn.cursor()
        
        # Trades de hoje
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT type, COUNT(*), AVG(price), SUM(amount), MIN(timestamp), MAX(timestamp)
            FROM trades 
            WHERE DATE(timestamp) = ?
            GROUP BY type
        ''', (today,))
        
        today_stats = {}
        for row in cursor.fetchall():
            today_stats[row[0]] = {
                'count': row[1],
                'avg_price': row[2],
                'total_amount': row[3],
                'first_trade': row[4],
                'last_trade': row[5]
            }
        
        # Estatísticas gerais (últimos 30 dias)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
        cursor.execute('''
            SELECT COUNT(*), AVG(price), SUM(amount)
            FROM trades 
            WHERE DATE(timestamp) >= ?
        ''', (thirty_days_ago,))
        
        general_stats = cursor.fetchone()
        
        # Trades por dia (últimos 7 dias)
        cursor.execute('''
            SELECT DATE(timestamp), COUNT(*), SUM(amount)
            FROM trades 
            WHERE DATE(timestamp) >= DATE('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp)
        ''', )
        
        daily_stats = [
            {
                'date': row[0],
                'count': row[1],
                'total_amount': row[2]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return jsonify({
            'today': today_stats,
            'last_30_days': {
                'total_trades': general_stats[0] or 0,
                'avg_price': general_stats[1] or 0,
                'total_amount': general_stats[2] or 0
            },
            'daily_breakdown': daily_stats
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({'error': str(e)}), 500

@api_ext.route('/api/signals/history', methods=['GET'])
def get_signals_history():
    """Obtém histórico de sinais do agente"""
    # Em produção, ler de arquivo de log ou banco de dados
    # Por enquanto, retornar dados simulados
    signals = []
    
    for i in range(10):
        signals.append({
            'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
            'symbol': 'DOGEUSDT',
            'action': ['buy', 'sell', 'hold'][i % 3],
            'confidence': round(0.5 + (i % 5) * 0.1, 2),
            'price': 0.224 + (i % 3 - 1) * 0.001,
            'reason': f'Sinal #{i+1} - Análise técnica',
            'executed': i % 2 == 0
        })
    
    return jsonify(signals)

@api_ext.route('/api/performance', methods=['GET'])
def get_performance_metrics():
    """Obtém métricas de performance do agente"""
    # Em produção, calcular métricas reais
    return jsonify({
        'total_trades': 45,
        'profitable_trades': 32,
        'win_rate': 71.1,
        'total_profit': 247.83,
        'best_trade': 45.20,
        'worst_trade': -12.50,
        'avg_trade_duration': 2.4,  # horas
        'sharpe_ratio': 1.34,
        'max_drawdown': 8.2,
        'current_streak': 5,  # trades consecutivos lucrativos
        'daily_pnl': [
            {'date': '2025-08-01', 'pnl': 23.45},
            {'date': '2025-08-02', 'pnl': -5.20},
            {'date': '2025-08-03', 'pnl': 31.80},
            {'date': '2025-08-04', 'pnl': 15.60},
            {'date': '2025-08-05', 'pnl': 8.90},
            {'date': '2025-08-06', 'pnl': -2.10},
            {'date': '2025-08-07', 'pnl': 19.30},
            {'date': '2025-08-08', 'pnl': 12.75}
        ]
    })

# Função para registrar as rotas no app principal
def register_extensions(app):
    """Registra as extensões da API no app Flask"""
    app.register_blueprint(api_ext)
    logger.info("Extensões da API registradas com sucesso")

if __name__ == "__main__":
    # Teste das funcionalidades
    print("Testando extensões da API...")
    
    # Testar configuração
    config_mgr = AgentConfigManager()
    config = config_mgr.load_config()
    print(f"Config carregada: {config['symbol']}")
    
    # Testar sentimento
    sentiment = sentiment_analyzer.get_overall_sentiment()
    print(f"Sentimento geral: {sentiment['overall']}")
    
    # Testar memecoins
    memecoins = memecoin_tracker.get_trending_memecoins()
    print(f"Memecoins encontradas: {len(memecoins)}")
    
    print("✅ Todas as extensões funcionando!")
