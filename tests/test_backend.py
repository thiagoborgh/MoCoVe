"""
Testes para o Backend do MoCoVe
"""

import unittest
import json
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

# Adicionar o diretório do backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, init_database

class TestMoCoVeBackend(unittest.TestCase):
    def test_ai_robust_log_endpoint(self):
        """Testa o endpoint do log do agente robusto de IA"""
        response = self.app.get('/api/ai-robust-log')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('log', data)
        # O log pode estar vazio, mas a chave deve existir
    
    def setUp(self):
        """Configuração para cada teste"""
        self.db_fd, app.config['DB_PATH'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.app = app.test_client()
        
        # Configurar variáveis de ambiente para teste
        os.environ['DB_PATH'] = app.config['DB_PATH']
        os.environ['USE_TESTNET'] = 'true'
        
        # Inicializar banco de dados de teste
        init_database()
    
    def tearDown(self):
        """Limpeza após cada teste"""
        os.close(self.db_fd)
        os.unlink(app.config['DB_PATH'])
    
    def test_status_endpoint(self):
        """Testa o endpoint de status"""
        response = self.app.get('/api/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'online')
    
    def test_trades_endpoint_empty(self):
        """Testa endpoint de trades vazio"""
        response = self.app.get('/api/trades')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)
    
    def test_prices_endpoint(self):
        """Testa endpoint de preços"""
        response = self.app.get('/api/prices?symbol=DOGE/BUSD')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
    
    def test_volatility_endpoint(self):
        """Testa endpoint de volatilidade"""
        response = self.app.get('/api/volatility?symbol=DOGE/BUSD')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('volatility', data)
        self.assertIn('threshold', data)
        self.assertIn('is_high', data)
    
    def test_settings_get(self):
        """Testa obter configurações"""
        response = self.app.get('/api/settings')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('symbol', data)
        self.assertIn('amount', data)
        self.assertIn('volatility_threshold', data)
    
    def test_settings_post(self):
        """Testa atualizar configurações"""
        new_settings = {
            'symbol': 'SHIB/BUSD',
            'amount': 200,
            'volatility_threshold': 0.08
        }
        
        response = self.app.post('/api/settings', 
                               data=json.dumps(new_settings),
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('message', data)
    
    @patch('app.exchange.fetch_ticker')
    def test_market_data_endpoint(self, mock_fetch_ticker):
        """Testa endpoint de dados de mercado com mock"""
        mock_fetch_ticker.return_value = {
            'last': 0.08,
            'high': 0.085,
            'low': 0.075,
            'baseVolume': 1000000,
            'change': 0.005,
            'percentage': 6.25
        }
        
        response = self.app.get('/api/market_data?symbol=DOGE/BUSD')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('price', data)
        self.assertIn('volume', data)
        self.assertEqual(data['symbol'], 'DOGE/BUSD')

class TestDataValidation(unittest.TestCase):
    """Testes de validação de dados"""
    
    def test_calculate_volatility(self):
        """Testa cálculo de volatilidade"""
        from app import calculate_volatility
        
        # Teste com preços estáveis
        stable_prices = [1.0, 1.0, 1.0, 1.0, 1.0]
        volatility = calculate_volatility(stable_prices)
        self.assertEqual(volatility, 0.0)
        
        # Teste com preços voláteis
        volatile_prices = [1.0, 1.1, 0.9, 1.2, 0.8]
        volatility = calculate_volatility(volatile_prices)
        self.assertGreater(volatility, 0)
        
        # Teste com lista vazia
        empty_prices = []
        volatility = calculate_volatility(empty_prices)
        self.assertEqual(volatility, 0.0)

if __name__ == '__main__':
    unittest.main()
