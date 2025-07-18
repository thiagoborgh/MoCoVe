from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Literal

import numpy as np
import joblib
import os

# Carregar modelo treinado
MODEL_PATH = os.environ.get('MODEL_PATH', 'memecoin_rf_model.pkl')
clf = None
if os.path.exists(MODEL_PATH):
    clf = joblib.load(MODEL_PATH)
    print(f"Modelo carregado de {MODEL_PATH}")
else:
    print("AVISO: Modelo não encontrado, usando lógica dummy.")

app = FastAPI()

class Features(BaseModel):
    price: float
    sma9: float
    sma21: float
    sma50: float
    rsi: float
    min24h: float
    max24h: float
    var24h: float
    volume: float = 0.0
    sentiment: float = 0.5
    # Adicione outros campos conforme necessário

class Prediction(BaseModel):
    decision: Literal['BUY', 'SELL', 'HOLD']
    probability: float
    # Outros campos opcionais


@app.post('/predict', response_model=Prediction)
async def predict(features: Features):
    x = np.array([
        features.price, features.sma9, features.sma21, features.sma50,
        features.rsi, features.min24h, features.max24h, features.var24h,
        features.volume, features.sentiment
    ]).reshape(1, -1)
    if clf:
        pred = clf.predict(x)[0]
        proba = max(clf.predict_proba(x)[0]) if hasattr(clf, 'predict_proba') else 0.8
        if pred == 1:
            return {"decision": "BUY", "probability": float(proba)}
        elif pred == -1:
            return {"decision": "SELL", "probability": float(proba)}
        else:
            return {"decision": "HOLD", "probability": float(proba)}
    # fallback dummy
    if features.rsi < 30 or (features.sma9 and features.sma21 and features.sma9 > features.sma21):
        return {"decision": "BUY", "probability": 0.85}
    elif features.rsi > 70 or (features.sma9 and features.sma21 and features.sma9 < features.sma21):
        return {"decision": "SELL", "probability": 0.85}
    else:
        return {"decision": "HOLD", "probability": 0.5}

# Para rodar: uvicorn ai_model:app --reload --host 0.0.0.0 --port 5000
