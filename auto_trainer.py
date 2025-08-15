#!/usr/bin/env python3
"""
Auto Trainer MoCoVe: coleta histórico Binance, engenharia de features, labeling, treino, salva modelo e thresholds para uso direto pelo Agente Pro.
- Coleta candles 1m, 5m, 15m das memecoins (lista editável)
- Salva no memecoin.db
- Feature engineering completa
- Labeling triple-barrier
- Treina (XGBoost se disponível, senão RandomForest)
- Salva artefatos em ./runtime/model/
- Agendamento diário automático (05:00 UTC)
"""
import os
import time
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import logging

# Binance
try:
    from binance.client import Client
except ImportError:
    raise ImportError("python-binance não instalado. Instale com: pip install python-binance")

# ML
try:
    from xgboost import XGBClassifier
    XGB_OK = True
except ImportError:
    from sklearn.ensemble import RandomForestClassifier
    XGB_OK = False
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import classification_report
import joblib

# Config
MODEL_DIR = Path("./runtime/model")
MODEL_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = str(Path("memecoin.db").absolute())
SYMBOLS = ["DOGEUSDT", "PEPEUSDT", "SHIBUSDT", "FLOKIUSDT", "BONKUSDT"]  # Edite aqui
INTERVALS = ["1m", "5m", "15m"]
START_DAYS = 30  # Quantos dias de histórico buscar
API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("auto_trainer")

# --- Coleta de dados Binance ---
def fetch_binance(symbol, interval, start_days=30):
    client = Client(API_KEY, API_SECRET)
    end = int(time.time() * 1000)
    start = int((datetime.utcnow() - timedelta(days=start_days)).timestamp() * 1000)
    klines = client.get_historical_klines(symbol, interval, start_str=start, end_str=end)
    df = pd.DataFrame(klines, columns=[
        'open_time','open','high','low','close','volume','close_time','quote_asset_vol','num_trades','taker_buy_base','taker_buy_quote','ignore'])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    for col in ['open','high','low','close','volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['symbol'] = symbol
    df['interval'] = interval
    return df[['symbol','interval','open_time','open','high','low','close','volume']]

def save_to_sqlite(df):
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('prices', conn, if_exists='append', index=False)
    conn.close()

# --- Feature Engineering ---
def add_features(df):
    df = df.sort_values(['symbol','open_time'])
    g = df.groupby('symbol')
    def _feat(gr):
        p = gr['close']
        out = pd.DataFrame(index=gr.index)
        out['sma9'] = p.rolling(9).mean()
        out['sma21'] = p.rolling(21).mean()
        out['ema12'] = p.ewm(span=12, adjust=False).mean()
        out['ema26'] = p.ewm(span=26, adjust=False).mean()
        delta = p.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain / loss.replace(0, np.inf)
        out['rsi'] = 100 - (100 / (1 + rs))
        m = p.rolling(21).mean()
        sd = p.rolling(21).std()
        out['bb_upper'] = m + 2*sd
        out['bb_lower'] = m - 2*sd
        out['bb_pos'] = (p - out['bb_lower']) / (out['bb_upper'] - out['bb_lower']).replace(0, np.nan)
        out['volatility'] = p.pct_change().rolling(20).std()
        out['min24'] = p.rolling(24).min()
        out['max24'] = p.rolling(24).max()
        out['var24'] = (p - p.shift(24)) / p.shift(24)
        return out
    feats = g.apply(_feat)
    feats.reset_index(drop=True, inplace=True)
    return pd.concat([df.reset_index(drop=True), feats], axis=1)

# --- Sentimento ---
def fetch_sentiment(symbol, ts):
    try:
        import requests
        r = requests.get(f"http://localhost:5000/api/sentiment?symbol={symbol}&timestamp={ts}", timeout=2)
        if r.ok:
            return r.json().get('sentiment', 0.5)
    except Exception:
        pass
    return 0.5

def add_sentiment(df):
    df['sentiment'] = [fetch_sentiment(row['symbol'], row['open_time']) for _, row in df.iterrows()]
    return df

# --- Labeling Triple-Barrier ---
def triple_barrier_label(df, up_pct=0.03, lo_pct=0.02, max_holding=30):
    labels = np.zeros(len(df), dtype=int)
    for i in range(len(df)):
        entry = df['close'].iloc[i]
        up = entry * (1 + up_pct)
        lo = entry * (1 - lo_pct)
        end = min(i + max_holding, len(df) - 1)
        hit = 0
        for j in range(i+1, end+1):
            if df['close'].iloc[j] >= up:
                hit = 1; break
            if df['close'].iloc[j] <= lo:
                hit = -1; break
        labels[i] = hit
    return labels

# --- Treinamento ---
def train_and_save(df):
    FEATURES = ['close','sma9','sma21','ema12','ema26','rsi','bb_pos','volatility','min24','max24','var24','sentiment']
    df = df.dropna(subset=FEATURES)
    X = df[FEATURES].values
    y = triple_barrier_label(df)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    if XGB_OK:
        model = XGBClassifier(n_estimators=200, max_depth=8, learning_rate=0.1, random_state=42, use_label_encoder=False, eval_metric='mlogloss')
    else:
        model = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, class_weight='balanced')
    model.fit(Xs, y)
    # Thresholds: simples (padrão)
    thresholds = {'buy_p': 0.5, 'sell_p': 0.5}
    # Salvar artefatos
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    model_fn = f"model_{ts}.pkl"
    scaler_fn = f"scaler_{ts}.pkl"
    meta_fn = f"model_{ts}_metadata.json"
    joblib.dump(model, MODEL_DIR/model_fn)
    joblib.dump(scaler, MODEL_DIR/scaler_fn)
    meta = {
        'model_filename': model_fn,
        'scaler_filename': scaler_fn,
        'thresholds': thresholds,
        'features': FEATURES,
        'train_time': ts
    }
    with open(MODEL_DIR/meta_fn, 'w') as f:
        json.dump(meta, f, indent=2)
    # Atualiza latest_model.json
    with open(MODEL_DIR/'latest_model.json', 'w') as f:
        json.dump(meta, f, indent=2)
    logging.info(f"Modelo salvo: {model_fn}, scaler: {scaler_fn}, meta: {meta_fn}")

# --- Agendamento diário ---
def daily_scheduler():
    while True:
        now = datetime.utcnow()
        next_run = now.replace(hour=5, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)
        wait = (next_run - now).total_seconds()
        logging.info(f"Próximo treino agendado para {next_run} UTC (em {wait/3600:.2f}h)")
        time.sleep(wait)
        try:
            main()
        except Exception as e:
            logging.error(f"Erro no treino automático: {e}")

# --- Main ---
def main():
    all_dfs = []
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            logging.info(f"Baixando {symbol} {interval}...")
            df = fetch_binance(symbol, interval, START_DAYS)
            save_to_sqlite(df)
            all_dfs.append(df)
    df = pd.concat(all_dfs, ignore_index=True)
    df = add_features(df)
    df = add_sentiment(df)
    train_and_save(df)

if __name__ == "__main__":
    import threading
    t = threading.Thread(target=daily_scheduler, daemon=True)
    t.start()
    main()
