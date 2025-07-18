import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# Config
DB_PATH = 'memecoin.db'
FUTURE_WINDOW = 15  # minutos à frente para calcular variação
THRESHOLD = 0.01   # 1% para BUY/SELL

# 1. Extrair dados do SQLite
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query('SELECT * FROM prices ORDER BY coin_id, timestamp', conn)
conn.close()

# 2. Calcular features técnicas
for period in [9, 21, 50]:
    df[f'sma{period}'] = df.groupby('coin_id')['price'].transform(lambda x: x.rolling(period).mean())
df['rsi'] = df.groupby('coin_id')['price'].transform(lambda x: x.rolling(15).apply(lambda s: 100 - 100/(1 + (s.diff().clip(lower=0).sum() / abs(s.diff().clip(upper=0)).sum() if abs(s.diff().clip(upper=0)).sum() != 0 else 1)), raw=False))
df['min24h'] = df.groupby('coin_id')['price'].transform(lambda x: x.rolling(24).min())
df['max24h'] = df.groupby('coin_id')['price'].transform(lambda x: x.rolling(24).max())
df['var24h'] = df.groupby('coin_id')['price'].transform(lambda x: (x - x.shift(24)) / x.shift(24))
df['sentiment'] = 0.5  # Placeholder, pode integrar depois

# 3. Calcular target (variação futura)
df['future_price'] = df.groupby('coin_id')['price'].shift(-FUTURE_WINDOW)
df['future_return'] = (df['future_price'] - df['price']) / df['price']
def label(row):
    if row['future_return'] > THRESHOLD:
        return 1  # BUY
    elif row['future_return'] < -THRESHOLD:
        return -1 # SELL
    else:
        return 0  # HOLD
df['target'] = df.apply(label, axis=1)

# 4. Limpar e preparar
features = ['price','sma9','sma21','sma50','rsi','min24h','max24h','var24h','sentiment']
df = df.dropna(subset=features+['target'])
X = df[features].values
y = df['target'].values

# 5. Treinar modelo
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)
print(classification_report(y_test, clf.predict(X_test)))

# 6. Salvar modelo
joblib.dump(clf, 'memecoin_rf_model.pkl')
print('Modelo salvo em memecoin_rf_model.pkl')
