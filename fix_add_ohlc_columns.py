import sqlite3

DB_PATH = 'memecoin.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Adiciona coluna se não existir
for col in [
    ("high", "REAL", 0),
    ("low", "REAL", 0),
    ("close", "REAL", 0)
]:
    try:
        c.execute(f"ALTER TABLE prices ADD COLUMN {col[0]} {col[1]} DEFAULT {col[2]};")
        print(f"Coluna '{col[0]}' adicionada com sucesso.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e) or 'already exists' in str(e):
            print(f"A coluna '{col[0]}' já existe.")
        else:
            print(f"Erro ao adicionar coluna {col[0]}: {e}")

conn.commit()
conn.close()
