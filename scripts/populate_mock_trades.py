import sqlite3
from datetime import datetime, timedelta
import random

import pathlib
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
DB_PATH = str(PROJECT_ROOT / 'memecoin.db')

SYMBOLS = ['DOGE/BUSD', 'PEPE/BUSD', 'SHIB/BUSD', 'FLOKI/BUSD', 'BONK/BUSD']

# Gera trades mock

def generate_trades(n=100):
    trades = []
    now = datetime.now()
    for i in range(n):
        symbol = random.choice(SYMBOLS)
        trade_type = random.choice(['buy', 'sell'])
        amount = round(random.uniform(10, 100), 2)
        price = round(random.uniform(0.00001, 0.5), 6)
        total = round(amount * price, 4)
        status = 'completed'
        date = now - timedelta(minutes=i*random.randint(1, 10))
        trades.append((date.strftime('%Y-%m-%d %H:%M:%S'), trade_type, symbol, amount, price, total, status))
    return trades

def insert_trades(trades):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for t in trades:
        cursor.execute('''
            INSERT INTO trades (date, type, symbol, amount, price, total, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', t)
    conn.commit()
    conn.close()

def main():
    trades = generate_trades(120)
    insert_trades(trades)
    print(f"Inseridos {len(trades)} trades de exemplo.")

if __name__ == '__main__':
    main()
