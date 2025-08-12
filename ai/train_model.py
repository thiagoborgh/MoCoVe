"""
MoCoVe Model Training - Treinamento de Modelo de Machine Learning
Script para treinar modelos de predição para trading de memecoins
"""

import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from datetime import datetime
import os

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações
DB_PATH = os.getenv('DB_PATH', '../memecoin.db')
MODEL_PATH = os.getenv('MODEL_PATH', 'memecoin_rf_model.pkl')
SCALER_PATH = os.getenv('SCALER_PATH', 'memecoin_scaler.pkl')
FUTURE_WINDOW = 15  # minutos à frente para calcular variação
BUY_THRESHOLD = 0.02   # 2% para BUY
SELL_THRESHOLD = -0.02 # -2% para SELL

def extract_data_from_db():
    """Extrai dados do SQLite e prepara DataFrame"""
    try:
        logger.info("Extraindo dados do banco de dados...")
        conn = sqlite3.connect(DB_PATH)
        
        # Query melhorada para extrair dados
        query = '''
        SELECT 
            symbol as coin_id,
            timestamp,
            price,
            volume
        FROM prices 
        WHERE price > 0
        ORDER BY symbol, timestamp
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            raise ValueError("Nenhum dado encontrado no banco de dados")
        
        logger.info(f"Dados extraídos: {len(df)} registros, {df['coin_id'].nunique()} moedas")
        return df
        
    except Exception as e:
        logger.error(f"Erro ao extrair dados: {e}")
        raise

def calculate_technical_features(df):
    """Calcula features técnicas para cada moeda"""
    logger.info("Calculando features técnicas...")
    
    features_df = df.copy()
    
    # Agrupar por moeda para calcular indicadores
    grouped = features_df.groupby('coin_id')
    
    # Médias móveis
    for period in [9, 21, 50]:
        features_df[f'sma{period}'] = grouped['price'].transform(
            lambda x: x.rolling(period, min_periods=1).mean()
        )
    
    # RSI (Relative Strength Index)
    def calculate_rsi(prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
        rs = gain / loss.replace(0, np.inf)
        return 100 - (100 / (1 + rs))
    
    features_df['rsi'] = grouped['price'].transform(lambda x: calculate_rsi(x))
    
    # Mínimos e máximos
    features_df['min24h'] = grouped['price'].transform(
        lambda x: x.rolling(24, min_periods=1).min()
    )
    features_df['max24h'] = grouped['price'].transform(
        lambda x: x.rolling(24, min_periods=1).max()
    )
    
    # Variação 24h
    features_df['var24h'] = grouped['price'].transform(
        lambda x: (x - x.shift(24)) / x.shift(24).replace(0, np.inf)
    )
    
    # Volatilidade (desvio padrão dos retornos)
    features_df['volatility'] = grouped['price'].transform(
        lambda x: x.pct_change().rolling(10, min_periods=1).std()
    )
    
    # Volume normalizado (se disponível)
    if 'volume' in features_df.columns:
        features_df['volume_norm'] = grouped['volume'].transform(
            lambda x: (x - x.rolling(24, min_periods=1).mean()) / x.rolling(24, min_periods=1).std().replace(0, 1)
        )
    else:
        features_df['volume_norm'] = 0
    
    # Sentimento (placeholder - pode ser integrado com análise de redes sociais)
    features_df['sentiment'] = 0.5
    
    # Bandas de Bollinger
    features_df['bb_upper'] = features_df['sma21'] + (2 * grouped['price'].transform(
        lambda x: x.rolling(21, min_periods=1).std()
    ))
    features_df['bb_lower'] = features_df['sma21'] - (2 * grouped['price'].transform(
        lambda x: x.rolling(21, min_periods=1).std()
    ))
    features_df['bb_position'] = (features_df['price'] - features_df['bb_lower']) / (
        features_df['bb_upper'] - features_df['bb_lower']
    ).replace(0, 1)
    
    # MACD
    ema12 = grouped['price'].transform(lambda x: x.ewm(span=12).mean())
    ema26 = grouped['price'].transform(lambda x: x.ewm(span=26).mean())
    features_df['macd'] = ema12 - ema26
    features_df['macd_signal'] = features_df['macd'].rolling(9, min_periods=1).mean()
    
    logger.info("Features técnicas calculadas com sucesso")
    return features_df

def calculate_target_labels(df):
    """Calcula os labels de target baseados em variações futuras"""
    logger.info("Calculando labels de target...")
    
    df = df.copy()
    grouped = df.groupby('coin_id')
    
    # Preço futuro
    df['future_price'] = grouped['price'].shift(-FUTURE_WINDOW)
    
    # Retorno futuro
    df['future_return'] = (df['future_price'] - df['price']) / df['price']
    
    # Labels baseados em thresholds
    def create_label(return_val):
        if pd.isna(return_val):
            return 0  # HOLD para valores NaN
        elif return_val > BUY_THRESHOLD:
            return 1  # BUY
        elif return_val < SELL_THRESHOLD:
            return -1  # SELL
        else:
            return 0  # HOLD
    
    df['target'] = df['future_return'].apply(create_label)
    
    # Estatísticas dos labels
    label_counts = df['target'].value_counts()
    logger.info(f"Distribuição de labels: BUY={label_counts.get(1, 0)}, SELL={label_counts.get(-1, 0)}, HOLD={label_counts.get(0, 0)}")
    
    return df

def prepare_training_data(df):
    """Prepara dados para treinamento"""
    logger.info("Preparando dados para treinamento...")
    
    # Features para o modelo
    feature_columns = [
        'price', 'sma9', 'sma21', 'sma50', 'rsi', 
        'min24h', 'max24h', 'var24h', 'volatility',
        'volume_norm', 'sentiment', 'bb_position', 
        'macd', 'macd_signal'
    ]
    
    # Remover linhas com valores nulos
    clean_df = df.dropna(subset=feature_columns + ['target'])
    
    if clean_df.empty:
        raise ValueError("Nenhum dado válido após limpeza")
    
    # Preparar features e target
    X = clean_df[feature_columns].values
    y = clean_df['target'].values
    
    logger.info(f"Dados preparados: {X.shape[0]} samples, {X.shape[1]} features")
    
    # Verificar balanceamento das classes
    unique, counts = np.unique(y, return_counts=True)
    logger.info(f"Balanceamento das classes: {dict(zip(unique, counts))}")
    
    return X, y, feature_columns

def train_and_evaluate_model(X, y, feature_columns):
    """Treina e avalia o modelo"""
    logger.info("Treinando modelo...")
    
    # Dividir dados
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Normalizar features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Treinar modelo Random Forest
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight='balanced'  # Para lidar com desbalanceamento
    )
    
    clf.fit(X_train_scaled, y_train)
    
    # Avaliar modelo
    logger.info("Avaliando modelo...")
    
    # Predições
    y_pred = clf.predict(X_test_scaled)
    
    # Cross-validation
    cv_scores = cross_val_score(clf, X_train_scaled, y_train, cv=5)
    
    # Relatórios
    logger.info(f"Cross-validation score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    logger.info("Classification Report:")
    logger.info(f"\n{classification_report(y_test, y_pred)}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': clf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    logger.info("Top 10 features mais importantes:")
    logger.info(f"\n{feature_importance.head(10)}")
    
    return clf, scaler, {
        'cv_score': cv_scores.mean(),
        'cv_std': cv_scores.std(),
        'test_accuracy': clf.score(X_test_scaled, y_test),
        'feature_importance': feature_importance.to_dict('records')
    }

def save_model_and_artifacts(clf, scaler, metadata):
    """Salva modelo e artefatos"""
    logger.info("Salvando modelo e artefatos...")
    
    try:
        # Salvar modelo
        joblib.dump(clf, MODEL_PATH)
        logger.info(f"Modelo salvo em {MODEL_PATH}")
        
        # Salvar scaler
        joblib.dump(scaler, SCALER_PATH)
        logger.info(f"Scaler salvo em {SCALER_PATH}")
        
        # Salvar metadata
        metadata_path = MODEL_PATH.replace('.pkl', '_metadata.json')
        import json
        metadata['training_date'] = datetime.now().isoformat()
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Metadata salva em {metadata_path}")
        
    except Exception as e:
        logger.error(f"Erro ao salvar artefatos: {e}")
        raise

def main():
    """Função principal de treinamento"""
    try:
        logger.info("=== Iniciando treinamento do modelo MoCoVe ===")
        
        # 1. Extrair dados
        df = extract_data_from_db()
        
        # 2. Calcular features técnicas
        df_with_features = calculate_technical_features(df)
        
        # 3. Calcular target labels
        df_with_target = calculate_target_labels(df_with_features)
        
        # 4. Preparar dados
        X, y, feature_columns = prepare_training_data(df_with_target)
        
        # 5. Treinar modelo
        clf, scaler, metadata = train_and_evaluate_model(X, y, feature_columns)
        
        # 6. Salvar artefatos
        save_model_and_artifacts(clf, scaler, metadata)
        
        logger.info("=== Treinamento concluído com sucesso! ===")
        
    except Exception as e:
        logger.error(f"Erro no treinamento: {e}")
        raise

if __name__ == "__main__":
    main()
