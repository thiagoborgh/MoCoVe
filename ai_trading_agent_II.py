
import time
import joblib
import threading
import logging
import json
import requests  # Para fallback HTTP
from pathlib import Path
from datetime import datetime, timedelta

# === Auto-treinamento e recarregamento ===
MODEL_DIR = Path("./runtime/model")
MODEL_DIR.mkdir(parents=True, exist_ok=True)
CHECK_INTERVAL_HOURS = 1
TRAIN_INTERVAL_HOURS = 24
THRESHOLDS = {}
last_train_time = None
model = None
scaler = None

def load_latest_model():
    global model, scaler, THRESHOLDS
    latest_meta = MODEL_DIR / "latest_model.json"
    if latest_meta.exists():
        with open(latest_meta, "r") as f:
            meta = json.load(f)
        model_path = MODEL_DIR / meta["model_filename"]
        scaler_path = MODEL_DIR / meta["scaler_filename"]
        try:
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)
            THRESHOLDS = meta.get("thresholds", {})
            logging.info(f"[AutoML] Modelo carregado: {meta['model_filename']}, thresholds: {THRESHOLDS}")
        except Exception as e:
            logging.error(f"Erro ao carregar modelo/scaler: {e}")
            model = None
            scaler = None
    else:
        logging.info("[AutoML] Nenhum modelo encontrado, será treinado na próxima janela.")

def auto_train_loop():
    global last_train_time
    from ai.train_model import main as train_model
    while True:
        now = datetime.now()
        if not last_train_time or (now - last_train_time) >= timedelta(hours=TRAIN_INTERVAL_HOURS):
            logging.info(f"[AutoML] Iniciando treinamento automático...")
            train_model()
            last_train_time = now
            load_latest_model()
        time.sleep(CHECK_INTERVAL_HOURS * 3600)

def start_auto_training():
    t = threading.Thread(target=auto_train_loop, daemon=True)
    t.start()

# Inicialização do AutoML
load_latest_model()
start_auto_training()

#!/usr/bin/env python3
"""
MoCoVe AI Trading Agent – Versão Pro (revisada, robusta e com gestão de risco avançada)

Melhorias principais nesta versão:
- Arquitetura assíncrona (aiohttp) e IO não bloqueante
- Gestão de risco completa: SL/TP por ATR, trailing stop, OCO lógico
- Sizing por risco (stop-distance) + limites por volatilidade
- Limite de perda diária e cooldown após perda
- Reset diário automático, persistência de sinais/trades em .jsonl
- Indicadores otimizados em NumPy (SMA/EMA/RSI/Bollinger/ATR)
- Modo TESTE/REAL seguro via env; simulação de histórico quando faltar dado

⚠️ Aviso: Trading em cripto/memecoins envolve alto risco. Código educacional.
"""

import asyncio
import os
import json
import logging
import math
import requests  # Adicionado para solução de fallback
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np
import aiohttp
import contextlib

# ==========================
# Configuração
# ==========================

@dataclass
class Settings:
    api_base: str = os.getenv("MOCOVE_API_BASE", "http://localhost:5000")
    default_symbol: str = os.getenv("MOCOVE_SYMBOL", "DOGEUSDT")
    test_mode: bool = os.getenv("MOCOVE_TEST_MODE", "true").lower() == "true"
    verbose_logging: bool = os.getenv("MOCOVE_VERBOSE", "true").lower() == "true"

    # Regras de decisão
    min_confidence: float = float(os.getenv("MOCOVE_MIN_CONF", 0.45))
    max_daily_trades: int = int(os.getenv("MOCOVE_MAX_DAILY", 20))
    min_trade_interval_s: int = int(os.getenv("MOCOVE_MIN_INTERVAL", 180))

    # Risco base / sizing
    max_position_usd: float = float(os.getenv("MOCOVE_MAX_POS", 25))
    risk_per_trade_usd: float = float(os.getenv("MOCOVE_RISK_USD", 2.5))  # risco por trade
    maker_taker_fee_pct: float = float(os.getenv("MOCOVE_FEE_PCT", 0.001))  # 0.1% por lado (exemplo)
    daily_loss_limit_usd: float = float(os.getenv("MOCOVE_DAILY_LOSS", 15))
    cooldown_after_loss_s: int = int(os.getenv("MOCOVE_COOLDOWN", 300))

    # SL/TP e trailing
    use_atr_sl_tp: bool = os.getenv("MOCOVE_USE_ATR", "true").lower() == "true"
    atr_period: int = int(os.getenv("MOCOVE_ATR_PERIOD", 14))
    sl_atr_mult: float = float(os.getenv("MOCOVE_SL_ATR", 1.5))
    tp_rr: float = float(os.getenv("MOCOVE_TP_RR", 1.6))  # take = rr * risco
    use_trailing_stop: bool = os.getenv("MOCOVE_TRAIL", "true").lower() == "true"
    trail_atr_mult: float = float(os.getenv("MOCOVE_TRAIL_ATR", 1.0))
    trail_activation_rr: float = float(os.getenv("MOCOVE_TRAIL_ACT_RR", 1.0))

    # Volatilidade / dados
    volatility_threshold: float = float(os.getenv("MOCOVE_VOL_THR", 3.0))  # %
    rsi_period: int = 10
    rsi_overbought: float = 65
    rsi_oversold: float = 35
    sma_fast: int = 5
    sma_slow: int = 10
    ema_fast: int = 6
    ema_slow: int = 12
    bb_period: int = 15
    bb_std: float = 2.0
    min_price_history: int = 30

    # Loop
    monitoring_interval_s: int = int(os.getenv("MOCOVE_MONITOR", 20))

    # Persistência
    save_dir: str = os.getenv("MOCOVE_SAVE_DIR", "./runtime")


# ==========================
# Logging
# ==========================

def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("ai_trading_agent.log", encoding="utf-8"),
        ],
    )


# ==========================
# Utilitários
# ==========================

TZ_UTC = timezone.utc


def utcnow() -> datetime:
    return datetime.now(tz=TZ_UTC)


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


# ==========================
# Indicadores Técnicos (NumPy)
# ==========================

class TA:
    @staticmethod
    def sma(arr: np.ndarray, period: int) -> float:
        if arr.size < period:
            return float(arr[-1]) if arr.size else 0.0
        return float(arr[-period:].mean())

    @staticmethod
    def ema(arr: np.ndarray, period: int) -> float:
        if arr.size < period:
            return float(arr[-1]) if arr.size else 0.0
        alpha = 2 / (period + 1)
        ema_val = arr[0]
        for x in arr[1:]:
            ema_val = alpha * x + (1 - alpha) * ema_val
        return float(ema_val)

    @staticmethod
    def rsi(arr: np.ndarray, period: int = 14) -> float:
        if arr.size < period + 1:
            return 50.0
        diff = np.diff(arr)
        gains = np.clip(diff, 0, None)
        losses = -np.clip(diff, None, 0)
        avg_gain = gains[-period:].mean()
        avg_loss = losses[-period:].mean()
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return float(100 - (100 / (1 + rs)))

    @staticmethod
    def bollinger(arr: np.ndarray, period: int = 20, std_mult: float = 2.0) -> Tuple[float, float, float]:
        if arr.size < period:
            x = float(arr[-1]) if arr.size else 0.0
            return x, x, x
        window = arr[-period:]
        mid = float(window.mean())
        std = float(window.std(ddof=0))
        up = mid + std_mult * std
        lo = mid - std_mult * std
        return up, mid, lo

    @staticmethod
    def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        # Fallback: quando não há OHLC, aproximamos ATR pelo desvio das últimas variações de close
        n = min(high.size, low.size, close.size)
        if n >= period + 1:
            prev_close = close[:-1]
            tr = np.maximum(high[1:] - low[1:], np.maximum(np.abs(high[1:] - prev_close), np.abs(low[1:] - prev_close)))
            return float(tr[-period:].mean())
        if close.size >= period:
            return float(np.abs(np.diff(close))[-period:].mean())
        return 0.0


# ==========================
# Modelos de Dados
# ==========================

@dataclass
class MarketState:
    symbol: str
    current_price: float
    price_history: List[float]
    volume_24h: float
    change_24h_pct: float
    volatility_pct: float
    timestamp: datetime

@dataclass
class TradingSignal:
    action: str  # 'buy' | 'sell' | 'hold'
    symbol: str
    confidence: float
    reason: str
    price: float
    amount_usd: float
    timestamp: datetime
    indicators: Dict[str, float]


# ==========================
# Cliente de Exchange / API - Versão híbrida com fallback
# ==========================

# ==========================
# Cliente de Exchange / API - Versão Robusta
# ==========================

class ExchangeClient:
    def __init__(self, api_base: str, session: aiohttp.ClientSession, test_mode: bool):
        self.api_base = api_base.rstrip("/")
        self.session = session
        self.test_mode = test_mode
        self.log = logging.getLogger("ExchangeClient")

    def _sync_get_json(self, path: str, params: Dict = None, timeout: int = 8) -> Dict:
        """Método síncrono usando requests como fallback robusto"""
        url = f"{self.api_base}{path}"
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            result = response.json()
            return result
        except Exception as e:
            self.log.warning(f"Sync GET {url} falhou: {e}")
            return {}

    def _sync_post_json(self, path: str, payload: Dict, timeout: int = 15, retries: int = 2) -> Dict:
        """Método síncrono usando requests para POST"""
        url = f"{self.api_base}{path}"
        for i in range(retries + 1):
            try:
                response = requests.post(url, json=payload, timeout=timeout)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                self.log.error(f"Sync POST {url} falhou (tentativa {i+1}/{retries+1}): {e}")
                if i < retries:
                    time.sleep(0.5 * (i + 1))
        return {}

    async def get_json(self, path: str, params: Dict = None, timeout: int = 8) -> Dict:
        # Usar método síncrono via asyncio.to_thread para máxima compatibilidade
        return await asyncio.to_thread(self._sync_get_json, path, params, timeout)

    async def post_json(self, path: str, payload: Dict, timeout: int = 15, retries: int = 2) -> Dict:
        # Usar método síncrono via asyncio.to_thread para máxima compatibilidade
        return await asyncio.to_thread(self._sync_post_json, path, payload, timeout, retries)

    async def market_data(self, symbol: str) -> Dict:
        return await self.get_json("/api/market_data", {"symbol": symbol})

    async def prices(self, symbol: str, limit: int = 60) -> List[Dict]:
        data = await self.get_json("/api/prices", {"symbol": symbol, "limit": limit})
        if isinstance(data, list):
            return data
        return data.get("prices", [])

    async def volatility(self, symbol: str) -> Dict:
        return await self.get_json("/api/volatility", {"symbol": symbol})

    async def trade(self, action: str, symbol: str, amount_usd: float) -> Dict:
        if self.test_mode:
            self.log.info(f"[TEST MODE] {action.upper()} ${amount_usd:.2f} {symbol}")
            return {"status": "test_ok", "action": action, "symbol": symbol, "amount_usd": amount_usd}
        path = "/api/trading/buy" if action == "buy" else "/api/trading/sell"
        return await self.post_json(path, {"symbol": symbol, "amount": amount_usd})


# ==========================
# Estratégia
# ==========================

class Strategy:
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        self.log = logging.getLogger("Strategy")
        self.daily_trade_count: int = 0
        self.last_trade_time: Optional[datetime] = None
        self.last_reset_day: Optional[datetime.date] = None

        # Posição simples (uma por vez)
        self.current_position: Optional[str] = None  # 'long' | None
        self.entry_price: float = 0.0
        self.position_usd: float = 0.0
        self.stop_price: Optional[float] = None
        self.take_price: Optional[float] = None
        self.trailing_stop: Optional[float] = None
        self.max_favorable_price: Optional[float] = None

        # Controle de risco agregado
        self.daily_realized_pnl: float = 0.0
        self.last_loss_time: Optional[datetime] = None

    def _reset_daily_if_needed(self):
        today = utcnow().date()
        if self.last_reset_day != today:
            self.daily_trade_count = 0
            self.daily_realized_pnl = 0.0
            self.last_reset_day = today
            self.log.info("Reset diário de contadores executado")

    # ===== Análise de entrada =====
    def analyze(self, m: MarketState) -> TradingSignal:
        self._reset_daily_if_needed()

        prices = np.array(m.price_history, dtype=float)
        price = float(m.current_price)

        sma_f = TA.sma(prices, self.cfg.sma_fast)
        sma_s = TA.sma(prices, self.cfg.sma_slow)
        ema_f = TA.ema(prices, self.cfg.ema_fast)
        ema_s = TA.ema(prices, self.cfg.ema_slow)
        rsi = TA.rsi(prices, self.cfg.rsi_period)
        bb_up, bb_mid, bb_lo = TA.bollinger(prices, self.cfg.bb_period, self.cfg.bb_std)

        # Aproximação de ATR usando closes (sem OHLC)
        atr = TA.atr(prices, prices, prices, self.cfg.atr_period)

        reasons = []
        buy_score = 0.0
        sell_score = 0.0
        total_weight = 0.0

        # 1) Crossovers
        w = 3.0
        if sma_f > sma_s and ema_f > ema_s:
            buy_score += w; reasons.append("Crossover altista")
        elif sma_f < sma_s and ema_f < ema_s:
            sell_score += w; reasons.append("Crossover baixista")
        total_weight += w

        # 2) RSI
        w = 2.0
        if rsi < self.cfg.rsi_oversold:
            buy_score += w; reasons.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > self.cfg.rsi_overbought:
            sell_score += w; reasons.append(f"RSI overbought ({rsi:.1f})")
        else:
            reasons.append(f"RSI neutro ({rsi:.1f})")
        total_weight += w

        # 3) Bandas de Bollinger – posição
        w = 2.0
        width = max(bb_up - bb_lo, 1e-12)
        bb_pos = (price - bb_lo) / width
        if bb_pos <= 0.2:
            buy_score += w; reasons.append("Preço perto da banda inferior")
        elif bb_pos >= 0.8:
            sell_score += w; reasons.append("Preço perto da banda superior")
        else:
            reasons.append(f"Preço no meio das bandas ({bb_pos:.2f})")
        total_weight += w

        # 4) Tendência curta (3 candles)
        w = 2.0
        if prices.size >= 3:
            pct = (price - prices[-3]) / prices[-3] * 100
            if pct > 0.5:
                buy_score += w; reasons.append(f"Tendência altista ({pct:.2f}%)")
            elif pct < -0.5:
                sell_score += w; reasons.append(f"Tendência baixista ({pct:.2f}%)")
            else:
                reasons.append(f"Tendência lateral ({pct:.2f}%)")
            total_weight += w

        # 5) Mudança 24h
        w = 1.0
        if m.change_24h_pct > 1:
            buy_score += w; reasons.append(f"Alta 24h ({m.change_24h_pct:.2f}%)")
        elif m.change_24h_pct < -1:
            sell_score += w; reasons.append(f"Queda 24h ({m.change_24h_pct:.2f}%)")
        total_weight += w

        # Resultado
        if buy_score > sell_score:
            action = "buy"
            conf = buy_score / max(total_weight, 1e-9)
        elif sell_score > buy_score:
            action = "sell"
            conf = sell_score / max(total_weight, 1e-9)
        else:
            action = "hold"
            conf = 0.5

        # Ajuste por volatilidade e cooldown
        if m.volatility_pct > self.cfg.volatility_threshold:
            conf *= 0.8
            reasons.append(f"Alta volatilidade ({m.volatility_pct:.2f}%) – reduzindo confiança")
        if self.last_loss_time and (utcnow() - self.last_loss_time).total_seconds() < self.cfg.cooldown_after_loss_s:
            conf *= 0.85
            reasons.append("Cooldown pós-perda ativo – confiança reduzida")

        # ===== Sizing por risco
        amount_usd = 0.0
        stop_distance = max(atr * self.cfg.sl_atr_mult if self.cfg.use_atr_sl_tp else price * 0.015, 1e-12)
        if action == "buy" and conf >= self.cfg.min_confidence:
            # posição alvo tal que perda no stop ≈ risk_per_trade_usd
            qty = self.cfg.risk_per_trade_usd / stop_distance  # qty em 'moeda da cripto' via USD/stop
            amount_usd = min(qty * price, self.cfg.max_position_usd)
            # ajuste por volatilidade
            if m.volatility_pct > self.cfg.volatility_threshold:
                amount_usd *= 0.7

        indicators = {
            "sma_fast": sma_f, "sma_slow": sma_s,
            "ema_fast": ema_f, "ema_slow": ema_s,
            "rsi": rsi,
            "bb_up": bb_up, "bb_mid": bb_mid, "bb_lo": bb_lo,
            "bb_pos": bb_pos,
            "volatility_pct": m.volatility_pct,
            "change_24h_pct": m.change_24h_pct,
            "current_price": price,
            "atr": atr,
            "stop_distance": stop_distance,
        }

        return TradingSignal(
            action=action,
            symbol=m.symbol,
            confidence=float(conf),
            reason="; ".join(reasons),
            price=price,
            amount_usd=float(amount_usd) if amount_usd > 0 else 0.0,
            timestamp=utcnow(),
            indicators=indicators,
        )

    # ===== Regras para executar entrada =====
    def should_execute(self, sig: TradingSignal) -> bool:
        now = utcnow()
        if sig.confidence < self.cfg.min_confidence:
            logging.debug(f"Confiança insuficiente: {sig.confidence:.3f} < {self.cfg.min_confidence}")
            return False
        if self.daily_trade_count >= self.cfg.max_daily_trades:
            logging.info(f"Limite diário de trades atingido: {self.daily_trade_count}")
            return False
        if self.last_trade_time and (now - self.last_trade_time).total_seconds() < self.cfg.min_trade_interval_s:
            logging.debug("Intervalo mínimo entre trades não atingido")
            return False
        if sig.action != "buy":
            return False
        return True

    # ===== Definição de OCO (SL/TP) na entrada =====
    def set_oco_levels(self, entry_price: float, atr: float):
        # Stop por ATR ou percentual
        if self.cfg.use_atr_sl_tp and atr > 0:
            stop_dist = self.cfg.sl_atr_mult * atr
        else:
            stop_dist = max(entry_price * 0.015, 1e-12)
        self.stop_price = max(entry_price - stop_dist, 0.0)

        # Take baseado em R:R
        take_dist = self.cfg.tp_rr * (entry_price - self.stop_price)
        self.take_price = entry_price + take_dist

        # Zera trailing no início
        self.trailing_stop = None
        self.max_favorable_price = entry_price

    # ===== Lógica de saída (SL/TP/Trailing) =====
    def check_exit_signal(self, current_price: float, atr: float) -> Optional[str]:
        if self.current_position != "long":
            return None
        if self.stop_price is None or self.take_price is None:
            return None

        # Atualiza máxima a favor
        if self.max_favorable_price is None or current_price > self.max_favorable_price:
            self.max_favorable_price = current_price

        # Ativa/atualiza trailing se configurado e lucro >= ativação
        if self.cfg.use_trailing_stop and self.max_favorable_price and self.stop_price:
            risk = (self.entry_price - self.stop_price)
            if risk > 0 and (self.max_favorable_price - self.entry_price) >= self.cfg.trail_activation_rr * risk:
                trail_dist = (self.cfg.trail_atr_mult * atr) if (self.cfg.use_atr_sl_tp and atr > 0) else max(self.entry_price * 0.01, 1e-12)
                new_trail = self.max_favorable_price - trail_dist
                # trailing nunca desce
                if self.trailing_stop is None or new_trail > self.trailing_stop:
                    self.trailing_stop = new_trail

        # Regra de OCO: se tocar um, sai
        effective_stop = self.trailing_stop if self.trailing_stop is not None else self.stop_price
        if current_price <= effective_stop:
            return "stop"
        if current_price >= self.take_price:
            return "take"
        return None

    # ===== Registro de execução =====
    def register_execution(self, action: str, exec_price: float, pnl_realized: float):
        self.last_trade_time = utcnow()
        if action == "buy":
            self.daily_trade_count += 1
            self.current_position = "long"
            self.entry_price = exec_price
            # posição em USD definida externamente (no agente)
        elif action == "sell" and self.current_position == "long":
            self.current_position = None
            self.entry_price = 0.0
            self.position_usd = 0.0
            self.stop_price = None
            self.take_price = None
            self.trailing_stop = None
            self.max_favorable_price = None
            self.daily_realized_pnl += pnl_realized
            if pnl_realized < 0:
                self.last_loss_time = utcnow()


# ==========================
# Agente
# ==========================

class TradingAgent:
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        self.strategy = Strategy(cfg)
        self.is_running = False
        self.total_trades = 0
        self.profitable_trades = 0
        self.total_profit_usd = 0.0
        self.signal_history: List[TradingSignal] = []
        self.trade_history: List[Dict] = []
        ensure_dir(self.cfg.save_dir)
        self.log = logging.getLogger("Agent")

    async def _build_market_state(self, client: ExchangeClient, symbol: str) -> Optional[MarketState]:
        """Constrói estado de mercado de forma robusta"""
        try:
            # Obter dados de mercado
            md = await client.market_data(symbol)
            if not md:
                self.log.warning("Dados de mercado vazios")
                return None
            
            price = float(md.get("price", 0.0))
            vol = float(md.get("volume", 0.0))
            chg = float(md.get("change_24h", 0.0))

            # Obter histórico de preços
            prices = await client.prices(symbol, limit=max(self.cfg.min_price_history, 120))
            price_hist = []
            if prices:
                price_hist = [float(p.get("price")) for p in prices if p.get("price") is not None]

            # Fallback: gerar histórico simulado se necessário
            if len(price_hist) < self.cfg.min_price_history:
                if price <= 0:
                    self.log.warning("Preço inválido e sem histórico")
                    return None
                # Criar série simulada simples
                price_hist = [price * (1 + 0.001 * i) for i in range(-self.cfg.min_price_history, 0)]
                self.log.info(f"Histórico simulado criado: {len(price_hist)} pontos")

            # Obter volatilidade
            vol_resp = await client.volatility(symbol)
            vol_pct = float(vol_resp.get("volatility", 2.0)) if vol_resp else 2.0

            return MarketState(
                symbol=symbol,
                current_price=price if price > 0 else float(price_hist[-1]),
                price_history=price_hist,
                volume_24h=vol,
                change_24h_pct=chg,
                volatility_pct=vol_pct,
                timestamp=utcnow(),
            )
            
        except Exception as e:
            self.log.error(f"Erro ao construir market state: {e}")
            return None

    def _fees_for(self, notional_usd: float, sides: int = 1) -> float:
        # taxa aproximada por lado
        return notional_usd * self.cfg.maker_taker_fee_pct * sides

    def _calc_pnl(self, side: str, exec_price: float) -> float:
        # PnL realizado somente quando vendemos a posição long
        if side == "sell" and self.strategy.entry_price > 0 and self.strategy.position_usd > 0:
            qty = self.strategy.position_usd / self.strategy.entry_price
            gross = (exec_price - self.strategy.entry_price) * qty
            # taxas de entrada + saída
            fees = self._fees_for(self.strategy.position_usd, sides=2)
            return float(gross - fees)
        return 0.0

    def _persist(self):
        # salva JSONs simples para auditoria rápida
        with open(os.path.join(self.cfg.save_dir, "signals.jsonl"), "a", encoding="utf-8") as f:
            for s in self.signal_history:
                f.write(json.dumps({**asdict(s), "timestamp": s.timestamp.isoformat()}) + '\n')
        self.signal_history.clear()

        with open(os.path.join(self.cfg.save_dir, "trades.jsonl"), "a", encoding="utf-8") as f:
            for t in self.trade_history:
                t2 = dict(t)
                if isinstance(t2.get("timestamp"), datetime):
                    t2["timestamp"] = t2["timestamp"].isoformat()
                f.write(json.dumps(t2) + '\n')
        self.trade_history.clear()

    def _should_halt_for_daily_loss(self) -> bool:
        if self.strategy.daily_realized_pnl <= -abs(self.cfg.daily_loss_limit_usd):
            self.log.warning("Limite de perda diária atingido – suspendendo entradas")
            return True
        return False

    async def _maybe_exit_position(self, client: ExchangeClient, ms: MarketState):
        if self.strategy.current_position != "long":
            return
        # usa ATR aproximado dos closes
        prices = np.array(ms.price_history, dtype=float)
        atr = TA.atr(prices, prices, prices, self.cfg.atr_period)
        exit_reason = self.strategy.check_exit_signal(ms.current_price, atr)
        if exit_reason:
            # monta sinal sintético de saída
            sig = TradingSignal(
                action="sell",
                symbol=ms.symbol,
                confidence=1.0,
                reason=f"Saída por {exit_reason.upper()} (OCO/Trailing)",
                price=ms.current_price,
                amount_usd=self.strategy.position_usd,
                timestamp=utcnow(),
                indicators={"atr": atr, "exit_reason": exit_reason},
            )
            self.signal_history.append(sig)
            self.log.info(f"EXIT: {exit_reason.upper()} @ {sig.price:.8f} amt=${sig.amount_usd:.2f}")
            result = await client.trade("sell", sig.symbol, sig.amount_usd)
            if result:
                pnl = self._calc_pnl("sell", sig.price)
                self.total_profit_usd += pnl
                if pnl > 0:
                    self.profitable_trades += 1
                self.trade_history.append({
                    "timestamp": sig.timestamp,
                    "action": sig.action,
                    "symbol": sig.symbol,
                    "price": sig.price,
                    "amount_usd": sig.amount_usd,
                    "confidence": sig.confidence,
                    "reason": sig.reason,
                    "api_result": result,
                    "pnl": pnl,
                })
                self.strategy.register_execution("sell", sig.price, pnl)

    async def run_once(self, client: ExchangeClient):
        """Executa um ciclo completo de análise e trading"""
        try:
            # 1. Construir estado de mercado
            ms = await self._build_market_state(client, self.cfg.default_symbol)
            if not ms:
                self.log.warning("Sem dados de mercado válidos para análise")
                return

            # 2. Gerenciar saídas (SL/TP/Trailing)
            await self._maybe_exit_position(client, ms)

            # 3. Gerar sinal de trading
            if model is not None:
                # Usar modelo AutoML se disponível
                sig = self._generate_ml_signal(ms)
            else:
                # Usar estratégia tradicional
                sig = self.strategy.analyze(ms)
            
            self.signal_history.append(sig)
            self.log.info(f"Sinal: {sig.action.upper()} | Confiança: {sig.confidence:.2f} | {sig.reason}")

            # 4. Verificar limites de risco
            if self._should_halt_for_daily_loss():
                return

            # 5. Executar trades se aplicável
            await self._execute_signal(client, sig)

            # 6. Persistir dados
            self._persist()
            
        except Exception as e:
            self.log.error(f"Erro em run_once: {e}", exc_info=True)
            # Não re-levantar exceção para manter agente rodando

    def _generate_ml_signal(self, ms: MarketState) -> TradingSignal:
        """Gera sinal usando modelo AutoML"""
        try:
            features = [
                ms.current_price,
                TA.sma(np.array(ms.price_history), 9),
                TA.sma(np.array(ms.price_history), 21),
                TA.sma(np.array(ms.price_history), 50),
                TA.ema(np.array(ms.price_history), 12),
                TA.ema(np.array(ms.price_history), 26),
                TA.rsi(np.array(ms.price_history), 14),
                # bb_pos
                (ms.current_price - TA.bollinger(np.array(ms.price_history), 21, 2.0)[2]) /
                    (TA.bollinger(np.array(ms.price_history), 21, 2.0)[0] - TA.bollinger(np.array(ms.price_history), 21, 2.0)[2] + 1e-9),
                # macd
                TA.ema(np.array(ms.price_history), 12) - TA.ema(np.array(ms.price_history), 26),
                # macd_signal
                TA.ema(np.array(ms.price_history), 9),
                # volatilidade
                np.std(np.diff(np.array(ms.price_history)[-20:])),
                # atr
                TA.atr(np.array(ms.price_history), np.array(ms.price_history), np.array(ms.price_history), 14),
                # volume_z (não disponível, usar 0)
                0.0,
                # min24, max24, var24
                np.min(np.array(ms.price_history)[-24:]),
                np.max(np.array(ms.price_history)[-24:]),
                (ms.current_price - np.array(ms.price_history)[-24]) / (np.array(ms.price_history)[-24] + 1e-9) if len(ms.price_history) >= 24 else 0.0
            ]
            
            X = np.array(features).reshape(1, -1)
            if scaler is not None:
                X = scaler.transform(X)
            
            proba = model.predict_proba(X)[0]
            classes = list(model.classes_)
            idx_buy = classes.index(1) if 1 in classes else None
            idx_sell = classes.index(-1) if -1 in classes else None
            
            pb = THRESHOLDS.get('buy_p', 0.5)
            ps = THRESHOLDS.get('sell_p', 0.5)
            
            is_buy = proba[idx_buy] >= pb if idx_buy is not None else False
            is_sell = proba[idx_sell] >= ps if idx_sell is not None else False
            
            # Resolver conflitos
            action = 'hold'
            if is_buy and is_sell:
                action = 'buy' if proba[idx_buy] >= proba[idx_sell] else 'sell'
            elif is_buy:
                action = 'buy'
            elif is_sell:
                action = 'sell'
            
            conf = max(proba[idx_buy] if idx_buy is not None else 0, proba[idx_sell] if idx_sell is not None else 0)
            reason = f"AutoML: proba_buy={proba[idx_buy]:.2f}, proba_sell={proba[idx_sell]:.2f}"
            amount_usd = self.cfg.risk_per_trade_usd if action != 'hold' else 0.0
            
            return TradingSignal(
                action=action,
                symbol=ms.symbol,
                confidence=conf,
                reason=reason,
                price=ms.current_price,
                amount_usd=amount_usd,
                timestamp=utcnow(),
                indicators={},
            )
        except Exception as e:
            self.log.error(f"Erro no modelo AutoML: {e}")
            # Fallback para estratégia tradicional
            return self.strategy.analyze(ms)

    async def _execute_signal(self, client: ExchangeClient, sig: TradingSignal):
        """Executa sinal de trading"""
        executed = False
        result = {}
        
        if sig.action == "buy" and self.strategy.should_execute(sig):
            atr = float(sig.indicators.get("atr", 0.0)) if sig.indicators else 0.0
            self.strategy.set_oco_levels(sig.price, atr)
            self.strategy.position_usd = sig.amount_usd
            
            self.log.info(f"EXECUTANDO BUY: {sig.symbol} | Preço: {sig.price:.8f} | Valor: ${sig.amount_usd:.2f}")
            result = await client.trade("buy", sig.symbol, sig.amount_usd)
            executed = bool(result)
            
            if executed:
                self.total_trades += 1
                self.trade_history.append({
                    "timestamp": sig.timestamp,
                    "action": "buy",
                    "symbol": sig.symbol,
                    "price": sig.price,
                    "amount_usd": sig.amount_usd,
                    "confidence": sig.confidence,
                    "reason": sig.reason,
                    "api_result": result,
                    "sl": self.strategy.stop_price,
                    "tp": self.strategy.take_price,
                })
                self.strategy.register_execution("buy", sig.price, 0.0)
                
        elif sig.action == "sell" and self.strategy.current_position == "long":
            self.log.info(f"EXECUTANDO SELL: {sig.symbol} | Preço: {sig.price:.8f} | Valor: ${self.strategy.position_usd:.2f}")
            result = await client.trade("sell", sig.symbol, self.strategy.position_usd)
            
            if result:
                pnl = self._calc_pnl("sell", sig.price)
                self.total_profit_usd += pnl
                if pnl > 0:
                    self.profitable_trades += 1
                    
                self.trade_history.append({
                    "timestamp": sig.timestamp,
                    "action": "sell",
                    "symbol": sig.symbol,
                    "price": sig.price,
                    "amount_usd": self.strategy.position_usd,
                    "confidence": sig.confidence,
                    "reason": sig.reason,
                    "api_result": result,
                    "pnl": pnl,
                })
                self.strategy.register_execution("sell", sig.price, pnl)

        # 1) Primeiro, gerenciar saídas (SL/TP/Trailing)
        await self._maybe_exit_position(client, ms)

        # 2) Avaliar entradas
        # ======== INTEGRAÇÃO COM MODELO AUTO-ML ========
        if model is not None:
            # Monta features para predição
            features = [
                ms.current_price,
                TA.sma(np.array(ms.price_history), 9),
                TA.sma(np.array(ms.price_history), 21),
                TA.sma(np.array(ms.price_history), 50),
                TA.ema(np.array(ms.price_history), 12),
                TA.ema(np.array(ms.price_history), 26),
                TA.rsi(np.array(ms.price_history), 14),
                # bb_pos
                (ms.current_price - TA.bollinger(np.array(ms.price_history), 21, 2.0)[2]) /
                    (TA.bollinger(np.array(ms.price_history), 21, 2.0)[0] - TA.bollinger(np.array(ms.price_history), 21, 2.0)[2] + 1e-9),
                # macd
                TA.ema(np.array(ms.price_history), 12) - TA.ema(np.array(ms.price_history), 26),
                # macd_signal
                TA.ema(np.array(ms.price_history), 9),
                # volatilidade
                np.std(np.diff(np.array(ms.price_history)[-20:])),
                # atr
                TA.atr(np.array(ms.price_history), np.array(ms.price_history), np.array(ms.price_history), 14),
                # volume_z (não disponível, usar 0)
                0.0,
                # min24, max24, var24
                np.min(np.array(ms.price_history)[-24:]),
                np.max(np.array(ms.price_history)[-24:]),
                (ms.current_price - np.array(ms.price_history)[-24]) / (np.array(ms.price_history)[-24] + 1e-9) if len(ms.price_history) >= 24 else 0.0
            ]
            X = np.array(features).reshape(1, -1)
            if scaler is not None:
                X = scaler.transform(X)
            proba = model.predict_proba(X)[0]
            classes = list(model.classes_)
            idx_buy = classes.index(1) if 1 in classes else None
            idx_sell = classes.index(-1) if -1 in classes else None
            pb = THRESHOLDS.get('buy_p', 0.5)
            ps = THRESHOLDS.get('sell_p', 0.5)
            is_buy = proba[idx_buy] >= pb if idx_buy is not None else False
            is_sell = proba[idx_sell] >= ps if idx_sell is not None else False
            # Resolver conflitos
            action = 'hold'
            if is_buy and is_sell:
                action = 'buy' if proba[idx_buy] >= proba[idx_sell] else 'sell'
            elif is_buy:
                action = 'buy'
            elif is_sell:
                action = 'sell'
            conf = max(proba[idx_buy] if idx_buy is not None else 0, proba[idx_sell] if idx_sell is not None else 0)
            reason = f"AutoML: proba_buy={proba[idx_buy]:.2f}, proba_sell={proba[idx_sell]:.2f}"
            # amount_usd: sizing padrão
            amount_usd = self.cfg.risk_per_trade_usd if action != 'hold' else 0.0
            sig = TradingSignal(
                action=action,
                symbol=ms.symbol,
                confidence=conf,
                reason=reason,
                price=ms.current_price,
                amount_usd=amount_usd,
                timestamp=utcnow(),
                indicators={},
            )
        else:
            # fallback: lógica tradicional
            sig = self.strategy.analyze(ms)
        self.signal_history.append(sig)

        if self._should_halt_for_daily_loss():
            return

        executed = False
        result = {}
        if sig.action == "buy" and self.strategy.should_execute(sig):
            atr = float(sig.indicators.get("atr", 0.0)) if sig.indicators else 0.0
            self.strategy.set_oco_levels(sig.price, atr)
            self.strategy.position_usd = sig.amount_usd
            self.log.info(f"ENTER: BUY {sig.symbol} | px={sig.price:.8f} conf={sig.confidence:.2f} amt=${sig.amount_usd:.2f} SL={self.strategy.stop_price:.8f} TP={self.strategy.take_price:.8f}")
            result = await client.trade("buy", sig.symbol, sig.amount_usd)
            executed = True if result else False
            if executed:
                self.total_trades += 1
                self.trade_history.append({
                    "timestamp": sig.timestamp,
                    "action": "buy",
                    "symbol": sig.symbol,
                    "price": sig.price,
                    "amount_usd": sig.amount_usd,
                    "confidence": sig.confidence,
                    "reason": sig.reason,
                    "api_result": result,
                    "sl": self.strategy.stop_price,
                    "tp": self.strategy.take_price,
                })
                self.strategy.register_execution("buy", sig.price, 0.0)
        elif sig.action == "sell" and self.strategy.current_position == "long":
            # Executa venda automática se modelo indicar SELL
            self.log.info(f"EXIT: SELL {sig.symbol} | px={sig.price:.8f} conf={sig.confidence:.2f} amt=${self.strategy.position_usd:.2f}")
            result = await client.trade("sell", sig.symbol, self.strategy.position_usd)
            if result:
                pnl = self._calc_pnl("sell", sig.price)
                self.total_profit_usd += pnl
                if pnl > 0:
                    self.profitable_trades += 1
                self.trade_history.append({
                    "timestamp": sig.timestamp,
                    "action": "sell",
                    "symbol": sig.symbol,
                    "price": sig.price,
                    "amount_usd": self.strategy.position_usd,
                    "confidence": sig.confidence,
                    "reason": sig.reason,
                    "api_result": result,
                    "pnl": pnl,
                })
                self.strategy.register_execution("sell", sig.price, pnl)

        # Logs úteis
        ind = sig.indicators
        self.log.debug(
            f"RSI={ind.get('rsi', 0):.1f} VOL={ind.get('volatility_pct', 0):.2f}% BBpos={ind.get('bb_pos', 0):.2f} ATR={ind.get('atr',0):.6f}"
        )

        # Persistência periódica
        self._persist()

    async def run(self):
        """Loop principal do agente de trading"""
        self.is_running = True
        self.log.info("=== AGENTE IA TRADING INICIADO ===")
        
        try:
            # Configuração robusta do aiohttp
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                client = ExchangeClient(self.cfg.api_base, session, self.cfg.test_mode)
                self.log.info(f"Configuração: {self.cfg.default_symbol} | Intervalo: {self.cfg.monitoring_interval_s}s | Modo: {'TESTE' if self.cfg.test_mode else 'REAL'}")
                
                cycle_count = 0
                while self.is_running:
                    cycle_count += 1
                    self.log.info(f"=== CICLO {cycle_count} ===")
                    
                    try:
                        await self.run_once(client)
                        self.log.info(f"Ciclo {cycle_count} completado com sucesso")
                        
                        # Status resumido a cada 10 ciclos
                        if cycle_count % 10 == 0:
                            self.log.info(f"Status: {cycle_count} ciclos | {self.total_trades} trades | PnL: ${self.total_profit_usd:.2f}")
                        
                    except Exception as e:
                        self.log.error(f"Erro no ciclo {cycle_count}: {e}")
                        # Continuar rodando mesmo com erro
                    
                    # Aguardar próximo ciclo
                    await asyncio.sleep(self.cfg.monitoring_interval_s)
                    
        except Exception as e:
            self.log.error(f"Erro crítico no agente: {e}", exc_info=True)
        finally:
            self.log.info("Finalizando agente...")
            self._persist()
            self.print_status()

    def stop(self):
        self.is_running = False

    def print_status(self):
        win_rate = (self.profitable_trades / self.total_trades * 100) if self.total_trades else 0.0
        lines = [
            '\n' + '=' * 60,
            'AI TRADING AGENT – STATUS',
            '=' * 60,
            f"Trades: {self.total_trades} | Win%: {win_rate:.1f}% | PnL: ${self.total_profit_usd:.2f}",
            f"Posição: {self.strategy.current_position or 'Nenhuma'}",
            f"Perda diária: ${self.strategy.daily_realized_pnl:.2f} / limite ${-abs(self.cfg.daily_loss_limit_usd):.2f}",
        ]
        if self.strategy.current_position:
            lines += [
                f"Entrada: ${self.strategy.entry_price:.8f}",
                f"Valor: ${self.strategy.position_usd:.2f}",
                f"SL: ${self.strategy.stop_price:.8f} | TP: ${self.strategy.take_price:.8f}",
                f"Trailing: ${self.strategy.trailing_stop:.8f}" if self.strategy.trailing_stop else "Trailing: inativo",
            ]
        lines.append(f"Trades hoje: {self.strategy.daily_trade_count}/{self.cfg.max_daily_trades}")
        print("\n".join(lines))


# ==========================
# Execução
# ==========================

async def main():
    """Função principal do sistema"""
    cfg = Settings()
    setup_logging(cfg.verbose_logging)
    agent = TradingAgent(cfg)
    
    logging.info("=== SISTEMA DE TRADING IA INICIANDO ===")
    
    # Criar task do agente
    agent_task = asyncio.create_task(agent.run())
    
    try:
        # Loop de monitoramento
        while agent.is_running:
            # Verificar se task ainda está rodando
            if agent_task.done():
                logging.error("Task do agente terminou inesperadamente!")
                exception = agent_task.exception()
                if exception:
                    logging.error(f"Exceção: {exception}")
                break
            
            await asyncio.sleep(5)  # Verifica a cada 5 segundos
            
    except KeyboardInterrupt:
        logging.info("Interrupção pelo usuário")
        agent.stop()
        agent_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await agent_task
    except Exception as e:
        logging.error(f"Erro no main: {e}", exc_info=True)
        agent.stop()
    
    logging.info("=== SISTEMA ENCERRADO ===")


if __name__ == "__main__":
    print("=== INICIANDO AGENTE IA TRADING ===")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Agente interrompido pelo usuário")
    except Exception as e:
        print(f"Erro crítico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("=== AGENTE FINALIZADO ===")
