#!/usr/bin/env python3
"""
Atualizador de Status do Sistema MoCoVe
Script para manter o status do sistema atualizado em tempo real
"""

import time
import sqlite3
import json
import requests
import os
import psutil
from datetime import datetime
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemStatusUpdater:
    def __init__(self, db_path="memecoin.db"):
        self.db_path = db_path
        self.backend_url = "http://localhost:5000"
        
    def check_process_running(self, process_name: str) -> bool:
        """Verificar se um processo está rodando"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline']).lower()
                    if process_name.lower() in cmdline:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception:
            return False
    
    def check_backend_alive(self) -> bool:
        """Verificar se backend está respondendo"""
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def check_ai_agent_activity(self) -> bool:
        """Verificar atividade do AI Agent através do arquivo de status ou logs"""
        try:
            status_file = "ai_agent_status.txt"
            if os.path.exists(status_file):
                with open(status_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                # Espera-se formato: 'ACTIVE - 2025-08-14 12:34:56' ou similar
                if content.startswith("ACTIVE"):
                    # Extrair timestamp se disponível
                    parts = content.split("-", 1)
                    if len(parts) == 2:
                        ts_str = parts[1].strip()
                        try:
                            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                            # Considera ativo se atualizado nos últimos 2 minutos
                            if (datetime.now() - ts).total_seconds() < 120:
                                return True
                        except Exception:
                            # Se não conseguir parsear timestamp, assume ativo
                            return True
                    else:
                        return True
            # Fallback: checar log file
            log_file = "ai_trading_agent.log"
            if os.path.exists(log_file):
                stat = os.stat(log_file)
                # Log foi modificado nos últimos 2 minutos
                return (time.time() - stat.st_mtime) < 120
            return False
        except Exception:
            return False
    
    def update_status_in_db(self, status_data):
        """Atualizar status na base de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se existe registro recente (último minuto)
            cursor.execute('''
                SELECT id FROM system_status 
                WHERE timestamp > datetime('now', '-1 minute')
                ORDER BY timestamp DESC LIMIT 1
            ''')
            result = cursor.fetchone()
            
            if result:
                # Atualizar registro existente
                cursor.execute('''
                    UPDATE system_status SET
                        timestamp = ?,
                        backend_running = ?,
                        binance_connected = ?,
                        ai_agent_active = ?,
                        watchlist_loaded = ?,
                        price_updater_running = ?,
                        market_data_fresh = ?,
                        social_sentiment_active = ?,
                        error_count = ?,
                        warnings = ?
                    WHERE id = ?
                ''', (
                    status_data['timestamp'],
                    status_data['backend_running'],
                    status_data['binance_connected'],
                    status_data['ai_agent_active'],
                    status_data['watchlist_loaded'],
                    status_data['price_updater_running'],
                    status_data['market_data_fresh'],
                    status_data['social_sentiment_active'],
                    status_data['error_count'],
                    json.dumps(status_data['warnings']),
                    result[0]
                ))
            else:
                # Inserir novo registro
                cursor.execute('''
                    INSERT INTO system_status 
                    (timestamp, backend_running, binance_connected, ai_agent_active, 
                     watchlist_loaded, price_updater_running, balance_updated, 
                     market_data_fresh, social_sentiment_active, error_count, warnings)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    status_data['timestamp'],
                    status_data['backend_running'],
                    status_data['binance_connected'],
                    status_data['ai_agent_active'],
                    status_data['watchlist_loaded'],
                    status_data['price_updater_running'],
                    status_data.get('balance_updated', 'Nunca'),
                    status_data['market_data_fresh'],
                    status_data['social_sentiment_active'],
                    status_data['error_count'],
                    json.dumps(status_data['warnings'])
                ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar status na base: {e}")
            return False
    
    def collect_status(self):
        """Coletar status atual do sistema"""
        try:
            # Verificar componentes
            backend_running = self.check_backend_alive()
            ai_agent_active = self.check_ai_agent_activity()
            price_updater_running = self.check_process_running('populate_prices.py')
            
            # Verificar conexão Binance através da API
            binance_connected = False
            try:
                if backend_running:
                    response = requests.get(f"{self.backend_url}/api/system/status", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        binance_connected = data.get('status', {}).get('binance_connected', False)
            except:
                pass
            
            # Verificar watchlist
            watchlist_loaded = os.path.exists("coin_watchlist_expanded.json")
            
            # Verificar frescor dos dados
            market_data_fresh = False
            social_sentiment_active = False
            
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Dados de mercado frescos (últimos 5 minutos)
                cursor.execute('''
                    SELECT COUNT(*) FROM market_data 
                    WHERE timestamp > datetime('now', '-5 minutes')
                ''')
                market_data_fresh = cursor.fetchone()[0] > 0
                
                # Sentimento social ativo (última hora)
                cursor.execute('''
                    SELECT COUNT(*) FROM social_sentiment 
                    WHERE timestamp > datetime('now', '-1 hour')
                ''')
                social_sentiment_active = cursor.fetchone()[0] > 0
                
                conn.close()
            except:
                pass
            
            # Gerar warnings
            warnings = []
            if not backend_running:
                warnings.append("Backend não está rodando")
            if not ai_agent_active:
                warnings.append("AI Agent inativo")
            if not binance_connected:
                warnings.append("Binance não conectado")
            if not market_data_fresh:
                warnings.append("Dados de mercado desatualizados")
            
            status_data = {
                'timestamp': datetime.now().isoformat(),
                'backend_running': backend_running,
                'binance_connected': binance_connected,
                'ai_agent_active': ai_agent_active,
                'watchlist_loaded': watchlist_loaded,
                'price_updater_running': price_updater_running,
                'market_data_fresh': market_data_fresh,
                'social_sentiment_active': social_sentiment_active,
                'error_count': len([w for w in warnings if 'erro' in w.lower()]),
                'warnings': warnings
            }
            
            return status_data
            
        except Exception as e:
            logger.error(f"Erro ao coletar status: {e}")
            return None
    
    def run_once(self):
        """Executar uma atualização de status"""
        logger.info("Atualizando status do sistema...")
        
        status = self.collect_status()
        if status:
            success = self.update_status_in_db(status)
            if success:
                logger.info(f"Status atualizado: Backend={status['backend_running']}, AI={status['ai_agent_active']}, Binance={status['binance_connected']}")
            else:
                logger.error("Falha ao atualizar status na base")
        else:
            logger.error("Falha ao coletar status")
    
    def run_continuous(self, interval=30):
        """Executar atualizações contínuas"""
        logger.info(f"Iniciando atualizador de status (intervalo: {interval}s)")
        
        try:
            while True:
                self.run_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Atualizador parado pelo usuário")
        except Exception as e:
            logger.error(f"Erro no atualizador: {e}")

if __name__ == "__main__":
    import sys
    
    updater = SystemStatusUpdater()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Executar apenas uma vez
        updater.run_once()
    else:
        # Executar continuamente
        updater.run_continuous()
