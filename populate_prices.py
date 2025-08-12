#!/usr/bin/env python3
"""
Populate Prices - MoCoVe
Script para popular dados históricos de preços no database
"""

import sqlite3
import requests
import json
import time
from datetime import datetime, timedelta
import os

# Configuração
DATABASE_FILE = "memecoin.db"
WATCHLIST_FILE = "coin_watchlist_expanded.json"

def print_status(message, status="INFO"):
    """Imprimir status com formatação"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    emoji = {"INFO": "[INFO]", "SUCCESS": "[OK]", "ERROR": "[ERR]", "WARNING": "[WARN]"}
    print(f"{emoji.get(status, '[INFO]')} [{timestamp}] {message}")

def load_watchlist():
    """Carregar lista de moedas do arquivo de configuração"""
    try:
        if not os.path.exists(WATCHLIST_FILE):
            print_status(f"Arquivo {WATCHLIST_FILE} não encontrado!", "ERROR")
            return []
        
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extrair todos os símbolos de todas as categorias
        symbols = []
        
        for category, coins in data.items():
            if isinstance(coins, dict):
                for coin_data in coins.values():
                    if isinstance(coin_data, dict) and 'symbol' in coin_data:
                        symbols.append(coin_data['symbol'])
                    elif isinstance(coin_data, str):
                        symbols.append(coin_data)
            elif isinstance(coins, list):
                symbols.extend(coins)
        
        # Remover duplicatas e converter para maiúsculo
        symbols = list(set([s.upper() for s in symbols if s]))
        
        print_status(f"Carregadas {len(symbols)} moedas da watchlist", "SUCCESS")
        return symbols
        
    except Exception as e:
        print_status(f"Erro ao carregar watchlist: {e}", "ERROR")
        return []

def setup_database():
    """Configurar database e criar tabelas necessárias"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Criar tabela de preços se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                volume REAL,
                market_cap REAL,
                change_24h REAL,
                timestamp TEXT NOT NULL,
                source TEXT DEFAULT 'populate_script'
            )
        ''')
        
        # Criar índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prices_symbol ON prices(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prices_timestamp ON prices(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prices_symbol_timestamp ON prices(symbol, timestamp)')
        
        conn.commit()
        conn.close()
        
        print_status("Database configurado com sucesso", "SUCCESS")
        return True
        
    except Exception as e:
        print_status(f"Erro ao configurar database: {e}", "ERROR")
        return False

def get_binance_price(symbol):
    """Obter preço atual da Binance"""
    try:
        # Tentar diferentes formatos de símbolo
        pairs_to_try = [
            f"{symbol}USDT",
            f"{symbol}BUSD", 
            f"{symbol}BTC",
            f"{symbol}ETH"
        ]
        
        for pair in pairs_to_try:
            try:
                url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'symbol': symbol,
                        'price': float(data['lastPrice']),
                        'volume': float(data['volume']),
                        'change_24h': float(data['priceChangePercent']) / 100,
                        'pair': pair,
                        'source': 'binance'
                    }
            except:
                continue
        
        return None
        
    except Exception as e:
        print_status(f"Erro ao obter preço Binance para {symbol}: {e}", "WARNING")
        return None

def get_coingecko_price(symbol):
    """Obter preço do CoinGecko (backup)"""
    try:
        # Mapeamento de símbolos para IDs do CoinGecko
        symbol_mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'DOGE': 'dogecoin',
            'SHIB': 'shiba-inu',
            'PEPE': 'pepe',
            'WIF': 'dogwifcoin',
            'FLOKI': 'floki',
            'BONK': 'bonk',
            'SOL': 'solana',
            'ADA': 'cardano',
            'AVAX': 'avalanche-2',
            'DOT': 'polkadot',
            'UNI': 'uniswap',
            'AAVE': 'aave',
            'COMP': 'compound-governance-token',
            'FET': 'fetch-ai',
            'AGIX': 'singularitynet',
            'OCEAN': 'ocean-protocol',
            'AXS': 'axie-infinity',
            'SAND': 'the-sandbox',
            'MANA': 'decentraland',
            'ENJ': 'enjincoin'
        }
        
        coin_id = symbol_mapping.get(symbol, symbol.lower())
        
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if coin_id in data:
                coin_data = data[coin_id]
                return {
                    'symbol': symbol,
                    'price': coin_data.get('usd', 0),
                    'volume': coin_data.get('usd_24h_vol', 0),
                    'market_cap': coin_data.get('usd_market_cap', 0),
                    'change_24h': coin_data.get('usd_24h_change', 0) / 100 if coin_data.get('usd_24h_change') else 0,
                    'source': 'coingecko'
                }
        
        return None
        
    except Exception as e:
        print_status(f"Erro ao obter preço CoinGecko para {symbol}: {e}", "WARNING")
        return None

def insert_price_data(price_data):
    """Inserir dados de preço no database"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO prices (symbol, price, volume, market_cap, change_24h, timestamp, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            price_data['symbol'],
            price_data['price'],
            price_data.get('volume', 0),
            price_data.get('market_cap', 0),
            price_data.get('change_24h', 0),
            datetime.now().isoformat(),
            price_data.get('source', 'unknown')
        ))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print_status(f"Erro ao inserir dados de {price_data['symbol']}: {e}", "ERROR")
        return False

def generate_sample_data(symbols):
    """Gerar dados de exemplo quando APIs não estão disponíveis"""
    import random
    
    sample_data = []
    base_prices = {
        'BTC': 45000, 'ETH': 2800, 'BNB': 350, 'SOL': 110, 'ADA': 0.45,
        'DOGE': 0.08, 'SHIB': 0.000009, 'PEPE': 0.0000012, 'WIF': 2.5,
        'FLOKI': 0.00018, 'BONK': 0.000025, 'UNI': 8.5, 'AAVE': 95,
        'COMP': 55, 'FET': 1.35, 'AGIX': 0.42, 'OCEAN': 0.65,
        'AXS': 6.8, 'SAND': 0.48, 'MANA': 0.52, 'ENJ': 0.28
    }
    
    print_status("Gerando dados de exemplo...", "WARNING")
    
    for symbol in symbols[:20]:  # Limitar a 20 moedas para o exemplo
        base_price = base_prices.get(symbol, random.uniform(0.01, 100))
        
        # Gerar variação realista
        change = random.uniform(-0.15, 0.15)  # -15% a +15%
        current_price = base_price * (1 + change)
        
        sample_data.append({
            'symbol': symbol,
            'price': round(current_price, 8),
            'volume': random.uniform(100000, 10000000),
            'market_cap': random.uniform(1000000, 1000000000),
            'change_24h': change,
            'source': 'sample_data'
        })
    
    return sample_data

def populate_prices():
    """Função principal para popular preços"""
    print_status("Iniciando população de dados de preços", "INFO")
    
    # Configurar database
    if not setup_database():
        return False
    
    # Carregar watchlist
    symbols = load_watchlist()
    if not symbols:
        print_status("Nenhuma moeda encontrada na watchlist", "ERROR")
        return False
    
    print_status(f"Processando {len(symbols)} moedas: {', '.join(symbols[:10])}{'...' if len(symbols) > 10 else ''}", "INFO")
    
    successful_inserts = 0
    api_failures = 0
    
    for i, symbol in enumerate(symbols, 1):
        print_status(f"[{i}/{len(symbols)}] Processando {symbol}...", "INFO")
        
        # Tentar obter dados da Binance primeiro
        price_data = get_binance_price(symbol)
        
        # Se falhar, tentar CoinGecko
        if not price_data:
            time.sleep(1)  # Rate limiting
            price_data = get_coingecko_price(symbol)
        
        if price_data:
            if insert_price_data(price_data):
                successful_inserts += 1
                print_status(f"{symbol}: ${price_data['price']:.8f} ({price_data['change_24h']:+.2%})", "SUCCESS")
            else:
                print_status(f"Falha ao inserir dados de {symbol}", "ERROR")
        else:
            api_failures += 1
            print_status(f"Não foi possível obter dados para {symbol}", "WARNING")
        
        # Rate limiting
        time.sleep(0.5)
        
        # Parar se muitas falhas consecutivas
        if api_failures >= 5 and successful_inserts == 0:
            print_status("Muitas falhas de API - gerando dados de exemplo", "WARNING")
            sample_data = generate_sample_data(symbols)
            
            for data in sample_data:
                if insert_price_data(data):
                    successful_inserts += 1
            break
    
    # Relatório final
    print_status("="*50, "INFO")
    print_status(f"População concluída!", "SUCCESS")
    print_status(f"Inserções bem-sucedidas: {successful_inserts}", "SUCCESS")
    print_status(f"Falhas de API: {api_failures}", "WARNING")
    print_status(f"Taxa de sucesso: {successful_inserts/len(symbols)*100:.1f}%", "INFO")
    
    return successful_inserts > 0

def main():
    """Função principal"""
    try:
        success = populate_prices()
        if success:
            print_status("✅ Script executado com sucesso!", "SUCCESS")
            return True
        else:
            print_status("❌ Script falhou!", "ERROR")
            return False
            
    except KeyboardInterrupt:
        print_status("Script interrompido pelo usuário", "WARNING")
        return False
    except Exception as e:
        print_status(f"Erro inesperado: {e}", "ERROR")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
