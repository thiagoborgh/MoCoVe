import sqlite3

DB_PATH = 'memecoin.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

try:
    c.execute("ALTER TABLE prices ADD COLUMN volume REAL DEFAULT 0;")
    print("Coluna 'volume' adicionada com sucesso.")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e) or 'already exists' in str(e):
        print("A coluna 'volume' já existe.")
    else:
        print(f"Erro ao adicionar coluna: {e}")
finally:
    conn.commit()
    conn.close()
