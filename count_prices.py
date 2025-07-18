import sqlite3
conn = sqlite3.connect('memecoin.db')
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM prices;")
print("Total de registros em prices:", cur.fetchone()[0])
conn.close()
