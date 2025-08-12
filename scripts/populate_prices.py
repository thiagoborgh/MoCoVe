import sqlite3
import requests
import time
from datetime import datetime

# Lista das principais memecoins (CoinGecko IDs)
memecoins = [
    'dogecoin', 'shiba-inu', 'pepe', 'dogwifhat', 'bonk',
    'floki', 'milady', 'trump', 'pudgy-penguins', 'mog-coin', 'brett'
]

DB_PATH = 'memecoin.db'
DAYS = 90  # Quantos dias de histórico buscar

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

for coin_id in memecoins:
    print(f'Baixando histórico de {coin_id}...')
    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={DAYS}'
    r = requests.get(url)
    if r.status_code != 200:
        print(f'Erro ao buscar {coin_id}:', r.text)
        continue
    data = r.json()
    prices = data.get('prices', [])
    for i in range(1, len(prices)):
        ts = int(prices[i][0] // 1000)
        dt = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        price = float(prices[i][1])
        prev_price = float(prices[i-1][1])
        volume_change = (price / prev_price - 1) if prev_price != 0 else 0
        c.execute('INSERT INTO prices (coin_id, timestamp, price, volume_change) VALUES (?, ?, ?, ?)',
                  (coin_id, dt, price, volume_change))
    conn.commit()
    print(f'{len(prices)} registros inseridos para {coin_id}')
    time.sleep(2)  # Evita rate limit

conn.close()
print('População concluída!')
