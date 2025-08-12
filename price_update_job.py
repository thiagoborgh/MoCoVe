#!/usr/bin/env python3
"""
Price Update Job - MoCoVe AI Trading System
Job automático para atualizar preços da watchlist via Binance API
"""

import asyncio
import logging
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List
import ccxt
from dotenv import load_dotenv

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from watchlist_manager import WatchlistManager

# Carregar variáveis de ambiente
load_dotenv()

class PriceUpdateJob:
    def __init__(self, update_interval: int = 60):  # 60 segundos por padrão
        self.update_interval = update_interval
        self.logger = logging.getLogger(__name__)
        self.watchlist_manager = WatchlistManager()
        self.exchange = None
        self.running = False
        self.last_update = None
        self.update_count = 0
        self.error_count = 0
        
        # Configurar Binance
        self.setup_binance()
    
    def setup_binance(self):
        """Configurar conexão com Binance"""
        try:
            api_key = os.getenv('BINANCE_API_KEY', '')
            api_secret = os.getenv('BINANCE_API_SECRET', '')
            use_testnet = os.getenv('USE_TESTNET', 'false').lower() == 'true'
            
            if not api_key or not api_secret:
                self.logger.warning("Chaves da API Binance não configuradas")
                return False
            
            self.exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': use_testnet,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'
                }
            })
            
            # Testar conexão
            balance = self.exchange.fetch_balance()
            self.logger.info("Conexão com Binance estabelecida com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar Binance: {e}")
            return False
    
    async def update_single_coin(self, symbol: str) -> Dict:
        """Atualizar dados de uma única moeda"""
        try:
            # Obter ticker do Binance
            ticker = self.exchange.fetch_ticker(symbol)
            
            # Calcular variação percentual
            price_change_24h = (ticker['percentage'] or 0) / 100
            
            # Atualizar no watchlist manager
            self.watchlist_manager.update_coin_price(
                symbol=symbol,
                price=ticker['last'],
                volume_24h=ticker['quoteVolume'] or 0,
                price_change_24h=price_change_24h
            )
            
            return {
                'symbol': symbol,
                'price': ticker['last'],
                'volume_24h': ticker['quoteVolume'],
                'change_24h': price_change_24h,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'success': False
            }
    
    async def update_all_coins(self) -> Dict:
        """Atualizar todas as moedas da watchlist"""
        start_time = time.time()
        
        try:
            # Obter lista de símbolos da watchlist
            symbols = list(self.watchlist_manager.coins_data.keys())
            
            if not symbols:
                self.logger.warning("Nenhuma moeda na watchlist para atualizar")
                return {'success': False, 'message': 'Watchlist vazia'}
            
            self.logger.info(f"Iniciando atualização de {len(symbols)} moedas...")
            
            # Processar moedas em lotes para evitar rate limits
            batch_size = 10
            successful_updates = []
            failed_updates = []
            
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                
                # Processar lote
                batch_tasks = [self.update_single_coin(symbol) for symbol in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Processar resultados
                for result in batch_results:
                    if isinstance(result, Exception):
                        failed_updates.append(str(result))
                    elif result and result.get('success'):
                        successful_updates.append(result['symbol'])
                    else:
                        failed_updates.append(result.get('symbol', 'unknown'))
                
                # Aguardar entre lotes para respeitar rate limits
                if i + batch_size < len(symbols):
                    await asyncio.sleep(1)
            
            # Estatísticas da atualização
            elapsed_time = time.time() - start_time
            success_rate = len(successful_updates) / len(symbols) * 100
            
            self.update_count += 1
            self.last_update = datetime.now()
            
            if failed_updates:
                self.error_count += len(failed_updates)
            
            update_info = {
                'success': True,
                'total_coins': len(symbols),
                'successful_updates': len(successful_updates),
                'failed_updates': len(failed_updates),
                'success_rate': success_rate,
                'elapsed_time': elapsed_time,
                'timestamp': self.last_update.isoformat(),
                'update_count': self.update_count
            }
            
            self.logger.info(
                f"Atualização concluída: {len(successful_updates)}/{len(symbols)} moedas "
                f"({success_rate:.1f}%) em {elapsed_time:.1f}s"
            )
            
            if failed_updates:
                self.logger.warning(f"Falhas: {failed_updates[:5]}...")  # Mostrar apenas 5
            
            return update_info
            
        except Exception as e:
            self.logger.error(f"Erro na atualização geral: {e}")
            self.error_count += 1
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_continuous(self):
        """Executar atualizações contínuas"""
        self.running = True
        self.logger.info(f"Iniciando job de atualização contínua (intervalo: {self.update_interval}s)")
        
        while self.running:
            try:
                # Executar atualização
                result = await self.update_all_coins()
                
                if result['success']:
                    self.logger.debug(f"Atualização #{self.update_count} concluída com sucesso")
                else:
                    self.logger.error(f"Falha na atualização: {result.get('error', 'Erro desconhecido')}")
                
                # Aguardar próximo ciclo
                await asyncio.sleep(self.update_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Interrupção manual detectada")
                break
            except Exception as e:
                self.logger.error(f"Erro no ciclo de atualização: {e}")
                await asyncio.sleep(self.update_interval)
        
        self.running = False
        self.logger.info("Job de atualização finalizado")
    
    def stop(self):
        """Parar o job"""
        self.running = False
    
    def get_status(self) -> Dict:
        """Obter status do job"""
        return {
            'running': self.running,
            'update_interval': self.update_interval,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'update_count': self.update_count,
            'error_count': self.error_count,
            'success_rate': ((self.update_count - self.error_count) / max(self.update_count, 1)) * 100,
            'watchlist_size': len(self.watchlist_manager.coins_data),
            'exchange_connected': self.exchange is not None
        }

class PriceUpdateScheduler:
    """Agendador para múltiplos jobs de atualização"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.jobs = {}
        self.running = False
    
    def add_job(self, name: str, interval: int) -> bool:
        """Adicionar um novo job"""
        try:
            job = PriceUpdateJob(interval)
            self.jobs[name] = job
            self.logger.info(f"Job '{name}' adicionado com intervalo de {interval}s")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao adicionar job '{name}': {e}")
            return False
    
    def remove_job(self, name: str) -> bool:
        """Remover um job"""
        if name in self.jobs:
            self.jobs[name].stop()
            del self.jobs[name]
            self.logger.info(f"Job '{name}' removido")
            return True
        return False
    
    async def start_all_jobs(self):
        """Iniciar todos os jobs"""
        if not self.jobs:
            self.logger.warning("Nenhum job configurado")
            return
        
        self.running = True
        tasks = []
        
        for name, job in self.jobs.items():
            task = asyncio.create_task(job.run_continuous())
            tasks.append(task)
            self.logger.info(f"Job '{name}' iniciado")
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Erro na execução dos jobs: {e}")
        finally:
            self.running = False
    
    def stop_all_jobs(self):
        """Parar todos os jobs"""
        for name, job in self.jobs.items():
            job.stop()
            self.logger.info(f"Job '{name}' parado")
        self.running = False
    
    def get_jobs_status(self) -> Dict:
        """Obter status de todos os jobs"""
        return {name: job.get_status() for name, job in self.jobs.items()}

async def main():
    """Função principal"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # Criar job único para atualização
    job = PriceUpdateJob(update_interval=60)  # Atualizar a cada 60 segundos
    
    try:
        logger.info("=== MoCoVe Price Update Job ===")
        logger.info("Pressione Ctrl+C para parar")
        
        # Executar uma atualização inicial
        logger.info("Executando atualização inicial...")
        initial_result = await job.update_all_coins()
        
        if initial_result['success']:
            logger.info("Atualização inicial bem-sucedida")
        else:
            logger.error("Falha na atualização inicial")
        
        # Iniciar atualizações contínuas
        await job.run_continuous()
        
    except KeyboardInterrupt:
        logger.info("Finalizando job...")
    except Exception as e:
        logger.error(f"Erro na execução: {e}")
    finally:
        job.stop()
        logger.info("Job finalizado")

if __name__ == "__main__":
    asyncio.run(main())
