import sqlite3

import pathlib
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
DB_PATH = str(PROJECT_ROOT / 'memecoin.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print('--- TRADES REGISTRADOS ---')
for row in cursor.execute('SELECT id, date, type, symbol, amount, price, total, status FROM trades ORDER BY date DESC LIMIT 20'):
    print(row)

conn.close()
