"""
MoCoVe - Módulo de Segurança para Trading Real
Implementa limitações e verificações para conta Binance real
"""

import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class TradingSecurityManager:
    """Gerencia segurança e limitações para trading real"""
    
    def __init__(self, db_path: str = 'memecoin.db'):
        self.db_path = db_path
        self.max_trade_amount = float(os.getenv('MAX_TRADE_AMOUNT', 100.0))
        self.daily_loss_limit = float(os.getenv('DAILY_LOSS_LIMIT', 50.0))
        self.min_balance_usdt = float(os.getenv('MIN_BALANCE_USDT', 10.0))
        
    def validate_trade_amount(self, amount: float, symbol: str) -> Tuple[bool, str]:
        """Valida se o valor do trade está dentro dos limites"""
        try:
            if amount <= 0:
                return False, "Valor deve ser maior que zero"
            
            if amount > self.max_trade_amount:
                return False, f"Valor acima do limite máximo: ${amount:.2f} > ${self.max_trade_amount:.2f}"
            
            # Verificar se é múltiplo razoável (evitar trades muito pequenos)
            if amount < 1.0:
                return False, "Valor mínimo para trading: $1.00"
                
            return True, "Valor válido"
            
        except Exception as e:
            logger.error(f"Erro ao validar valor do trade: {e}")
            return False, f"Erro na validação: {str(e)}"
    
    def check_daily_limits(self) -> Tuple[bool, str, float]:
        """Verifica se os limites diários não foram ultrapassados"""
        try:
            # Calcular P&L do dia
            daily_pnl = self.calculate_daily_pnl()
            
            if daily_pnl < -abs(self.daily_loss_limit):
                return False, f"Limite de perda diária atingido: ${daily_pnl:.2f} < -${self.daily_loss_limit:.2f}", daily_pnl
            
            # Alerta se próximo do limite
            if daily_pnl < -abs(self.daily_loss_limit * 0.8):
                return True, f"AVISO: Próximo ao limite de perda (${daily_pnl:.2f})", daily_pnl
            
            return True, f"Dentro dos limites diários (P&L: ${daily_pnl:.2f})", daily_pnl
            
        except Exception as e:
            logger.error(f"Erro ao verificar limites diários: {e}")
            return False, f"Erro na verificação: {str(e)}", 0.0
    
    def calculate_daily_pnl(self) -> float:
        """Calcula P&L do dia atual"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Data de hoje
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Buscar trades do dia
            cursor.execute('''
                SELECT type, quantity, price, total
                FROM trades 
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp
            ''', (today,))
            
            trades = cursor.fetchall()
            conn.close()
            
            total_pnl = 0.0
            position = 0.0  # Posição atual
            avg_price = 0.0  # Preço médio de compra
            
            for trade_type, quantity, price, total in trades:
                if trade_type.upper() == 'BUY':
                    # Compra: adicionar à posição
                    if position == 0:
                        avg_price = price
                    else:
                        # Recalcular preço médio
                        total_cost = (position * avg_price) + (quantity * price)
                        total_quantity = position + quantity
                        avg_price = total_cost / total_quantity if total_quantity > 0 else price
                    
                    position += quantity
                    
                elif trade_type.upper() == 'SELL':
                    # Venda: reduzir posição e calcular P&L
                    if position > 0:
                        sold_quantity = min(quantity, position)
                        pnl = sold_quantity * (price - avg_price)
                        total_pnl += pnl
                        position -= sold_quantity
            
            return total_pnl
            
        except Exception as e:
            logger.error(f"Erro ao calcular P&L diário: {e}")
            return 0.0
    
    def verify_account_balance(self, exchange, min_usdt: Optional[float] = None) -> Tuple[bool, str, Dict]:
        """Verifica saldos da conta"""
        try:
            if min_usdt is None:
                min_usdt = self.min_balance_usdt
                
            balance = exchange.fetch_balance()
            
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            busd_balance = balance.get('BUSD', {}).get('free', 0)
            total_stable = usdt_balance + busd_balance
            
            balance_info = {
                'USDT': usdt_balance,
                'BUSD': busd_balance,
                'total_stable': total_stable,
                'timestamp': datetime.now().isoformat()
            }
            
            if total_stable < min_usdt:
                return False, f"Saldo insuficiente: ${total_stable:.2f} < ${min_usdt:.2f}", balance_info
            
            return True, f"Saldo adequado: ${total_stable:.2f}", balance_info
            
        except Exception as e:
            logger.error(f"Erro ao verificar saldo: {e}")
            return False, f"Erro na verificação de saldo: {str(e)}", {}
    
    def validate_market_conditions(self, symbol: str, exchange) -> Tuple[bool, str]:
        """Valida condições de mercado antes do trade"""
        try:
            # Obter ticker atual
            ticker = exchange.fetch_ticker(symbol)
            
            # Verificar se mercado está ativo
            if not ticker.get('last'):
                return False, f"Mercado {symbol} não disponível"
            
            # Verificar volatilidade extrema (> 10% em 24h)
            change_24h = abs(ticker.get('percentage', 0))
            if change_24h > 10:
                return False, f"Volatilidade extrema detectada: {change_24h:.2f}%"
            
            # Verificar volume mínimo
            volume_24h = ticker.get('baseVolume', 0)
            if volume_24h < 1000000:  # Volume mínimo de 1M
                return False, f"Volume insuficiente: {volume_24h:,.0f}"
            
            return True, f"Condições de mercado normais ({symbol})"
            
        except Exception as e:
            logger.error(f"Erro ao validar condições de mercado: {e}")
            return False, f"Erro na validação de mercado: {str(e)}"
    
    def comprehensive_risk_check(self, trade_data: Dict[str, Any], exchange) -> Dict[str, Any]:
        """Executa verificação completa de riscos"""
        
        checks = {
            'timestamp': datetime.now().isoformat(),
            'trade_data': trade_data,
            'validations': {},
            'overall_status': 'PENDING',
            'warnings': [],
            'errors': []
        }
        
        try:
            # 1. Validar valor do trade
            amount_valid, amount_msg = self.validate_trade_amount(
                trade_data.get('amount', 0), 
                trade_data.get('symbol', '')
            )
            checks['validations']['amount'] = {
                'status': 'PASS' if amount_valid else 'FAIL',
                'message': amount_msg
            }
            
            if not amount_valid:
                checks['errors'].append(amount_msg)
            
            # 2. Verificar limites diários
            daily_ok, daily_msg, daily_pnl = self.check_daily_limits()
            checks['validations']['daily_limits'] = {
                'status': 'PASS' if daily_ok else 'FAIL',
                'message': daily_msg,
                'current_pnl': daily_pnl
            }
            
            if not daily_ok:
                checks['errors'].append(daily_msg)
            elif 'AVISO' in daily_msg:
                checks['warnings'].append(daily_msg)
            
            # 3. Verificar saldo da conta
            balance_ok, balance_msg, balance_info = self.verify_account_balance(exchange)
            checks['validations']['balance'] = {
                'status': 'PASS' if balance_ok else 'FAIL',
                'message': balance_msg,
                'balance_info': balance_info
            }
            
            if not balance_ok:
                checks['errors'].append(balance_msg)
            
            # 4. Validar condições de mercado
            market_ok, market_msg = self.validate_market_conditions(
                trade_data.get('symbol', ''), exchange
            )
            checks['validations']['market'] = {
                'status': 'PASS' if market_ok else 'FAIL',
                'message': market_msg
            }
            
            if not market_ok:
                checks['errors'].append(market_msg)
            
            # Status geral
            if checks['errors']:
                checks['overall_status'] = 'REJECTED'
            elif checks['warnings']:
                checks['overall_status'] = 'APPROVED_WITH_WARNINGS'
            else:
                checks['overall_status'] = 'APPROVED'
            
            # Log do resultado
            logger.info(f"Risk check completed: {checks['overall_status']} for {trade_data}")
            
            return checks
            
        except Exception as e:
            logger.error(f"Erro na verificação de riscos: {e}")
            checks['overall_status'] = 'ERROR'
            checks['errors'].append(f"Erro na verificação: {str(e)}")
            return checks
    
    def log_security_event(self, event_type: str, message: str, data: Dict = None):
        """Registra eventos de segurança"""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = {
                'timestamp': timestamp,
                'event_type': event_type,
                'message': message,
                'data': data or {}
            }
            
            # Log estruturado
            logger.warning(f"SECURITY_EVENT: {event_type} - {message} - {data}")
            
            # Salvar em arquivo específico de segurança
            security_log_path = os.path.join('logs', 'security.log')
            os.makedirs('logs', exist_ok=True)
            
            with open(security_log_path, 'a') as f:
                f.write(f"{timestamp} | {event_type} | {message} | {data}\n")
                
        except Exception as e:
            logger.error(f"Erro ao registrar evento de segurança: {e}")

# Instância global do gerenciador de segurança
security_manager = TradingSecurityManager()

def execute_secure_trade(trade_data: Dict[str, Any], exchange) -> Dict[str, Any]:
    """
    Executa trade com verificações de segurança completas
    """
    # Verificação de riscos
    risk_check = security_manager.comprehensive_risk_check(trade_data, exchange)
    
    if risk_check['overall_status'] == 'REJECTED':
        security_manager.log_security_event(
            'TRADE_REJECTED',
            'Trade rejeitado por verificações de segurança',
            {'trade_data': trade_data, 'errors': risk_check['errors']}
        )
        return {
            'success': False,
            'message': 'Trade rejeitado por segurança',
            'errors': risk_check['errors'],
            'risk_check': risk_check
        }
    
    try:
        # Executar trade real
        if trade_data['action'].upper() == 'BUY':
            result = exchange.create_market_buy_order(
                trade_data['symbol'],
                trade_data['amount'] / trade_data['price']  # Quantidade em base currency
            )
        else:
            result = exchange.create_market_sell_order(
                trade_data['symbol'],
                trade_data['amount'] / trade_data['price']  # Quantidade em base currency
            )
        
        # Log de sucesso
        security_manager.log_security_event(
            'TRADE_EXECUTED',
            f"Trade executado com sucesso: {trade_data['action']} {trade_data['symbol']}",
            {'trade_data': trade_data, 'result': result, 'risk_check': risk_check}
        )
        
        return {
            'success': True,
            'message': 'Trade executado com sucesso',
            'result': result,
            'risk_check': risk_check,
            'warnings': risk_check.get('warnings', [])
        }
        
    except Exception as e:
        security_manager.log_security_event(
            'TRADE_ERROR',
            f"Erro na execução do trade: {str(e)}",
            {'trade_data': trade_data, 'error': str(e)}
        )
        
        return {
            'success': False,
            'message': f'Erro na execução: {str(e)}',
            'risk_check': risk_check
        }
