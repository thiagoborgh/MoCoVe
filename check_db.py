import sqlite3

# Verificar estrutura do banco
conn = sqlite3.connect('memecoin.db')
cursor = conn.cursor()

print("=== ESTRUTURA DO BANCO ===")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

for table in tables:
    print(table[0])
    print("-" * 50)

print("\n=== DADOS EXISTENTES ===")

# Verificar trades
try:
    cursor.execute("SELECT COUNT(*) FROM trades")
    print(f"Trades: {cursor.fetchone()[0]} registros")
except:
    print("Tabela trades não existe")

# Verificar prices
try:
    cursor.execute("SELECT COUNT(*) FROM prices") 
    print(f"Prices: {cursor.fetchone()[0]} registros")
except:
    print("Tabela prices não existe")

# Verificar settings
try:
    cursor.execute("SELECT COUNT(*) FROM settings")
    print(f"Settings: {cursor.fetchone()[0]} registros")
except:
    print("Tabela settings não existe")

conn.close()
