#!/usr/bin/env python3
"""
Portfolio Monitor - Sistema de Monitoramento de Performance
Monitora desvalorização/valorização das moedas baseado no preço de compra real
"""

import json
import time
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("PortfolioMonitor")

class PortfolioPosition:
    """Representa uma posição no portfólio"""
    def __init__(self, symbol: str, buy_price: float, quantity: float, buy_date: str, trade_id: str = None):
        self.symbol = symbol
        self.buy_price = buy_price
        self.quantity = quantity
        self.buy_date = buy_date
        self.trade_id = trade_id
        self.current_price = 0.0
        self.last_update = None
        
        # 🚀 TRAILING STOP: Rastreamento do pico máximo
        self.peak_price = buy_price  # Iniciar com preço de compra
        self.peak_performance_pct = 0.0  # Performance máxima atingida
        self.trailing_stop_triggered = False
        
    def update_current_price(self, current_price: float):
        """Atualiza o preço atual da posição e o trailing stop"""
        self.current_price = current_price
        self.last_update = datetime.now().isoformat()
        
        # 🚀 TRAILING STOP: Atualizar pico máximo se necessário
        if current_price > self.peak_price:
            self.peak_price = current_price
            self.peak_performance_pct = ((current_price - self.buy_price) / self.buy_price) * 100
            log.info(f"🚀 {self.symbol} NOVO PICO: ${current_price:.8f} (+{self.peak_performance_pct:.2f}%)")
    
    def get_performance(self) -> Dict:
        """Calcula a performance da posição com trailing stop"""
        if self.current_price <= 0:
            return {
                'symbol': self.symbol,
                'status': 'no_price',
                'performance_pct': 0.0,
                'pnl_usd': 0.0,
                'error': 'Preço atual não disponível'
            }
        
        # Cálculo da variação percentual baseada no preço de compra
        performance_pct = ((self.current_price - self.buy_price) / self.buy_price) * 100
        
        # 🚀 TRAILING STOP: Calcular queda do pico máximo
        drop_from_peak_pct = 0.0
        if self.peak_price > 0:
            drop_from_peak_pct = ((self.current_price - self.peak_price) / self.peak_price) * 100
        
        # Cálculo do P&L em USD
        position_value_now = self.current_price * self.quantity
        position_value_buy = self.buy_price * self.quantity
        pnl_usd = position_value_now - position_value_buy
        
        # Determinar status
        if performance_pct >= 10:
            status = 'excellent'
        elif performance_pct >= 5:
            status = 'good'
        elif performance_pct >= 0:
            status = 'positive'
        elif performance_pct >= -5:
            status = 'slight_loss'
        elif performance_pct >= -10:
            status = 'loss'
        else:
            status = 'heavy_loss'
        
        return {
            'symbol': self.symbol,
            'buy_price': self.buy_price,
            'current_price': self.current_price,
            'quantity': self.quantity,
            'buy_date': self.buy_date,
            'performance_pct': round(performance_pct, 2),
            'pnl_usd': round(pnl_usd, 4),
            'position_value_buy': round(position_value_buy, 2),
            'position_value_now': round(position_value_now, 2),
            'status': status,
            'last_update': self.last_update,
            'days_held': self._get_days_held(),
            # 🚀 TRAILING STOP INFO
            'peak_price': self.peak_price,
            'peak_performance_pct': round(self.peak_performance_pct, 2),
            'drop_from_peak_pct': round(drop_from_peak_pct, 2),
            'trailing_stop_triggered': self.trailing_stop_triggered
        }
    
    def _get_days_held(self) -> int:
        """Calcula quantos dias a posição está sendo mantida"""
        try:
            buy_datetime = datetime.fromisoformat(self.buy_date.replace('Z', '+00:00'))
            return (datetime.now() - buy_datetime).days
        except:
            return 0

class PortfolioMonitor:
    """Monitor de performance do portfólio"""
    
    def __init__(self, api_base: str = "http://localhost:5000"):
        self.api_base = api_base
        self.positions: Dict[str, PortfolioPosition] = {}
        self.portfolio_file = "portfolio_positions.json"
        self.load_positions()
        
        # Configurações de alertas - TRAILING STOP
        self.trailing_stop_percentage = 1.0  # 1% de queda do pico máximo
        self.take_profit_threshold = 15.0  # +15%
        self.monitoring_enabled = True
        
        log.info(f"🚀 Portfolio Monitor configurado:")
        log.info(f"   📉 Trailing Stop: {self.trailing_stop_percentage}% de queda do pico")
        log.info(f"   🎯 Take Profit: {self.take_profit_threshold}%")
        
    def load_positions(self):
        """Carrega posições do arquivo ou do histórico de trades"""
        try:
            # Tentar carregar do arquivo primeiro
            try:
                with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for pos_data in data.get('positions', []):
                        position = PortfolioPosition(
                            symbol=pos_data['symbol'],
                            buy_price=pos_data['buy_price'],
                            quantity=pos_data['quantity'],
                            buy_date=pos_data['buy_date'],
                            trade_id=pos_data.get('trade_id')
                        )
                        self.positions[pos_data['symbol']] = position
                log.info(f"📊 Carregadas {len(self.positions)} posições do arquivo")
            except FileNotFoundError:
                log.info("📊 Arquivo de posições não encontrado, carregando do histórico de trades")
                self._load_from_trades_history()
                
        except Exception as e:
            log.error(f"❌ Erro ao carregar posições: {e}")
    
    def _load_from_trades_history(self):
        """Carrega posições do histórico de trades via API"""
        try:
            response = requests.get(f"{self.api_base}/api/trades", timeout=10)
            if response.status_code == 200:
                trades = response.json()
                
                # Processar apenas trades de compra que ainda não foram vendidos
                buy_trades = [t for t in trades if t.get('type') == 'buy']
                sell_trades = [t for t in trades if t.get('type') == 'sell']
                
                # Criar conjunto de moedas já vendidas
                sold_symbols = {t.get('symbol') for t in sell_trades}
                
                for trade in buy_trades:
                    symbol = trade.get('symbol')
                    if symbol and symbol not in sold_symbols:
                        position = PortfolioPosition(
                            symbol=symbol,
                            buy_price=float(trade.get('price', 0)),
                            quantity=float(trade.get('amount', 0)),
                            buy_date=trade.get('date'),
                            trade_id=str(trade.get('id'))
                        )
                        self.positions[symbol] = position
                
                log.info(f"📊 Carregadas {len(self.positions)} posições ativas do histórico")
                self.save_positions()
                
        except Exception as e:
            log.error(f"❌ Erro ao carregar do histórico: {e}")
    
    def save_positions(self):
        """Salva posições no arquivo"""
        try:
            data = {
                'last_update': datetime.now().isoformat(),
                'positions': []
            }
            
            for position in self.positions.values():
                data['positions'].append({
                    'symbol': position.symbol,
                    'buy_price': position.buy_price,
                    'quantity': position.quantity,
                    'buy_date': position.buy_date,
                    'trade_id': position.trade_id,
                    'current_price': position.current_price,
                    'last_update': position.last_update
                })
            
            with open(self.portfolio_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            log.error(f"❌ Erro ao salvar posições: {e}")
    
    def add_position(self, symbol: str, buy_price: float, quantity: float, buy_date: str = None, trade_id: str = None):
        """Adiciona uma nova posição ao portfólio"""
        if buy_date is None:
            buy_date = datetime.now().isoformat()
            
        position = PortfolioPosition(symbol, buy_price, quantity, buy_date, trade_id)
        self.positions[symbol] = position
        self.save_positions()
        log.info(f"📊 Nova posição adicionada: {symbol} @ ${buy_price}")
    
    def remove_position(self, symbol: str):
        """Remove uma posição do portfólio (quando vendida)"""
        if symbol in self.positions:
            del self.positions[symbol]
            self.save_positions()
            log.info(f"📊 Posição removida: {symbol}")
    
    def update_prices(self):
        """Atualiza preços atuais de todas as posições"""
        if not self.positions:
            log.warning("📊 Nenhuma posição para atualizar")
            return
        
        log.info(f"📊 Atualizando preços de {len(self.positions)} posições...")
        
        for symbol, position in self.positions.items():
            try:
                # Buscar preço atual via API
                response = requests.get(
                    f"{self.api_base}/api/market_data",
                    params={"symbol": symbol},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    current_price = float(data.get('price', 0))
                    if current_price > 0:
                        position.update_current_price(current_price)
                        log.debug(f"📊 {symbol}: ${current_price:.8f}")
                    else:
                        log.warning(f"📊 {symbol}: Preço inválido recebido")
                else:
                    log.warning(f"📊 {symbol}: Erro na API - {response.status_code}")
                    
            except Exception as e:
                log.error(f"📊 {symbol}: Erro ao atualizar preço - {e}")
        
        self.save_positions()
    
    def get_portfolio_performance(self) -> Dict:
        """Calcula performance geral do portfólio"""
        if not self.positions:
            return {
                'total_positions': 0,
                'total_invested': 0.0,
                'total_current_value': 0.0,
                'total_pnl': 0.0,
                'portfolio_performance_pct': 0.0,
                'positions': []
            }
        
        self.update_prices()
        
        positions_performance = []
        total_invested = 0.0
        total_current_value = 0.0
        
        for position in self.positions.values():
            perf = position.get_performance()
            positions_performance.append(perf)
            total_invested += perf['position_value_buy']
            total_current_value += perf['position_value_now']
        
        total_pnl = total_current_value - total_invested
        portfolio_performance_pct = ((total_current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0.0
        
        # Ordenar por performance
        positions_performance.sort(key=lambda x: x['performance_pct'], reverse=True)
        
        return {
            'total_positions': len(self.positions),
            'total_invested': round(total_invested, 2),
            'total_current_value': round(total_current_value, 2),
            'total_pnl': round(total_pnl, 4),
            'portfolio_performance_pct': round(portfolio_performance_pct, 2),
            'positions': positions_performance,
            'last_update': datetime.now().isoformat()
        }
    
    def check_alerts(self) -> List[Dict]:
        """Verifica alertas de trailing stop e take-profit"""
        alerts = []
        
        for position in self.positions.values():
            perf = position.get_performance()
            
            # 🚀 TRAILING STOP: Verificar queda do pico máximo
            if perf['drop_from_peak_pct'] <= -self.trailing_stop_percentage:
                alerts.append({
                    'type': 'trailing_stop',
                    'symbol': position.symbol,
                    'current_price': position.current_price,
                    'peak_price': position.peak_price,
                    'drop_from_peak_pct': perf['drop_from_peak_pct'],
                    'peak_performance_pct': perf['peak_performance_pct'],
                    'performance_pct': perf['performance_pct'],
                    'threshold': -self.trailing_stop_percentage,
                    'message': f"� TRAILING STOP: {position.symbol} caiu {abs(perf['drop_from_peak_pct']):.2f}% do pico de +{perf['peak_performance_pct']:.2f}%",
                    'recommendation': 'VENDER TOTAL - Proteção de lucros'
                })
                
                # Marcar trailing stop como acionado
                position.trailing_stop_triggered = True
            
            # 🎯 TAKE PROFIT: Manter como estava
            elif perf['performance_pct'] >= self.take_profit_threshold:
                alerts.append({
                    'type': 'take_profit',
                    'symbol': position.symbol,
                    'performance_pct': perf['performance_pct'],
                    'threshold': self.take_profit_threshold,
                    'message': f"🎯 TAKE PROFIT: {position.symbol} subiu {perf['performance_pct']:.2f}%",
                    'recommendation': 'CONSIDERAR VENDA'
                })
        
        return alerts
    
    def monitor_loop(self, interval_seconds: int = 60):
        """Loop de monitoramento contínuo"""
        log.info(f"📊 Iniciando monitoramento a cada {interval_seconds} segundos...")
        
        while self.monitoring_enabled:
            try:
                # Atualizar performance
                portfolio = self.get_portfolio_performance()
                
                # Verificar alertas
                alerts = self.check_alerts()
                
                # Log resumo
                log.info(f"📊 Portfolio: {portfolio['total_positions']} posições | " +
                        f"P&L: ${portfolio['total_pnl']:.2f} ({portfolio['portfolio_performance_pct']:+.2f}%)")
                
                # Mostrar alertas
                for alert in alerts:
                    log.warning(alert['message'])
                
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                log.info("📊 Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                log.error(f"📊 Erro no monitoramento: {e}")
                time.sleep(interval_seconds)

def main():
    """Função principal para testar o monitor"""
    monitor = PortfolioMonitor()
    
    # Mostrar performance atual
    portfolio = monitor.get_portfolio_performance()
    print(f"\n📊 === PERFORMANCE DO PORTFÓLIO ===")
    print(f"Posições: {portfolio['total_positions']}")
    print(f"Investido: ${portfolio['total_invested']:.2f}")
    print(f"Valor atual: ${portfolio['total_current_value']:.2f}")
    print(f"P&L: ${portfolio['total_pnl']:.2f} ({portfolio['portfolio_performance_pct']:+.2f}%)")
    
    print(f"\n📊 === PERFORMANCE POR POSIÇÃO ===")
    for pos in portfolio['positions']:
        status_emoji = {
            'excellent': '🚀',
            'good': '📈',
            'positive': '✅',
            'slight_loss': '⚠️',
            'loss': '📉',
            'heavy_loss': '🚨'
        }.get(pos['status'], '❓')
        
        print(f"{status_emoji} {pos['symbol']}: {pos['performance_pct']:+.2f}% | " +
              f"${pos['pnl_usd']:+.2f} | {pos['days_held']} dias")

if __name__ == "__main__":
    main()