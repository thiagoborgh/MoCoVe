import sqlite3

db_path = "memecoin.db"
tables = ["account_balance", "market_data", "social_sentiment", "system_status"]

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for table in tables:
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN timestamp DATETIME;")
        print(f"Coluna 'timestamp' adicionada em {table}")
    except Exception as e:
        print(f"Erro em {table}: {e}")

conn.commit()
conn.close()
print("Finalizado!")
