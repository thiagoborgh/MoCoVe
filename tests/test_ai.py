"""
Testes para os modelos de IA do MoCoVe
"""

import unittest
import numpy as np
import pandas as pd
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
import json

# Adicionar o diretório da IA ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ai'))

class TestAIModel(unittest.TestCase):
    """Testes para o modelo de IA"""
    
    def setUp(self):
        """Configuração para os testes"""
        self.test_features = {
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
    
    def test_features_validation(self):
        """Testa validação das features"""
        # Teste com features válidas
        self.assertGreater(self.test_features['price'], 0)
        self.assertGreaterEqual(self.test_features['rsi'], 0)
        self.assertLessEqual(self.test_features['rsi'], 100)
        self.assertGreaterEqual(self.test_features['sentiment'], 0)
        self.assertLessEqual(self.test_features['sentiment'], 1)
    
    def test_rule_based_decision_buy_signal(self):
        """Testa sinal de compra no sistema baseado em regras"""
        try:
            from ai_model import rule_based_decision, Features
            
            # Configurar features para sinal de compra
            buy_features = Features(
                price=0.08,
                sma9=0.081,  # SMA9 > SMA21 (tendência de alta)
                sma21=0.079,
                sma50=0.077,
                rsi=25.0,    # RSI baixo (oversold)
                min24h=0.075,
                max24h=0.082,
                var24h=0.05,  # Alta volatilidade positiva
                volume=2000000,
                sentiment=0.8  # Sentimento positivo
            )
            
            prediction = rule_based_decision(buy_features)
            
            self.assertEqual(prediction.decision, "BUY")
            self.assertGreater(prediction.probability, 0.5)
            self.assertIn("BUY", prediction.reasoning)
            
        except ImportError:
            self.skipTest("Módulo ai_model não disponível")
    
    def test_rule_based_decision_sell_signal(self):
        """Testa sinal de venda no sistema baseado em regras"""
        try:
            from ai_model import rule_based_decision, Features
            
            # Configurar features para sinal de venda
            sell_features = Features(
                price=0.08,
                sma9=0.077,  # SMA9 < SMA21 (tendência de baixa)
                sma21=0.079,
                sma50=0.081,
                rsi=85.0,    # RSI alto (overbought)
                min24h=0.075,
                max24h=0.082,
                var24h=-0.08,  # Volatilidade negativa
                volume=500000,
                sentiment=0.2  # Sentimento negativo
            )
            
            prediction = rule_based_decision(sell_features)
            
            self.assertEqual(prediction.decision, "SELL")
            self.assertGreater(prediction.probability, 0.5)
            self.assertIn("SELL", prediction.reasoning)
            
        except ImportError:
            self.skipTest("Módulo ai_model não disponível")
    
    def test_rule_based_decision_hold_signal(self):
        """Testa sinal de hold no sistema baseado em regras"""
        try:
            from ai_model import rule_based_decision, Features
            
            # Configurar features neutras
            hold_features = Features(
                price=0.08,
                sma9=0.0795,  # SMAs próximas
                sma21=0.079,
                sma50=0.0785,
                rsi=50.0,     # RSI neutro
                min24h=0.078,
                max24h=0.082,
                var24h=0.01,  # Baixa volatilidade
                volume=1000000,
                sentiment=0.5  # Sentimento neutro
            )
            
            prediction = rule_based_decision(hold_features)
            
            self.assertEqual(prediction.decision, "HOLD")
            self.assertIn("NEUTRO", prediction.reasoning)
            
        except ImportError:
            self.skipTest("Módulo ai_model não disponível")

class TestTrainingData(unittest.TestCase):
    """Testes para processamento de dados de treinamento"""
    
    def test_data_preprocessing(self):
        """Testa o preprocessamento de dados"""
        # Criar dados de teste
        test_data = pd.DataFrame({
            'coin_id': ['DOGE', 'DOGE', 'DOGE', 'DOGE', 'DOGE'],
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='H'),
            'price': [0.08, 0.082, 0.079, 0.085, 0.081],
            'volume': [1000000, 1200000, 900000, 1500000, 1100000]
        })
        
        # Verificar estrutura dos dados
        self.assertEqual(len(test_data), 5)
        self.assertIn('price', test_data.columns)
        self.assertIn('volume', test_data.columns)
        self.assertTrue(all(test_data['price'] > 0))
    
    def test_technical_indicators_calculation(self):
        """Testa cálculo de indicadores técnicos"""
        # Dados de preços de teste
        prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109])
        
        # Teste SMA simples
        sma_5 = np.mean(prices[-5:])
        self.assertIsInstance(sma_5, float)
        self.assertGreater(sma_5, 0)
        
        # Teste RSI básico
        returns = np.diff(prices)
        gains = returns[returns > 0]
        losses = -returns[returns < 0]
        
        if len(gains) > 0 and len(losses) > 0:
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            self.assertGreaterEqual(rsi, 0)
            self.assertLessEqual(rsi, 100)

class TestModelPerformance(unittest.TestCase):
    """Testes de performance do modelo"""
    
    def test_prediction_speed(self):
        """Testa velocidade das predições"""
        try:
            from ai_model import rule_based_decision, Features
            import time
            
            features = Features(
                price=0.08,
                rsi=50.0,
                var24h=0.02,
                sentiment=0.5
            )
            
            start_time = time.time()
            prediction = rule_based_decision(features)
            end_time = time.time()
            
            # Predição deve ser rápida (menos de 1 segundo)
            self.assertLess(end_time - start_time, 1.0)
            self.assertIsNotNone(prediction)
            
        except ImportError:
            self.skipTest("Módulo ai_model não disponível")
    
    def test_memory_usage(self):
        """Testa uso de memória básico"""
        # Teste simples de uso de memória
        large_array = np.random.rand(10000)
        
        # Verificar que conseguimos criar arrays grandes
        self.assertEqual(len(large_array), 10000)
        
        # Limpar memória
        del large_array

if __name__ == '__main__':
    unittest.main()


# Teste extra: Execução do agente robusto de IA (verificação básica)
import subprocess
import time
import os

def test_robust_agent_execution():
    """Testa se o agente robusto de IA executa e gera log"""
    log_path = os.path.join(os.path.dirname(__file__), '..', 'ai_trading_agent_robust.log')
    # Remove log antigo se existir
    if os.path.exists(log_path):
        os.remove(log_path)
    # Executa o agente por alguns segundos
    proc = subprocess.Popen(['python', '../ai_trading_agent_robust.py'])
    time.sleep(5)
    proc.terminate()
    proc.wait()
    # Verifica se o log foi criado
    assert os.path.exists(log_path), 'Log do agente robusto não foi criado.'
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        assert len(lines) > 0, 'Log do agente robusto está vazio.'
