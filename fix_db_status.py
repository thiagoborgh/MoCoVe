import sqlite3

# Caminho do banco de dados
DB_PATH = 'memecoin.db'

# Tabelas que podem precisar da coluna 'status'
tabelas = [
    'account_balance',
    'market_data',
    'social_sentiment',
    'system_status'
]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for tabela in tabelas:
    try:
        # Verifica se a coluna 'status' já existe
        cursor.execute(f"PRAGMA table_info({tabela})")
        colunas = [info[1] for info in cursor.fetchall()]
        if 'status' not in colunas:
            cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN status TEXT")
            print(f"Coluna 'status' adicionada em {tabela}")
        else:
            print(f"Coluna 'status' já existe em {tabela}")
    except Exception as e:
        print(f"Erro em {tabela}: {e}")

conn.commit()
conn.close()
print("Finalizado!")
