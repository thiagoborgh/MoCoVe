#!/usr/bin/env python3
"""
Watchlist Manager - MoCoVe AI Trading System
Gerenciamento robusto de lista de moedas para monitoramento
"""

import json
import sqlite3
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from dataclasses import dataclass

@dataclass
class CoinData:
    symbol: str
    name: str
    category: str
    market_cap_rank: int
    volume_threshold: float
    volatility_target: float
    social_weight: float
    trading_enabled: bool
    tier: Optional[str] = None
    current_price: Optional[float] = None
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    sentiment_score: Optional[float] = None
    last_updated: Optional[datetime] = None

class WatchlistManager:
    def __init__(self, config_file: str = "coin_watchlist_expanded.json", db_path: str = "memecoin.db"):
        self.config_file = config_file
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.coins_data: Dict[str, CoinData] = {}
        self.load_config()
        self.init_database()
    
    def load_config(self):
        """Carregar configuração da watchlist"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Processar todas as moedas em uma estrutura unificada
            all_coins = {}
            
            # Memecoins
            for tier, coins in self.config['memecoins'].items():
                if isinstance(coins, list):
                    for coin in coins:
                        coin['tier'] = tier
                        all_coins[coin['symbol']] = CoinData(**coin)
            
            # Altcoins
            for category, coins in self.config['altcoins'].items():
                for coin in coins:
                    coin['tier'] = f'alt_{category}'
                    all_coins[coin['symbol']] = CoinData(**coin)
            
            self.coins_data = all_coins
            self.logger.info(f"Carregadas {len(self.coins_data)} moedas para monitoramento")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {e}")
            self.coins_data = {}
    
    def init_database(self):
        """Inicializar tabelas do banco de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabela de watchlist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS watchlist_coins (
                    symbol TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT,
                    tier TEXT,
                    market_cap_rank INTEGER,
                    trading_enabled BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de dados de mercado
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL,
                    volume_24h REAL,
                    price_change_24h REAL,
                    market_cap REAL,
                    sentiment_score REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (symbol) REFERENCES watchlist_coins (symbol)
                )
            ''')
            
            # Tabela de alertas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    threshold_value REAL,
                    current_value REAL,
                    message TEXT,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("Database inicializado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar database: {e}")
    
    def sync_watchlist_to_db(self):
        """Sincronizar watchlist com banco de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for symbol, coin_data in self.coins_data.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO watchlist_coins 
                    (symbol, name, category, tier, market_cap_rank, trading_enabled, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    coin_data.name,
                    coin_data.category,
                    getattr(coin_data, 'tier', 'unknown'),
                    coin_data.market_cap_rank,
                    coin_data.trading_enabled,
                    datetime.now()
                ))
            
            conn.commit()
            conn.close()
            self.logger.info(f"Sincronizadas {len(self.coins_data)} moedas com o banco")
            
        except Exception as e:
            self.logger.error(f"Erro ao sincronizar watchlist: {e}")
    
    def get_coins_by_tier(self, tier: str) -> List[CoinData]:
        """Obter moedas por tier"""
        return [coin for coin in self.coins_data.values() 
                if hasattr(coin, 'tier') and getattr(coin, 'tier') == tier]
    
    def get_trading_enabled_coins(self) -> List[CoinData]:
        """Obter moedas habilitadas para trading"""
        return [coin for coin in self.coins_data.values() if coin.trading_enabled]
    
    def get_coins_by_category(self, category: str) -> List[CoinData]:
        """Obter moedas por categoria"""
        return [coin for coin in self.coins_data.values() if coin.category == category]
    
    def update_coin_price(self, symbol: str, price: float, volume_24h: float, 
                         price_change_24h: float, market_cap: Optional[float] = None):
        """Atualizar dados de preço de uma moeda"""
        if symbol in self.coins_data:
            coin = self.coins_data[symbol]
            coin.current_price = price
            coin.volume_24h = volume_24h
            coin.price_change_24h = price_change_24h
            coin.last_updated = datetime.now()
            
            # Salvar no banco
            self.save_market_data(symbol, price, volume_24h, price_change_24h, market_cap)
            
            # Verificar alertas
            self.check_price_alerts(symbol, price, price_change_24h, volume_24h)
    
    def save_market_data(self, symbol: str, price: float, volume_24h: float, 
                        price_change_24h: float, market_cap: Optional[float] = None):
        """Salvar dados de mercado no banco"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO market_data 
                (symbol, price, volume_24h, price_change_24h, market_cap)
                VALUES (?, ?, ?, ?, ?)
            ''', (symbol, price, volume_24h, price_change_24h, market_cap))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados de mercado para {symbol}: {e}")
    
    def check_price_alerts(self, symbol: str, price: float, price_change_24h: float, volume_24h: float):
        """Verificar e gerar alertas de preço"""
        try:
            alerts_config = self.config['watchlist_config']['price_alerts']
            if not alerts_config['enabled']:
                return
            
            thresholds = alerts_config['thresholds']
            alerts = []
            
            # Alerta de pump
            if price_change_24h >= thresholds['pump']:
                alerts.append({
                    'type': 'PUMP',
                    'threshold': thresholds['pump'],
                    'value': price_change_24h,
                    'message': f"{symbol} pumping +{price_change_24h:.2%}!"
                })
            
            # Alerta de dump
            if price_change_24h <= thresholds['dump']:
                alerts.append({
                    'type': 'DUMP',
                    'threshold': thresholds['dump'],
                    'value': price_change_24h,
                    'message': f"{symbol} dumping {price_change_24h:.2%}!"
                })
            
            # Alerta de volume
            coin = self.coins_data.get(symbol)
            if coin and volume_24h >= coin.volume_threshold * thresholds['volume_spike']:
                alerts.append({
                    'type': 'VOLUME_SPIKE',
                    'threshold': coin.volume_threshold * thresholds['volume_spike'],
                    'value': volume_24h,
                    'message': f"{symbol} volume spike: ${volume_24h:,.0f}!"
                })
            
            # Salvar alertas no banco
            for alert in alerts:
                self.save_alert(symbol, alert['type'], alert['threshold'], alert['value'], alert['message'])
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar alertas para {symbol}: {e}")
    
    def save_alert(self, symbol: str, alert_type: str, threshold: float, current_value: float, message: str):
        """Salvar alerta no banco de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO price_alerts 
                (symbol, alert_type, threshold_value, current_value, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (symbol, alert_type, threshold, current_value, message))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Alerta salvo: {message}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar alerta: {e}")
    
    def get_recent_alerts(self, limit: int = 20) -> List[Dict]:
        """Obter alertas recentes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT symbol, alert_type, threshold_value, current_value, message, triggered_at
                FROM price_alerts 
                ORDER BY triggered_at DESC 
                LIMIT ?
            ''', (limit,))
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    'symbol': row[0],
                    'type': row[1],
                    'threshold': row[2],
                    'current_value': row[3],
                    'message': row[4],
                    'timestamp': row[5]
                })
            
            conn.close()
            return alerts
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar alertas: {e}")
            return []
    
    def get_top_performers(self, timeframe: str = '24h', limit: int = 10) -> List[Dict]:
        """Obter top performers por timeframe"""
        performers = []
        
        for symbol, coin in self.coins_data.items():
            if coin.current_price and coin.price_change_24h is not None:
                performers.append({
                    'symbol': symbol,
                    'name': coin.name,
                    'category': coin.category,
                    'price': coin.current_price,
                    'change_24h': coin.price_change_24h,
                    'volume_24h': coin.volume_24h or 0,
                    'trading_enabled': coin.trading_enabled
                })
        
        # Ordenar por variação de preço
        performers.sort(key=lambda x: x['change_24h'], reverse=True)
        return performers[:limit]
    
    def get_watchlist_summary(self) -> Dict:
        """Obter resumo da watchlist"""
        total_coins = len(self.coins_data)
        trading_enabled = len(self.get_trading_enabled_coins())
        
        # Contar por tier
        tier_counts = {}
        for coin in self.coins_data.values():
            tier = getattr(coin, 'tier', 'unknown')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        # Calcular estatísticas
        prices = [coin.current_price for coin in self.coins_data.values() if coin.current_price]
        changes = [coin.price_change_24h for coin in self.coins_data.values() if coin.price_change_24h is not None]
        
        return {
            'total_coins': total_coins,
            'trading_enabled': trading_enabled,
            'tier_distribution': tier_counts,
            'price_stats': {
                'avg_change_24h': sum(changes) / len(changes) if changes else 0,
                'positive_performers': len([c for c in changes if c > 0]),
                'negative_performers': len([c for c in changes if c < 0])
            },
            'last_updated': datetime.now().isoformat()
        }
    
    def export_watchlist(self, format: str = 'json') -> str:
        """Exportar watchlist em diferentes formatos"""
        if format == 'json':
            export_data = {}
            for symbol, coin in self.coins_data.items():
                export_data[symbol] = {
                    'name': coin.name,
                    'category': coin.category,
                    'tier': getattr(coin, 'tier', 'unknown'),
                    'trading_enabled': coin.trading_enabled,
                    'current_price': coin.current_price,
                    'price_change_24h': coin.price_change_24h,
                    'volume_24h': coin.volume_24h,
                    'last_updated': coin.last_updated.isoformat() if coin.last_updated else None
                }
            return json.dumps(export_data, indent=2)
        
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(['Symbol', 'Name', 'Category', 'Tier', 'Price', 'Change24h', 'Volume24h', 'Trading'])
            
            # Data
            for symbol, coin in self.coins_data.items():
                writer.writerow([
                    symbol,
                    coin.name,
                    coin.category,
                    getattr(coin, 'tier', 'unknown'),
                    coin.current_price or '',
                    coin.price_change_24h or '',
                    coin.volume_24h or '',
                    coin.trading_enabled
                ])
            
            return output.getvalue()
    
    def add_custom_coin(self, symbol: str, name: str, category: str = "Custom", 
                       trading_enabled: bool = False) -> bool:
        """Adicionar moeda customizada à watchlist"""
        try:
            new_coin = CoinData(
                symbol=symbol,
                name=name,
                category=category,
                market_cap_rank=999,
                volume_threshold=1000000,
                volatility_target=0.20,
                social_weight=0.3,
                trading_enabled=trading_enabled
            )
            
            self.coins_data[symbol] = new_coin
            
            # Salvar no banco
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO watchlist_coins 
                (symbol, name, category, tier, market_cap_rank, trading_enabled, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, name, category, 'custom', 999, trading_enabled, datetime.now()))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Moeda customizada adicionada: {symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar moeda customizada {symbol}: {e}")
            return False
    
    def remove_coin(self, symbol: str) -> bool:
        """Remover moeda da watchlist"""
        try:
            if symbol in self.coins_data:
                del self.coins_data[symbol]
                
                # Remover do banco
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM watchlist_coins WHERE symbol = ?', (symbol,))
                conn.commit()
                conn.close()
                
                self.logger.info(f"Moeda removida: {symbol}")
                return True
            else:
                self.logger.warning(f"Moeda não encontrada: {symbol}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao remover moeda {symbol}: {e}")
            return False

# Classe para API endpoints
class WatchlistAPI:
    def __init__(self, watchlist_manager: WatchlistManager):
        self.wm = watchlist_manager
    
    def get_all_coins(self):
        """API: Obter todas as moedas"""
        return {symbol: {
            'name': coin.name,
            'category': coin.category,
            'tier': getattr(coin, 'tier', 'unknown'),
            'current_price': coin.current_price,
            'price_change_24h': coin.price_change_24h,
            'volume_24h': coin.volume_24h,
            'trading_enabled': coin.trading_enabled,
            'last_updated': coin.last_updated.isoformat() if coin.last_updated else None
        } for symbol, coin in self.wm.coins_data.items()}
    
    def get_coins_by_tier(self, tier: str):
        """API: Obter moedas por tier"""
        coins = self.wm.get_coins_by_tier(tier)
        return [{'symbol': coin.symbol, 'name': coin.name, 'category': coin.category,
                'price': coin.current_price, 'change_24h': coin.price_change_24h} 
                for coin in coins]
    
    def get_trading_coins(self):
        """API: Obter moedas habilitadas para trading"""
        coins = self.wm.get_trading_enabled_coins()
        return [{'symbol': coin.symbol, 'name': coin.name, 'category': coin.category,
                'price': coin.current_price, 'change_24h': coin.price_change_24h} 
                for coin in coins]
    
    def get_alerts(self, limit: int = 20):
        """API: Obter alertas recentes"""
        return self.wm.get_recent_alerts(limit)
    
    def get_top_performers(self, limit: int = 10):
        """API: Obter top performers"""
        return self.wm.get_top_performers(limit=limit)
    
    def get_summary(self):
        """API: Obter resumo da watchlist"""
        return self.wm.get_watchlist_summary()

if __name__ == "__main__":
    # Teste do sistema
    logging.basicConfig(level=logging.INFO)
    
    wm = WatchlistManager()
    wm.sync_watchlist_to_db()
    
    # Simular alguns dados de preço
    wm.update_coin_price("DOGEUSDT", 0.08, 1500000000, 0.12, 11000000000)
    wm.update_coin_price("SHIBUSDT", 0.000009, 800000000, 0.08, 5000000000)
    wm.update_coin_price("PEPEUSDT", 0.000001, 300000000, 0.25, 400000000)
    
    # Obter resumo
    summary = wm.get_watchlist_summary()
    print(f"Watchlist Summary: {json.dumps(summary, indent=2)}")
    
    # Obter top performers
    top = wm.get_top_performers()
    print(f"Top Performers: {json.dumps(top, indent=2)}")
