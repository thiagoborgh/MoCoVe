import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import logging
import requests

# Config
DB_PATH = 'memecoin.db'
FUTURE_WINDOW = 15  # minutos à frente para calcular variação
THRESHOLD = 0.01   # 1% para BUY/SELL

# Configurar logging
logging.basicConfig(
    filename='train_model.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logging.info('Iniciando treinamento do modelo')

# 1. Extrair dados do SQLite
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query('SELECT * FROM prices ORDER BY coin_id, timestamp', conn)
conn.close()

# 2. Calcular features técnicas
for period in [9, 21, 50]:
    df[f'sma{period}'] = df.groupby('coin_id')['price'].transform(lambda x: x.rolling(period).mean())

def get_sentiment(symbol):
    try:
        r = requests.get(f'http://localhost:5000/api/sentiment?symbol={symbol}')
        if r.status_code == 200:
            data = r.json()
            return data.get('overall', 0.5)
    except Exception as e:
        logging.warning(f'Erro ao buscar sentimento para {symbol}: {e}')
    return 0.5

# Integrar sentimento real
sentiment_map = {}
for symbol in df['coin_id'].unique():
    sentiment_map[symbol] = get_sentiment(symbol)
df['sentiment'] = df['coin_id'].map(sentiment_map)
logging.info(f'Sentimento integrado para moedas: {list(sentiment_map.keys())}')

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
try:
    clf.fit(X_train, y_train)
    logging.info('Modelo treinado com sucesso')
    print(classification_report(y_test, clf.predict(X_test)))
    logging.info('Relatório de classificação:\n' + classification_report(y_test, clf.predict(X_test)))
    joblib.dump(clf, 'memecoin_rf_model.pkl')
    logging.info('Modelo salvo em memecoin_rf_model.pkl')
    print('Modelo salvo em memecoin_rf_model.pkl')
except Exception as e:
    logging.error(f'Erro no treinamento: {e}')
    print(f'Erro no treinamento: {e}')
