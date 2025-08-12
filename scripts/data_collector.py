"""
MoCoVe Data Collection - Coleta de Dados de Memecoins
Script para coletar preços e dados de mercado de memecoins
"""

import sqlite3
import requests
import time
import ccxt
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações
DB_PATH = os.getenv('DB_PATH', '../memecoin.db')
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')
USE_TESTNET = os.getenv('USE_TESTNET', 'true').lower() == 'true'

# Lista de memecoins suportadas
SUPPORTED_MEMECOINS = [
    'DOGE/BUSD', 'SHIB/BUSD', 'PEPE/BUSD', 'FLOKI/BUSD',
    'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'FLOKI/USDT'
]

COINGECKO_MEMECOINS = [
    'dogecoin', 'shiba-inu', 'pepe', 'dogwifhat', 'bonk',
    'floki', 'milady', 'mog-coin', 'brett'
]

class DataCollector:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_database()
        
        # Configurar Binance exchange
        if BINANCE_API_KEY and BINANCE_API_SECRET:
            self.exchange = ccxt.binance({
                'apiKey': BINANCE_API_KEY,
                'secret': BINANCE_API_SECRET,
                'sandbox': USE_TESTNET,
                'enableRateLimit': True,
            })
        else:
            self.exchange = None
            logger.warning("Chaves da API Binance não configuradas")
    
    def init_database(self):
        """Inicializa o banco de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabela de preços
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    price REAL NOT NULL,
                    volume REAL DEFAULT 0,
                    market_cap REAL DEFAULT 0,
                    source TEXT DEFAULT 'unknown',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, timestamp, source)
                )
            ''')
            
            # Índices para performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_prices_symbol_timestamp ON prices(symbol, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_prices_timestamp ON prices(timestamp)')
            
            conn.commit()
            conn.close()
            logger.info("Banco de dados inicializado")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar banco: {e}")
            raise
    
    def collect_binance_data(self) -> List[Dict]:
        """Coleta dados da Binance"""
        if not self.exchange:
            return []
        
        collected_data = []
        
        try:
            for symbol in SUPPORTED_MEMECOINS:
                try:
                    # Obter ticker
                    ticker = self.exchange.fetch_ticker(symbol)
                    
                    if ticker and ticker.get('last'):
                        data = {
                            'symbol': symbol,
                            'timestamp': datetime.now(),
                            'price': float(ticker['last']),
                            'volume': float(ticker.get('baseVolume', 0)),
                            'source': 'binance'
                        }
                        collected_data.append(data)
                        logger.info(f"Coletado {symbol}: ${data['price']:.6f}")
                    
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Erro ao coletar {symbol} da Binance: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Erro geral na coleta Binance: {e}")
        
        return collected_data
    
    def collect_coingecko_data(self) -> List[Dict]:
        """Coleta dados do CoinGecko"""
        collected_data = []
        
        try:
            # API CoinGecko para múltiplas moedas
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': ','.join(COINGECKO_MEMECOINS),
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            current_time = datetime.now()
            
            for coin_id, coin_data in data.items():
                if 'usd' in coin_data:
                    symbol_map = {
                        'dogecoin': 'DOGE/USD',
                        'shiba-inu': 'SHIB/USD',
                        'pepe': 'PEPE/USD',
                        'floki': 'FLOKI/USD',
                        'dogwifhat': 'WIF/USD',
                        'bonk': 'BONK/USD'
                    }
                    
                    symbol = symbol_map.get(coin_id, f"{coin_id.upper()}/USD")
                    
                    record = {
                        'symbol': symbol,
                        'timestamp': current_time,
                        'price': float(coin_data['usd']),
                        'volume': float(coin_data.get('usd_24h_vol', 0)),
                        'market_cap': float(coin_data.get('usd_market_cap', 0)),
                        'source': 'coingecko'
                    }
                    
                    collected_data.append(record)
                    logger.info(f"Coletado {symbol}: ${record['price']:.6f}")
            
        except Exception as e:
            logger.error(f"Erro ao coletar dados do CoinGecko: {e}")
        
        return collected_data
    
    def save_to_database(self, data_list: List[Dict]):
        """Salva dados no banco de dados"""
        if not data_list:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for data in data_list:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO prices 
                        (symbol, timestamp, price, volume, market_cap, source)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        data['symbol'],
                        data['timestamp'],
                        data['price'],
                        data.get('volume', 0),
                        data.get('market_cap', 0),
                        data['source']
                    ))
                    
                except Exception as e:
                    logger.error(f"Erro ao inserir registro {data['symbol']}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            logger.info(f"Salvos {len(data_list)} registros no banco de dados")
            
        except Exception as e:
            logger.error(f"Erro ao salvar no banco: {e}")
    
    def collect_historical_data(self, days: int = 7):
        """Coleta dados históricos do CoinGecko"""
        logger.info(f"Coletando dados históricos dos últimos {days} dias...")
        
        for coin_id in COINGECKO_MEMECOINS:
            try:
                url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart'
                params = {
                    'vs_currency': 'usd',
                    'days': days,
                    'interval': 'hourly' if days <= 7 else 'daily'
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                prices = data.get('prices', [])
                volumes = data.get('total_volumes', [])
                market_caps = data.get('market_caps', [])
                
                # Mapear símbolo
                symbol_map = {
                    'dogecoin': 'DOGE/USD',
                    'shiba-inu': 'SHIB/USD',
                    'pepe': 'PEPE/USD',
                    'floki': 'FLOKI/USD',
                    'dogwifhat': 'WIF/USD',
                    'bonk': 'BONK/USD'
                }
                symbol = symbol_map.get(coin_id, f"{coin_id.upper()}/USD")
                
                historical_data = []
                for i, (timestamp, price) in enumerate(prices):
                    volume = volumes[i][1] if i < len(volumes) else 0
                    market_cap = market_caps[i][1] if i < len(market_caps) else 0
                    
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    
                    historical_data.append({
                        'symbol': symbol,
                        'timestamp': dt,
                        'price': float(price),
                        'volume': float(volume),
                        'market_cap': float(market_cap),
                        'source': 'coingecko_historical'
                    })
                
                self.save_to_database(historical_data)
                logger.info(f"Salvos {len(historical_data)} registros históricos para {coin_id}")
                
                time.sleep(2)  # Rate limiting CoinGecko
                
            except Exception as e:
                logger.error(f"Erro ao coletar histórico de {coin_id}: {e}")
                continue
    
    def get_database_stats(self) -> Dict:
        """Retorna estatísticas do banco de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total de registros
            cursor.execute('SELECT COUNT(*) FROM prices')
            total_records = cursor.fetchone()[0]
            
            # Contagem por símbolo
            cursor.execute('''
                SELECT symbol, COUNT(*) as count
                FROM prices
                GROUP BY symbol
                ORDER BY count DESC
            ''')
            symbol_counts = cursor.fetchall()
            
            # Período de dados
            cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM prices')
            min_date, max_date = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_records': total_records,
                'symbol_counts': dict(symbol_counts),
                'date_range': {
                    'start': min_date,
                    'end': max_date
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def run_collection_cycle(self):
        """Executa um ciclo completo de coleta"""
        logger.info("=== Iniciando ciclo de coleta de dados ===")
        
        # Coletar dados atuais
        binance_data = self.collect_binance_data()
        coingecko_data = self.collect_coingecko_data()
        
        # Salvar todos os dados
        all_data = binance_data + coingecko_data
        self.save_to_database(all_data)
        
        # Estatísticas
        stats = self.get_database_stats()
        logger.info(f"Estatísticas do banco: {stats.get('total_records', 0)} registros totais")
        
        logger.info("=== Ciclo de coleta concluído ===")
        return len(all_data)

def main():
    """Função principal"""
    collector = DataCollector()
    
    # Verificar se precisa de dados históricos
    stats = collector.get_database_stats()
    if stats.get('total_records', 0) < 100:
        logger.info("Poucos dados no banco, coletando histórico...")
        collector.collect_historical_data(days=30)
    
    # Executar coleta atual
    collector.run_collection_cycle()

if __name__ == "__main__":
    main()
