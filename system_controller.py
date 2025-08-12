#!/usr/bin/env python3
"""
System Control Manager - MoCoVe AI Trading System
Gerenciamento central de controles do sistema para integração com frontend
"""

import os
import sys
import json
import time
import psutil
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import sqlite3
import ccxt
from dotenv import load_dotenv

# Carregar configurações
load_dotenv()

@dataclass
class SystemStatus:
    timestamp: str
    backend_running: bool
    binance_connected: bool
    ai_agent_active: bool
    watchlist_loaded: bool
    price_updater_running: bool
    balance_updated: str
    market_data_fresh: bool
    social_sentiment_active: bool
    error_count: int
    warnings: List[str]

class SystemController:
    def __init__(self, db_path: str = "memecoin.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.processes = {}
        self.status_cache = {}
        self.last_update = None
        
        # Configurações
        self.binance_api_key = os.getenv('BINANCE_API_KEY', '')
        self.binance_api_secret = os.getenv('BINANCE_API_SECRET', '')
        self.use_testnet = os.getenv('USE_TESTNET', 'false').lower() == 'true'
        
        # Inicializar componentes
        self.setup_logging()
        self.init_database()
    
    def setup_logging(self):
        """Configurar logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def init_database(self):
        """Inicializar banco de dados para controles"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabela de status do sistema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de saldo da conta
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS account_balance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exchange TEXT DEFAULT 'binance',
                    asset TEXT NOT NULL,
                    free REAL,
                    locked REAL,
                    total REAL,
                    usd_value REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de sentimento social
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_sentiment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    source TEXT NOT NULL,
                    sentiment_score REAL,
                    volume_mentions INTEGER,
                    positive_ratio REAL,
                    negative_ratio REAL,
                    neutral_ratio REAL,
                    trending_score REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar database: {e}")
    
    def check_process_running(self, process_name: str) -> bool:
        """Verificar se um processo está rodando"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if process_name.lower() in ' '.join(proc.info['cmdline']).lower():
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception:
            return False
    
    def check_backend_api(self) -> bool:
        """Verificar se o backend está respondendo via API"""
        try:
            import requests
            response = requests.get("http://localhost:5000/api/health", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def check_ai_agent_activity(self) -> bool:
        """Verificar se o AI Agent está ativo através de logs recentes"""
        try:
            import os
            log_file = "ai_trading_agent.log"
            if os.path.exists(log_file):
                stat = os.stat(log_file)
                import time
                # Verificar se o log foi modificado nos últimos 2 minutos
                return (time.time() - stat.st_mtime) < 120
            return False
        except:
            return False
    
    def check_watchlist_loaded(self) -> bool:
        """Verificar se a watchlist está carregada"""
        try:
            import os
            return os.path.exists("coin_watchlist_expanded.json")
        except:
            return False
    
    def update_component_status(self, component: str, status: bool):
        """Atualizar status de componente específico na base"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se existe registro recente
            cursor.execute('''
                SELECT id FROM system_status 
                WHERE timestamp > datetime('now', '-5 minutes')
                ORDER BY timestamp DESC LIMIT 1
            ''')
            result = cursor.fetchone()
            
            if result:
                # Atualizar registro existente
                record_id = result[0]
                if component == "backend":
                    cursor.execute("UPDATE system_status SET backend_running = ?, timestamp = ? WHERE id = ?", 
                                 (status, datetime.now().isoformat(), record_id))
                elif component == "ai_agent":
                    cursor.execute("UPDATE system_status SET ai_agent_active = ?, timestamp = ? WHERE id = ?", 
                                 (status, datetime.now().isoformat(), record_id))
            else:
                # Criar novo registro
                cursor.execute('''
                    INSERT INTO system_status 
                    (timestamp, backend_running, binance_connected, ai_agent_active, watchlist_loaded, 
                     balance_updated, market_data_fresh, error_count, warnings)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (datetime.now().isoformat(), 
                      component == "backend" and status,
                      False,  # binance será atualizado separadamente
                      component == "ai_agent" and status, 
                      True,   # watchlist padrão
                      "Nunca", False, 0, ""))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar status do componente: {e}")
    
    def start_backend(self) -> bool:
        """Iniciar backend Flask"""
        try:
            if self.check_process_running('app_real.py'):
                self.logger.info("Backend já está rodando")
                return True
            
            backend_process = subprocess.Popen([
                sys.executable, 'backend/app_real.py'
            ], cwd=os.getcwd())
            
            self.processes['backend'] = backend_process
            time.sleep(3)  # Aguardar inicialização
            
            if backend_process.poll() is None:
                self.update_system_status('backend', 'running', 'Backend Flask iniciado')
                return True
            else:
                self.update_system_status('backend', 'failed', 'Falha ao iniciar backend')
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao iniciar backend: {e}")
            self.update_system_status('backend', 'error', str(e))
            return False
    
    def stop_backend(self) -> bool:
        """Parar backend"""
        try:
            if 'backend' in self.processes:
                self.processes['backend'].terminate()
                del self.processes['backend']
            
            # Terminar todos os processos do backend
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'app_real.py' in ' '.join(proc.info['cmdline']):
                        proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.update_system_status('backend', 'stopped', 'Backend parado')
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao parar backend: {e}")
            return False
    
    def test_binance_connection(self) -> Dict:
        """Testar conexão com Binance"""
        try:
            if not self.binance_api_key or not self.binance_api_secret:
                return {
                    'connected': False,
                    'error': 'API keys não configuradas',
                    'account_type': None,
                    'permissions': []
                }
            
            exchange = ccxt.binance({
                'apiKey': self.binance_api_key,
                'secret': self.binance_api_secret,
                'sandbox': self.use_testnet,
                'enableRateLimit': True
            })
            
            # Testar conexão
            account_info = exchange.fetch_balance()
            
            result = {
                'connected': True,
                'error': None,
                'account_type': 'testnet' if self.use_testnet else 'mainnet',
                'permissions': account_info.get('info', {}).get('permissions', []),
                'can_trade': account_info.get('info', {}).get('canTrade', False),
                'can_withdraw': account_info.get('info', {}).get('canWithdraw', False),
                'update_time': datetime.now().isoformat()
            }
            
            self.update_system_status('binance', 'connected', json.dumps(result))
            return result
            
        except Exception as e:
            error_result = {
                'connected': False,
                'error': str(e),
                'account_type': None,
                'permissions': []
            }
            self.update_system_status('binance', 'error', str(e))
            return error_result
    
    def start_ai_agent(self) -> bool:
        """Iniciar AI Agent"""
        try:
            if self.check_process_running('ai_trading_agent.py'):
                self.logger.info("AI Agent já está rodando")
                return True
            
            ai_process = subprocess.Popen([
                sys.executable, 'ai_trading_agent.py'
            ], cwd=os.getcwd())
            
            self.processes['ai_agent'] = ai_process
            time.sleep(2)
            
            if ai_process.poll() is None:
                self.update_system_status('ai_agent', 'running', 'AI Agent iniciado')
                return True
            else:
                self.update_system_status('ai_agent', 'failed', 'Falha ao iniciar AI Agent')
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao iniciar AI Agent: {e}")
            self.update_system_status('ai_agent', 'error', str(e))
            return False
    
    def stop_ai_agent(self) -> bool:
        """Parar AI Agent"""
        try:
            if 'ai_agent' in self.processes:
                self.processes['ai_agent'].terminate()
                del self.processes['ai_agent']
            
            # Terminar processos do AI Agent
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'ai_trading_agent.py' in ' '.join(proc.info['cmdline']):
                        proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.update_system_status('ai_agent', 'stopped', 'AI Agent parado')
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao parar AI Agent: {e}")
            return False
    
    def update_account_balance(self) -> Dict:
        """Atualizar saldo da conta Binance"""
        try:
            if not self.binance_api_key or not self.binance_api_secret:
                return {'error': 'API keys não configuradas'}
            
            exchange = ccxt.binance({
                'apiKey': self.binance_api_key,
                'secret': self.binance_api_secret,
                'sandbox': self.use_testnet,
                'enableRateLimit': True
            })
            
            balance = exchange.fetch_balance()
            
            # Salvar no banco
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Limpar dados antigos (manter apenas últimas 24h)
            cursor.execute('''
                DELETE FROM account_balance 
                WHERE timestamp < datetime('now', '-24 hours')
            ''')
            
            total_usd = 0
            balances_summary = {}
            
            for asset, amounts in balance['total'].items():
                if amounts > 0:
                    free = balance['free'].get(asset, 0)
                    locked = balance['used'].get(asset, 0)
                    
                    # Tentar obter preço em USD (simplificado)
                    usd_value = 0
                    if asset == 'USDT' or asset == 'BUSD':
                        usd_value = amounts
                    else:
                        try:
                            ticker = exchange.fetch_ticker(f"{asset}/USDT")
                            usd_value = amounts * ticker['last']
                        except:
                            pass
                    
                    # Salvar no banco
                    cursor.execute('''
                        INSERT OR REPLACE INTO account_balance 
                        (asset, free, locked, total, usd_value)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (asset, free, locked, amounts, usd_value))
                    
                    balances_summary[asset] = {
                        'free': free,
                        'locked': locked,
                        'total': amounts,
                        'usd_value': usd_value
                    }
                    
                    total_usd += usd_value
            
            conn.commit()
            conn.close()
            
            result = {
                'success': True,
                'total_usd': total_usd,
                'balances': balances_summary,
                'updated_at': datetime.now().isoformat()
            }
            
            self.update_system_status('balance', 'updated', f'Total: ${total_usd:.2f}')
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar saldo: {e}")
            return {'error': str(e)}
    
    def update_market_data(self) -> Dict:
        """Atualizar dados de mercado para watchlist"""
        try:
            # Usar a API do backend para atualizar preços
            import requests
            
            response = requests.post('http://localhost:5000/api/watchlist/update-prices')
            
            if response.status_code == 200:
                result = response.json()
                self.update_system_status('market_data', 'updated', f"Atualizadas {result.get('updated_coins', 0)} moedas")
                return result
            else:
                error = f"HTTP {response.status_code}"
                self.update_system_status('market_data', 'error', error)
                return {'error': error}
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar dados de mercado: {e}")
            self.update_system_status('market_data', 'error', str(e))
            return {'error': str(e)}
    
    def update_social_sentiment(self) -> Dict:
        """Simular atualização de sentimento social (placeholder)"""
        try:
            # Placeholder - aqui você integraria com APIs de redes sociais
            symbols = ['DOGEUSDT', 'SHIBUSDT', 'PEPEUSDT', 'SOLUSDT', 'ADAUSDT']
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updated_count = 0
            
            for symbol in symbols:
                # Gerar dados simulados (substitua por integração real)
                import random
                sentiment_score = random.uniform(-1, 1)
                volume_mentions = random.randint(100, 10000)
                positive_ratio = random.uniform(0.2, 0.8)
                negative_ratio = random.uniform(0.1, 0.4)
                neutral_ratio = 1 - positive_ratio - negative_ratio
                trending_score = random.uniform(0, 1)
                
                cursor.execute('''
                    INSERT INTO social_sentiment 
                    (symbol, source, sentiment_score, volume_mentions, positive_ratio, 
                     negative_ratio, neutral_ratio, trending_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (symbol, 'aggregated', sentiment_score, volume_mentions,
                      positive_ratio, negative_ratio, neutral_ratio, trending_score))
                
                updated_count += 1
            
            conn.commit()
            conn.close()
            
            result = {
                'success': True,
                'updated_symbols': updated_count,
                'updated_at': datetime.now().isoformat()
            }
            
            self.update_system_status('sentiment', 'updated', f"Atualizados {updated_count} símbolos")
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar sentimento: {e}")
            self.update_system_status('sentiment', 'error', str(e))
            return {'error': str(e)}
    
    def update_system_status(self, component: str, status: bool, details: str = ''):
        """Atualizar status de um componente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se existe registro
            cursor.execute("SELECT id FROM system_status ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                # Atualizar registro existente
                record_id = result[0]
                
                if component == "backend":
                    cursor.execute("UPDATE system_status SET backend_running = ?, timestamp = ? WHERE id = ?", 
                                 (status, datetime.now().isoformat(), record_id))
                elif component == "binance":
                    cursor.execute("UPDATE system_status SET binance_connected = ?, timestamp = ? WHERE id = ?", 
                                 (status, datetime.now().isoformat(), record_id))
                elif component == "ai_agent":
                    cursor.execute("UPDATE system_status SET ai_agent_active = ?, timestamp = ? WHERE id = ?", 
                                 (status, datetime.now().isoformat(), record_id))
                elif component == "watchlist":
                    cursor.execute("UPDATE system_status SET watchlist_loaded = ?, timestamp = ? WHERE id = ?", 
                                 (status, datetime.now().isoformat(), record_id))
                else:
                    # Para outros componentes, atualizar warnings
                    cursor.execute("UPDATE system_status SET warnings = ?, timestamp = ? WHERE id = ?", 
                                 (details, datetime.now().isoformat(), record_id))
            else:
                # Inserir novo registro com estrutura correta
                cursor.execute('''
                    INSERT INTO system_status 
                    (timestamp, backend_running, binance_connected, ai_agent_active, watchlist_loaded, 
                     balance_updated, market_data_fresh, error_count, warnings)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (datetime.now().isoformat(), 
                      component == "backend" and status,
                      component == "binance" and status,
                      component == "ai_agent" and status, 
                      component == "watchlist" and status,
                      "Nunca", False, 0, details))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar status: {e}")
    
    def get_system_status(self) -> SystemStatus:
        """Obter status completo do sistema"""
        try:
            # Verificar componentes de forma mais robusta
            backend_running = self.check_process_running('app_real.py') or self.check_backend_api()
            ai_agent_active = self.check_process_running('ai_trading_agent.py') or self.check_ai_agent_activity()
            price_updater_running = self.check_process_running('populate_prices.py')
            
            # Testar Binance
            binance_test = self.test_binance_connection()
            binance_connected = binance_test['connected']
            
            # Verificar watchlist
            watchlist_loaded = self.check_watchlist_loaded()
            
            # Verificar última atualização de saldo
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Atualizar status na base se componentes estão ativos
            if backend_running:
                self.update_component_status('backend', True)
            if ai_agent_active:
                self.update_component_status('ai_agent', True)
            
            cursor.execute('''
                SELECT timestamp FROM account_balance 
                ORDER BY timestamp DESC LIMIT 1
            ''')
            balance_result = cursor.fetchone()
            balance_updated = balance_result[0] if balance_result else 'Nunca'
            
            # Verificar frescor dos dados de mercado
            cursor.execute('''
                SELECT timestamp FROM market_data 
                WHERE timestamp > datetime('now', '-5 minutes')
                LIMIT 1
            ''')
            market_fresh = cursor.fetchone() is not None
            
            # Verificar sentimento social
            cursor.execute('''
                SELECT COUNT(*) FROM social_sentiment 
                WHERE timestamp > datetime('now', '-1 hour')
            ''')
            sentiment_count = cursor.fetchone()[0]
            social_sentiment_active = sentiment_count > 0
            
            # Contar erros recentes
            cursor.execute('''
                SELECT COUNT(*) FROM system_status 
                WHERE warnings LIKE '%erro%' AND timestamp > datetime('now', '-1 hour')
            ''')
            error_count = cursor.fetchone()[0]
            
            conn.close()
            
            # Gerar warnings
            warnings = []
            if not backend_running:
                warnings.append("Backend não está rodando")
            if not binance_connected:
                warnings.append("Binance não conectado")
            if not market_fresh:
                warnings.append("Dados de mercado desatualizados")
            if error_count > 0:
                warnings.append(f"{error_count} erros na última hora")
            
            return SystemStatus(
                timestamp=datetime.now().isoformat(),
                backend_running=backend_running,
                binance_connected=binance_connected,
                ai_agent_active=ai_agent_active,
                watchlist_loaded=watchlist_loaded,
                price_updater_running=price_updater_running,
                balance_updated=balance_updated,
                market_data_fresh=market_fresh,
                social_sentiment_active=social_sentiment_active,
                error_count=error_count,
                warnings=warnings
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao obter status: {e}")
            return SystemStatus(
                timestamp=datetime.now().isoformat(),
                backend_running=False,
                binance_connected=False,
                ai_agent_active=False,
                watchlist_loaded=False,
                price_updater_running=False,
                balance_updated='Erro',
                market_data_fresh=False,
                social_sentiment_active=False,
                error_count=1,
                warnings=[f"Erro ao verificar status: {e}"]
            )
    
    def get_recent_balances(self) -> List[Dict]:
        """Obter saldos recentes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT asset, free, locked, total, usd_value, timestamp
                FROM account_balance 
                WHERE timestamp = (
                    SELECT MAX(timestamp) FROM account_balance
                )
                ORDER BY usd_value DESC
            ''')
            
            balances = []
            for row in cursor.fetchall():
                balances.append({
                    'asset': row[0],
                    'free': row[1],
                    'locked': row[2],
                    'total': row[3],
                    'usd_value': row[4],
                    'timestamp': row[5]
                })
            
            conn.close()
            return balances
            
        except Exception as e:
            self.logger.error(f"Erro ao obter saldos: {e}")
            return []
    
    def get_social_sentiment_summary(self) -> Dict:
        """Obter resumo do sentimento social"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT symbol, 
                       AVG(sentiment_score) as avg_sentiment,
                       SUM(volume_mentions) as total_mentions,
                       AVG(trending_score) as avg_trending
                FROM social_sentiment 
                WHERE timestamp > datetime('now', '-1 hour')
                GROUP BY symbol
                ORDER BY avg_trending DESC
            ''')
            
            sentiments = []
            for row in cursor.fetchall():
                sentiments.append({
                    'symbol': row[0],
                    'avg_sentiment': row[1],
                    'total_mentions': row[2],
                    'trending_score': row[3]
                })
            
            conn.close()
            return {'sentiments': sentiments}
            
        except Exception as e:
            self.logger.error(f"Erro ao obter sentimento: {e}")
            return {'sentiments': []}

if __name__ == "__main__":
    # Teste do sistema
    controller = SystemController()
    
    status = controller.get_system_status()
    print(f"Sistema Status: {status}")
    
    # Testar Binance
    binance_test = controller.test_binance_connection()
    print(f"Binance: {binance_test}")
    
    # Atualizar saldo
    balance_update = controller.update_account_balance()
    print(f"Saldo: {balance_update}")
