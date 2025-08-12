"""
MoCoVe AI Model - Serviço de Predição Inteligente
FastAPI service para predições de trading baseadas em ML
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal, Optional
import numpy as np
import joblib
import os
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar modelo treinado
MODEL_PATH = os.environ.get('MODEL_PATH', 'memecoin_rf_model.pkl')
clf = None

def load_model():
    global clf
    if os.path.exists(MODEL_PATH):
        try:
            clf = joblib.load(MODEL_PATH)
            logger.info(f"Modelo carregado de {MODEL_PATH}")
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            return False
    else:
        logger.warning("AVISO: Modelo não encontrado, usando lógica baseada em regras.")
        return False

# Inicializar FastAPI
app = FastAPI(
    title="MoCoVe AI Model",
    description="Serviço de predição inteligente para trading de memecoins",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carregar modelo na inicialização
load_model()

class Features(BaseModel):
    """Modelo de dados para features de entrada"""
    price: float
    sma9: Optional[float] = None
    sma21: Optional[float] = None
    sma50: Optional[float] = None
    rsi: Optional[float] = 50.0
    min24h: Optional[float] = None
    max24h: Optional[float] = None
    var24h: float = 0.0
    volume: float = 0.0
    sentiment: float = 0.5
    
    class Config:
        schema_extra = {
            "example": {
                "price": 0.08,
                "sma9": 0.079,
                "sma21": 0.078,
                "sma50": 0.077,
                "rsi": 65.0,
                "min24h": 0.075,
                "max24h": 0.082,
                "var24h": 0.025,
                "volume": 1000000,
                "sentiment": 0.7
            }
        }

class Prediction(BaseModel):
    """Modelo de dados para predições"""
    decision: Literal['BUY', 'SELL', 'HOLD']
    probability: float
    confidence: float
    reasoning: str
    
    class Config:
        schema_extra = {
            "example": {
                "decision": "BUY",
                "probability": 0.85,
                "confidence": 0.92,
                "reasoning": "RSI baixo e tendência de alta confirmada"
            }
        }


def calculate_technical_indicators(features: Features) -> dict:
    """Calcula indicadores técnicos adicionais"""
    indicators = {}
    
    # Bollinger Bands (simplificado)
    if features.sma21 and features.price:
        volatility = abs(features.var24h) if features.var24h else 0.02
        upper_band = features.sma21 * (1 + volatility * 2)
        lower_band = features.sma21 * (1 - volatility * 2)
        
        indicators['bb_upper'] = upper_band
        indicators['bb_lower'] = lower_band
        indicators['bb_position'] = (features.price - lower_band) / (upper_band - lower_band) if upper_band != lower_band else 0.5
    
    # MACD (simplificado)
    if features.sma9 and features.sma21:
        indicators['macd'] = features.sma9 - features.sma21
        indicators['macd_signal'] = 1 if indicators['macd'] > 0 else -1
    
    # Volume analysis
    indicators['volume_strength'] = min(features.volume / 1000000, 5.0)  # Normalizado
    
    return indicators

def rule_based_decision(features: Features) -> Prediction:
    """Sistema de decisão baseado em regras quando não há modelo ML"""
    
    indicators = calculate_technical_indicators(features)
    score = 0
    reasons = []
    
    # Análise RSI
    if features.rsi < 30:
        score += 2
        reasons.append("RSI oversold (<30)")
    elif features.rsi > 70:
        score -= 2
        reasons.append("RSI overbought (>70)")
    elif 30 <= features.rsi <= 45:
        score += 1
        reasons.append("RSI favorável para compra")
    elif 55 <= features.rsi <= 70:
        score -= 1
        reasons.append("RSI sugerindo possível venda")
    
    # Análise de médias móveis
    if features.sma9 and features.sma21 and features.sma50:
        if features.sma9 > features.sma21 > features.sma50:
            score += 2
            reasons.append("Tendência de alta confirmada (SMAs)")
        elif features.sma9 < features.sma21 < features.sma50:
            score -= 2
            reasons.append("Tendência de baixa confirmada (SMAs)")
        elif features.sma9 > features.sma21:
            score += 1
            reasons.append("Sinal de alta de curto prazo")
        elif features.sma9 < features.sma21:
            score -= 1
            reasons.append("Sinal de baixa de curto prazo")
    
    # Análise de volatilidade
    if abs(features.var24h) > 0.1:  # Alta volatilidade (>10%)
        if features.var24h > 0:
            score += 1
            reasons.append("Alta volatilidade positiva")
        else:
            score -= 1
            reasons.append("Alta volatilidade negativa")
    
    # Análise de sentimento
    if features.sentiment > 0.7:
        score += 1
        reasons.append("Sentimento muito positivo")
    elif features.sentiment < 0.3:
        score -= 1
        reasons.append("Sentimento muito negativo")
    
    # Análise Bollinger Bands
    if 'bb_position' in indicators:
        if indicators['bb_position'] < 0.2:
            score += 1
            reasons.append("Preço próximo à banda inferior (oversold)")
        elif indicators['bb_position'] > 0.8:
            score -= 1
            reasons.append("Preço próximo à banda superior (overbought)")
    
    # Análise de volume
    if indicators.get('volume_strength', 0) > 2:
        score += 0.5
        reasons.append("Volume acima da média")
    
    # Decisão final
    reasoning = "; ".join(reasons) if reasons else "Análise técnica neutra"
    
    if score >= 2:
        return Prediction(
            decision="BUY", 
            probability=min(0.6 + (score * 0.1), 0.95),
            confidence=min(0.7 + (score * 0.05), 0.9),
            reasoning=f"Sinal de COMPRA: {reasoning}"
        )
    elif score <= -2:
        return Prediction(
            decision="SELL", 
            probability=min(0.6 + (abs(score) * 0.1), 0.95),
            confidence=min(0.7 + (abs(score) * 0.05), 0.9),
            reasoning=f"Sinal de VENDA: {reasoning}"
        )
    else:
        return Prediction(
            decision="HOLD", 
            probability=0.5,
            confidence=0.6,
            reasoning=f"Sinal NEUTRO: {reasoning}"
        )

@app.get("/")
async def root():
    """Endpoint raiz com informações do serviço"""
    return {
        "service": "MoCoVe AI Model",
        "version": "1.0.0",
        "status": "online",
        "model_loaded": clf is not None,
        "model_path": MODEL_PATH
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_available": clf is not None,
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.post('/predict', response_model=Prediction)
async def predict(features: Features):
    """Endpoint principal para predições de trading"""
    try:
        # Validação básica
        if features.price <= 0:
            raise HTTPException(status_code=400, detail="Preço deve ser maior que zero")
        
        if clf is not None:
            # Preparar features para o modelo ML
            feature_array = np.array([
                features.price,
                features.sma9 or features.price,
                features.sma21 or features.price,
                features.sma50 or features.price,
                features.rsi,
                features.min24h or features.price * 0.95,
                features.max24h or features.price * 1.05,
                features.var24h,
                features.sentiment
            ]).reshape(1, -1)
            
            # Fazer predição
            prediction = clf.predict(feature_array)[0]
            
            # Obter probabilidades se disponível
            if hasattr(clf, 'predict_proba'):
                probabilities = clf.predict_proba(feature_array)[0]
                probability = float(np.max(probabilities))
                confidence = float(probability)
            else:
                probability = 0.8
                confidence = 0.75
            
            # Mapear predição para decisão
            decision_map = {1: "BUY", -1: "SELL", 0: "HOLD"}
            decision = decision_map.get(prediction, "HOLD")
            
            # Gerar explicação
            if decision == "BUY":
                reasoning = f"Modelo ML prevê tendência de alta (confiança: {confidence:.2f})"
            elif decision == "SELL":
                reasoning = f"Modelo ML prevê tendência de baixa (confiança: {confidence:.2f})"
            else:
                reasoning = f"Modelo ML sugere manter posição (confiança: {confidence:.2f})"
            
            return Prediction(
                decision=decision,
                probability=probability,
                confidence=confidence,
                reasoning=reasoning
            )
        
        else:
            # Fallback para sistema baseado em regras
            logger.info("Usando sistema baseado em regras (modelo ML não disponível)")
            return rule_based_decision(features)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na predição: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post('/reload_model')
async def reload_model():
    """Recarrega o modelo ML"""
    try:
        success = load_model()
        if success:
            return {"message": "Modelo recarregado com sucesso", "model_loaded": True}
        else:
            return {"message": "Falha ao recarregar modelo", "model_loaded": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recarregar modelo: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
