#!/usr/bin/env python3
"""
MoCoVe Model Training – Versão Pro
Treinamento robusto para predição de sinais (BUY/SELL/HOLD) em memecoins, com:
- Extração de dados do SQLite (tabela `prices`) com fallback para colunas OHLC/volume
- Engenharia de features técnicas otimizadas (SMA/EMA/RSI/Bollinger/MACD/ATR/Vol/Z-Volume)
- Rotulagem configurável: `threshold` (retorno futuro) ou `triple_barrier` (ATR/pct + holding)
- Split temporal (sem vazamento): treino inicial, teste final (por tempo) + CV com TimeSeriesSplit e gap
- Classe desbalanceada: `class_weight='balanced'` (RF) e métricas separadas para BUY/SELL
- Otimização de thresholds de probabilidade com objetivo de retorno esperado líquido (com taxas/slippage)
- Backtest simples de estratégia baseada nas previsões no conjunto de teste
- Salvamento de artefatos: modelo, scaler (se usado), metadata e thresholds

⚠️ Aviso: uso educacional. Risco elevado. Evite usar sentimentos em tempo real durante treino para não vazar informação.
"""

from __future__ import annotations
import os
import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import joblib
import logging

# =====================
# Configuração & Logging
# =====================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("moco_train")

@dataclass
class Config:
    # Paths
    project_root: str = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path: str = os.getenv('DB_PATH') or os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), 'memecoin.db')
    artifacts_dir: str = os.getenv('ARTIFACTS_DIR', './artifacts')
    model_path: str = os.getenv('MODEL_PATH', 'memecoin_model.pkl')
    scaler_path: str = os.getenv('SCALER_PATH', 'memecoin_scaler.pkl')

    # Rotulagem
    label_method: str = os.getenv('LABEL_METHOD', 'threshold')  # 'threshold' | 'triple_barrier'
    future_window: int = int(os.getenv('FUTURE_WINDOW', '15'))  # em "barras" (ex: minutos) à frente
    buy_threshold: float = float(os.getenv('BUY_THRESHOLD', '0.02'))
    sell_threshold: float = float(os.getenv('SELL_THRESHOLD', '-0.02'))

    # Triple barrier
    tb_upper_mult_atr: float = float(os.getenv('TB_UPPER_ATR', '1.5'))
    tb_lower_mult_atr: float = float(os.getenv('TB_LOWER_ATR', '1.0'))
    tb_max_holding: int = int(os.getenv('TB_MAX_HOLD', '30'))
    tb_use_atr: bool = os.getenv('TB_USE_ATR', 'true').lower() == 'true'
    tb_upper_pct: float = float(os.getenv('TB_UPPER_PCT', '0.03'))  # se não usar ATR
    tb_lower_pct: float = float(os.getenv('TB_LOWER_PCT', '0.02'))

    # Modelo
    use_scaler: bool = os.getenv('USE_SCALER', 'false').lower() == 'true'  # árvores não precisam
    random_state: int = int(os.getenv('RANDOM_STATE', '42'))
    n_estimators: int = int(os.getenv('RF_TREES', '300'))
    max_depth: Optional[int] = int(os.getenv('RF_MAX_DEPTH', '12')) if os.getenv('RF_MAX_DEPTH', '') else None
    min_samples_split: int = int(os.getenv('RF_MIN_SPLIT', '5'))
    min_samples_leaf: int = int(os.getenv('RF_MIN_LEAF', '2'))

    # Split temporal
    test_size_frac: float = float(os.getenv('TEST_FRACTION', '0.2'))
    cv_splits: int = int(os.getenv('CV_SPLITS', '5'))
    cv_gap: int = int(os.getenv('CV_GAP', '3'))  # gap para reduzir vazamento entre folds

    # Otimização de thresholds
    fee_pct: float = float(os.getenv('FEE_PCT', '0.001'))  # 0.1% por lado
    slippage_pct: float = float(os.getenv('SLIPPAGE_PCT', '0.0005'))

cfg = Config()
os.makedirs(cfg.artifacts_dir, exist_ok=True)

# =====================
# Utilitários
# =====================

def to_dt(x):
    try:
        return pd.to_datetime(x, utc=True)
    except Exception:
        return pd.to_datetime(x)

# Indicadores técnicos
class TA:
    @staticmethod
    def sma(s: pd.Series, n: int) -> pd.Series:
        return s.rolling(n, min_periods=1).mean()

    @staticmethod
    def ema(s: pd.Series, n: int) -> pd.Series:
        return s.ewm(span=n, adjust=False).mean()

    @staticmethod
    def rsi(s: pd.Series, n: int = 14) -> pd.Series:
        delta = s.diff()
        gain = delta.clip(lower=0).rolling(n, min_periods=1).mean()
        loss = (-delta.clip(upper=0)).rolling(n, min_periods=1).mean()
        rs = gain / loss.replace(0, np.inf)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def bollinger(s: pd.Series, n: int = 20, k: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        m = s.rolling(n, min_periods=1).mean()
        sd = s.rolling(n, min_periods=1).std(ddof=0)
        up = m + k * sd
        lo = m - k * sd
        return up, m, lo

    @staticmethod
    def macd(s: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
        ema_f = s.ewm(span=fast, adjust=False).mean()
        ema_s = s.ewm(span=slow, adjust=False).mean()
        macd = ema_f - ema_s
        sig = macd.rolling(signal, min_periods=1).mean()
        return macd, sig

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
        # TR baseado em OHLC; fallback para close-only
        if not high.isnull().all() and not low.isnull().all():
            prev_close = close.shift(1)
            tr = pd.concat([
                (high - low),
                (high - prev_close).abs(),
                (low - prev_close).abs()
            ], axis=1).max(axis=1)
            return tr.rolling(n, min_periods=1).mean()
        else:
            return close.pct_change().abs().rolling(n, min_periods=1).mean() * close

# =====================
# 1) Extração de dados
# =====================

def extract_data_from_db(db_path: str) -> pd.DataFrame:
    logger.info("Extraindo dados do banco...")
    con = sqlite3.connect(db_path)
    q = (
        "SELECT symbol as coin_id, timestamp, price, volume, "
        "COALESCE(high, price) as high, COALESCE(low, price) as low, COALESCE(close, price) as close "
        "FROM prices WHERE price > 0 ORDER BY symbol, timestamp"
    )
    df = pd.read_sql_query(q, con)
    # Forçar coin_id a ser sempre string e 1D
    if 'coin_id' in df.columns:
        df['coin_id'] = df['coin_id'].apply(lambda x: x[0] if isinstance(x, (list, tuple, np.ndarray, pd.Series)) else x)
        df['coin_id'] = df['coin_id'].astype(str)
    con.close()
    if df.empty:
        raise ValueError("Nenhum dado encontrado em prices")
    df['timestamp'] = df['timestamp'].apply(to_dt)
    logger.info(f"Registros: {len(df):,} | Moedas: {df['coin_id'].nunique()}")
    return df

# =====================
# 2) Engenharia de Features
# =====================

def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Calculando features técnicas...")
    # Garantir que coin_id é 1D
    df = df.copy()
    if not df.empty and isinstance(df['coin_id'].iloc[0], (list, tuple, np.ndarray, pd.Series)):
        df['coin_id'] = df['coin_id'].astype(str)
    g = df.groupby('coin_id', group_keys=False)

    def _feat(group: pd.DataFrame) -> pd.DataFrame:
        p = group['price']
        v = group['volume'] if 'volume' in group else pd.Series(0, index=group.index)
        h, l, c = group['high'], group['low'], group['close']

        out = pd.DataFrame(index=group.index)
        out['price'] = p
        # Médias
        out['sma9'] = TA.sma(p, 9)
        out['sma21'] = TA.sma(p, 21)
        out['sma50'] = TA.sma(p, 50)
        out['ema12'] = TA.ema(p, 12)
        out['ema26'] = TA.ema(p, 26)
        # RSI/Bollinger
        out['rsi'] = TA.rsi(p, 14)
        bb_up, bb_mid, bb_lo = TA.bollinger(p, 21, 2.0)
        out['bb_upper'] = bb_up
        out['bb_lower'] = bb_lo
        out['bb_pos'] = (p - bb_lo) / (bb_up - bb_lo).replace(0, np.nan)
        # MACD
        macd, macd_sig = TA.macd(p)
        out['macd'] = macd
        out['macd_signal'] = macd_sig
        # Volatilidade e ATR
        out['volatility'] = p.pct_change().rolling(20, min_periods=1).std()
        out['atr'] = TA.atr(h, l, c, 14)
        # Z-score de volume
        v_mean = v.rolling(48, min_periods=1).mean()
        v_std = v.rolling(48, min_periods=1).std(ddof=0).replace(0, np.nan)
        out['volume_z'] = (v - v_mean) / v_std
        # Extremos 24b
        out['min24'] = p.rolling(24, min_periods=1).min()
        out['max24'] = p.rolling(24, min_periods=1).max()
        out['var24'] = (p - p.shift(24)) / p.shift(24)
        return out

    feats = g.apply(_feat)
    feats.reset_index(drop=True, inplace=True)
    out = pd.concat([df[['coin_id', 'timestamp']], feats], axis=1)
    logger.info(f"Features calculadas: {len(out)} linhas")
    return out

# =====================
# 3) Rotulagem
# =====================

def label_threshold(df: pd.DataFrame, future_window: int, buy_thr: float, sell_thr: float) -> pd.Series:
    # Garantir que coin_id é 1D
    df = df.copy()
    if not df.empty and isinstance(df['coin_id'].iloc[0], (list, tuple, np.ndarray, pd.Series)):
        df['coin_id'] = df['coin_id'].astype(str)
    g = df.groupby('coin_id', group_keys=False)
    future_price = g['price'].shift(-future_window)
    future_ret = (future_price - df['price']) / df['price']
    # thresholds levemente mais conservadores
    buy_t = buy_thr * 1.5
    sell_t = sell_thr * 1.5
    label = np.where(future_ret > buy_t, 1, np.where(future_ret < sell_t, -1, 0))
    return pd.Series(label, index=df.index), future_ret

def label_triple_barrier(df: pd.DataFrame, max_holding: int, use_atr: bool,
                         up_mult_atr: float, lo_mult_atr: float,
                         up_pct: float, lo_pct: float) -> pd.Series:
    labels = np.zeros(len(df), dtype=int)
    # Garantir que coin_id é 1D
    df = df.copy()
    if not df.empty and isinstance(df['coin_id'].iloc[0], (list, tuple, np.ndarray, pd.Series)):
        df['coin_id'] = df['coin_id'].astype(str)
    g = df.groupby('coin_id', group_keys=False)
    idx = 0
    for _, grp in g:
        p = grp['price'].values
        atr = grp['atr'].values if use_atr else None
        for i in range(len(grp)):
            entry = p[i]
            if i == len(grp) - 1:
                labels[idx] = 0; idx += 1; continue
            up = (entry + (up_mult_atr * atr[i])) if use_atr else entry * (1 + up_pct)
            lo = (entry - (lo_mult_atr * atr[i])) if use_atr else entry * (1 - lo_pct)
            end = min(i + max_holding, len(grp) - 1)
            hit = 0
            for j in range(i + 1, end + 1):
                if p[j] >= up:
                    hit = 1; break
                if p[j] <= lo:
                    hit = -1; break
            labels[idx] = hit
            idx += 1
    return pd.Series(labels, index=df.index)

# =====================
# 4) Preparação de dados
# =====================

FEATURES = ['price','sma9','sma21','sma50','ema12','ema26','rsi','bb_pos','macd','macd_signal','volatility','atr','volume_z','min24','max24','var24']

def prepare_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, Dict]:
    # Limpeza de NaNs iniciais
    clean = df.dropna(subset=['price'])

    # Rotulagem
    if cfg.label_method == 'triple_barrier':
        y = label_triple_barrier(
            clean,
            max_holding=cfg.tb_max_holding,
            use_atr=cfg.tb_use_atr,
            up_mult_atr=cfg.tb_upper_mult_atr,
            lo_mult_atr=cfg.tb_lower_mult_atr,
            up_pct=cfg.tb_upper_pct,
            lo_pct=cfg.tb_lower_pct,
        )
        future_ret = None
    else:
        y, future_ret = label_threshold(clean, cfg.future_window, cfg.buy_threshold, cfg.sell_threshold)

    clean = clean.assign(target=y)

    # Log de NaNs por coluna antes do dropna
    logger.info("NaNs por coluna antes do dropna:")
    logger.info(clean[FEATURES + ['target']].isna().sum())

    # Preencher NaNs em features não críticas
    clean['volume_z'] = clean['volume_z'].fillna(0)
    clean['var24'] = clean['var24'].fillna(0)
    clean['volatility'] = clean['volatility'].fillna(0)
    clean['rsi'] = clean['rsi'].fillna(0)
    clean['bb_pos'] = clean['bb_pos'].fillna(0)

    # Drop NaNs em features e target
    clean = clean.dropna(subset=FEATURES + ['target'])

    logger.info(f"Após limpeza: {len(clean)} linhas")

    X = clean[FEATURES].copy()
    y = clean['target'].astype(int)

    meta = {
        'n_samples': int(len(clean)),
        'n_coins': int(clean['coin_id'].nunique()),
        'label_method': cfg.label_method,
        'future_window': cfg.future_window,
        'features': FEATURES,
    }
    if future_ret is not None:
        meta['has_future_ret'] = True
    return X, y, clean, meta

# =====================
# 5) Split temporal & CV
# =====================

def temporal_train_test_split(df: pd.DataFrame, test_frac: float) -> np.ndarray:
    # Define corte temporal global preservando ordem por timestamp
    if df.empty or len(df['timestamp']) == 0:
        return np.array([], dtype=bool)
    ts_sorted = df['timestamp'].sort_values().values
    cutoff = ts_sorted[int((1 - test_frac) * len(ts_sorted))]
    test_mask = df['timestamp'].values >= cutoff
    return test_mask

# =====================
# 6) Modelo e treino
# =====================

def train_model(X: pd.DataFrame, y: pd.Series) -> Tuple[object, Optional[StandardScaler]]:
    scaler = None
    X_train = X.values
    if cfg.use_scaler:
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)

    clf = RandomForestClassifier(
        n_estimators=cfg.n_estimators,
        max_depth=cfg.max_depth,
        min_samples_split=cfg.min_samples_split,
        min_samples_leaf=cfg.min_samples_leaf,
        random_state=cfg.random_state,
        class_weight='balanced'
    )
    clf.fit(X_train, y)
    return clf, scaler

# =====================
# 7) Otimização de thresholds (probabilidade)
# =====================

def optimize_thresholds(model, scaler, X_val: pd.DataFrame, y_val: pd.Series, future_ret: Optional[pd.Series]) -> Dict[str, float]:
    """Escolhe limiares p(BUY) e p(SELL) para maximizar retorno esperado.
       Se `future_ret` não existir (triple_barrier), otimiza F1 por classe.
    """
    from sklearn.metrics import f1_score

    Xv = X_val.values
    if scaler is not None:
        Xv = scaler.transform(Xv)

    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(Xv)
        # Mapear colunas: classes podem vir como [-1,0,1] em ordem arbitrária
        classes = list(model.classes_)
        idx_buy = classes.index(1) if 1 in classes else None
        idx_sell = classes.index(-1) if -1 in classes else None
        idx_hold = classes.index(0) if 0 in classes else None
    else:
        # fallback: usar previsões duras
        proba = None

    thresholds = {'buy_p': 0.5, 'sell_p': 0.5}

    if proba is None:
        return thresholds

    # custos
    round_trip_cost = 2 * cfg.fee_pct + cfg.slippage_pct

    if future_ret is not None:
        # busca simples por melhor p* em grade
        grid = np.linspace(0.3, 0.9, 13)
        best_ev = -1e9
        best = (0.5, 0.5)
        fr = future_ret.loc[y_val.index]
        for pb in grid:
            for ps in grid:
                # sinais
                is_buy = proba[:, idx_buy] >= pb if idx_buy is not None else np.zeros(len(y_val), dtype=bool)
                is_sell = proba[:, idx_sell] >= ps if idx_sell is not None else np.zeros(len(y_val), dtype=bool)
                # resolver conflitos: prioriza maior prob entre buy/sell
                choose = np.full(len(y_val), 0)
                for i in range(len(y_val)):
                    if is_buy[i] and is_sell[i]:
                        choose[i] = 1 if proba[i, idx_buy] >= proba[i, idx_sell] else -1
                    elif is_buy[i]:
                        choose[i] = 1
                    elif is_sell[i]:
                        choose[i] = -1
                # retorno esperado
                ret = fr.values.copy()
                # BUY ganha futuro_ret, SELL ganha -futuro_ret
                pnl = np.where(choose == 1, ret, np.where(choose == -1, -ret, 0.0))
                # aplicar custos nas operações != 0
                costs = (np.abs(choose) > 0).astype(float) * round_trip_cost
                pnl_net = pnl - costs
                ev = pnl_net.mean()
                if ev > best_ev:
                    best_ev = ev; best = (float(pb), float(ps))
        thresholds = {'buy_p': best[0], 'sell_p': best[1]}
        logger.info(f"Thresholds ótimos por EV líquido: BUY>={best[0]:.2f}, SELL>={best[1]:.2f} | EV={best_ev:.5f}")
    else:
        # otimize F1 por classe quando não há futuro_ret direto
        grid = np.linspace(0.3, 0.9, 13)
        best_b, best_s = 0.5, 0.5
        best_f1_b, best_f1_s = -1, -1
        for p in grid:
            yhat = np.where(proba[:, idx_buy] >= p, 1, 0)
            f1b = f1_score((y_val==1).astype(int), yhat)
            if f1b > best_f1_b:
                best_f1_b, best_b = f1b, float(p)
        for p in grid:
            yhat = np.where(proba[:, idx_sell] >= p, 1, 0)
            f1s = f1_score((y_val==-1).astype(int), yhat)
            if f1s > best_f1_s:
                best_f1_s, best_s = f1s, float(p)
        thresholds = {'buy_p': best_b, 'sell_p': best_s}
        logger.info(f"Thresholds ótimos por F1: BUY>={best_b:.2f} (F1={best_f1_b:.3f}), SELL>={best_s:.2f} (F1={best_f1_s:.3f})")

    return thresholds

# =====================
# 8) Avaliação & Backtest simples
# =====================

def evaluate(model, scaler, X_test: pd.DataFrame, y_test: pd.Series, thresholds: Dict[str,float], future_ret: Optional[pd.Series]):
    Xt = X_test.values
    if scaler is not None:
        Xt = scaler.transform(Xt)

    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(Xt)
        classes = list(model.classes_)
        idx_buy = classes.index(1) if 1 in classes else None
        idx_sell = classes.index(-1) if -1 in classes else None
        # Sinais por thresholds
        pb, ps = thresholds['buy_p'], thresholds['sell_p']
        is_buy = proba[:, idx_buy] >= pb if idx_buy is not None else np.zeros(len(y_test), dtype=bool)
        is_sell = proba[:, idx_sell] >= ps if idx_sell is not None else np.zeros(len(y_test), dtype=bool)
        preds = np.zeros(len(y_test), dtype=int)
        for i in range(len(y_test)):
            if is_buy[i] and is_sell[i]:
                preds[i] = 1 if proba[i, idx_buy] >= proba[i, idx_sell] else -1
            elif is_buy[i]:
                preds[i] = 1
            elif is_sell[i]:
                preds[i] = -1
            else:
                preds[i] = 0
    else:
        preds = model.predict(Xt)

    # Relatórios
    report = classification_report(y_test, preds, digits=3)
    cm = confusion_matrix(y_test, preds, labels=[1,0,-1])
    logger.info("\n" + report)
    logger.info(f"Confusion matrix (rows=true, cols=pred) [1,0,-1]:\n{cm}")

    backtest = None
    if future_ret is not None:
        fr = future_ret.loc[y_test.index]
        round_trip_cost = 2 * cfg.fee_pct + cfg.slippage_pct
        pnl = np.where(preds == 1, fr.values, np.where(preds == -1, -fr.values, 0.0))
        costs = (np.abs(preds) > 0).astype(float) * round_trip_cost
        pnl_net = pnl - costs
        win_rate = (pnl_net > 0).mean() if len(pnl_net) else 0.0
        backtest = {
            'signals': int((np.abs(preds) > 0).sum()),
            'win_rate': float(win_rate),
            'avg_return_net': float(pnl_net.mean()) if len(pnl_net) else 0.0,
            'sum_return_net': float(pnl_net.sum()) if len(pnl_net) else 0.0,
        }
        logger.info(f"Backtest simples – sinais: {backtest['signals']} | win%: {100*backtest['win_rate']:.1f}% | avg_ret_net: {backtest['avg_return_net']:.5f}")
    return report, cm, backtest, preds

# =====================
# 9) Salvamento de artefatos
# =====================

def save_artifacts(model, scaler, metadata: Dict, thresholds: Dict[str,float]):
    joblib.dump(model, os.path.join(cfg.artifacts_dir, cfg.model_path))
    logger.info(f"Modelo salvo em {os.path.join(cfg.artifacts_dir, cfg.model_path)}")
    if scaler is not None:
        joblib.dump(scaler, os.path.join(cfg.artifacts_dir, cfg.scaler_path))
        logger.info(f"Scaler salvo em {os.path.join(cfg.artifacts_dir, cfg.scaler_path)}")
    meta = dict(metadata)
    meta['training_date'] = datetime.utcnow().isoformat()
    meta['thresholds'] = thresholds
    meta_path = os.path.join(cfg.artifacts_dir, cfg.model_path.replace('.pkl', '_metadata.json'))
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Metadata salva em {meta_path}")

# =====================
# 10) Main
# =====================

def main():
    logger.info("=== MoCoVe Training Pro – início ===")
    # 1) Dados
    raw = extract_data_from_db(cfg.db_path)
    feats = calculate_features(raw)

    # 2) Dataset
    X, y, joined, meta = prepare_dataset(feats)

    # 3) Split temporal
    test_mask = temporal_train_test_split(joined, cfg.test_size_frac)
    X_train, X_test = X[~test_mask], X[test_mask]
    y_train, y_test = y[~test_mask], y[test_mask]

    # Para otimizar thresholds por EV, precisamos de future_return quando label_method='threshold'
    future_ret = None
    if cfg.label_method == 'threshold':
        # Recriar future_return para linhas válidas
        _, fr_full = label_threshold(joined, cfg.future_window, cfg.buy_threshold, cfg.sell_threshold)
        future_ret = fr_full

    # 4) Treino
    if X_train.shape[0] == 0 or y_train.shape[0] == 0:
        logger.warning("Sem dados suficientes para treinar o modelo. Treinamento ignorado.")
        return
    model, scaler = train_model(X_train, y_train)

    # 5) Otimização de thresholds usando um pedaço do train (validação) ou diretamente test
    # Aqui usamos a parte final do treino como validação temporal
    if len(X_train) > 100:
        val_frac = 0.2
        n_val = int(len(X_train) * val_frac)
        X_val = X_train.iloc[-n_val:]
        y_val = y_train.iloc[-n_val:]
    else:
        X_val, y_val = X_test, y_test
    thresholds = optimize_thresholds(model, scaler, X_val, y_val, future_ret)

    # 6) Avaliação
    report, cm, backtest, preds = evaluate(model, scaler, X_test, y_test, thresholds, future_ret)

    # 7) Importâncias de features
    if hasattr(model, 'feature_importances_'):
        fi = pd.DataFrame({'feature': X.columns, 'importance': model.feature_importances_}).sort_values('importance', ascending=False)
        logger.info("Top features:\n" + fi.head(12).to_string(index=False))
        fi_path = os.path.join(cfg.artifacts_dir, cfg.model_path.replace('.pkl', '_feature_importance.csv'))
        os.makedirs(os.path.dirname(fi_path), exist_ok=True)
        fi.to_csv(fi_path, index=False)

    # 8) Salvar
    metadata = {
        **meta,
        'test_size_frac': cfg.test_size_frac,
        'model': 'RandomForestClassifier',
        'params': {
            'n_estimators': cfg.n_estimators,
            'max_depth': cfg.max_depth,
            'min_samples_split': cfg.min_samples_split,
            'min_samples_leaf': cfg.min_samples_leaf,
            'class_weight': 'balanced',
            'random_state': cfg.random_state,
        },
        'report': report,
        'confusion_matrix': cm.tolist(),
        'backtest': backtest,
    }
    save_artifacts(model, scaler, metadata, thresholds)

    logger.info("=== Treinamento concluído com sucesso ===")

if __name__ == '__main__':
    main()
