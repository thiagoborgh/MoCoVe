import sqlite3

conn = sqlite3.connect('memecoin.db')
cursor = conn.cursor()

# 1. Descobrir as colunas atuais
cursor.execute("PRAGMA table_info(social_sentiment);")
columns = cursor.fetchall()
print("Colunas atuais:", [col[1] for col in columns])

# 2. Definir as colunas desejadas (ajuste conforme sua necessidade real)
desired_columns = [
    "id INTEGER PRIMARY KEY AUTOINCREMENT",
    "symbol TEXT NOT NULL",
    "timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "sentiment_score REAL",
    "volume_mentions INTEGER",
    "positive_ratio REAL",
    "negative_ratio REAL",
    "neutral_ratio REAL"
]

# 3. Criar nova tabela temporária
cursor.execute("DROP TABLE IF EXISTS social_sentiment_new;")
cursor.execute(f"CREATE TABLE social_sentiment_new ({', '.join(desired_columns)});")

# 4. Copiar dados das colunas existentes (ajuste os nomes conforme necessário)
existing_cols = [col[1] for col in columns if col[1] in [c.split()[0] for c in desired_columns]]
cols_str = ", ".join(existing_cols)
cursor.execute(f"INSERT INTO social_sentiment_new ({cols_str}) SELECT {cols_str} FROM social_sentiment;")

# 5. Substituir a tabela antiga pela nova
cursor.execute("DROP TABLE social_sentiment;")
cursor.execute("ALTER TABLE social_sentiment_new RENAME TO social_sentiment;")

conn.commit()
conn.close()
print("Tabela social_sentiment atualizada com sucesso!")