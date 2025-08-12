#!/usr/bin/env python3
"""
Dashboard de Monitoramento do AI Trading Agent
Interface para monitorar o agente em tempo real
"""

import time
import os
import json
import requests
from datetime import datetime, timedelta
import threading
from typing import Dict, List

class AgentMonitor:
    """Monitor em tempo real do agente de IA"""
    
    def __init__(self):
        self.api_base = "http://localhost:5000"
        self.log_file = "ai_trading_agent.log"
        self.is_monitoring = False
        
        # Estatísticas
        self.stats = {
            'trades_today': 0,
            'total_profit': 0.0,
            'win_rate': 0.0,
            'last_signal': None,
            'current_position': None,
            'system_status': 'Unknown'
        }
        
    def clear_screen(self):
        """Limpa a tela"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_system_status(self) -> Dict:
        """Obtém status do sistema"""
        try:
            response = requests.get(f"{self.api_base}/api/status", timeout=5)
            if response.status_code == 200:
                return response.json()
            return {'status': 'offline'}
        except:
            return {'status': 'offline'}
    
    def get_market_data(self) -> Dict:
        """Obtém dados atuais do mercado"""
        try:
            response = requests.get(f"{self.api_base}/api/market_data?symbol=DOGEUSDT", timeout=5)
            if response.status_code == 200:
                return response.json()
            return {}
        except:
            return {}
    
    def get_recent_trades(self) -> List[Dict]:
        """Obtém trades recentes"""
        try:
            response = requests.get(f"{self.api_base}/api/trades", timeout=5)
            if response.status_code == 200:
                trades = response.json()
                # Filtrar trades de hoje
                today = datetime.now().date()
                recent_trades = []
                for trade in trades:
                    try:
                        trade_date = datetime.fromisoformat(trade['timestamp'].replace('Z', '')).date()
                        if trade_date == today:
                            recent_trades.append(trade)
                    except:
                        continue
                return recent_trades
            return []
        except:
            return []
    
    def read_recent_logs(self, lines: int = 10) -> List[str]:
        """Lê logs recentes do agente"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    return all_lines[-lines:] if len(all_lines) >= lines else all_lines
            return []
        except:
            return []
    
    def calculate_stats(self, trades: List[Dict]):
        """Calcula estatísticas dos trades"""
        if not trades:
            return
        
        self.stats['trades_today'] = len(trades)
        
        # Calcular P&L aproximado (simplificado)
        total_profit = 0.0
        profitable_trades = 0
        
        for i, trade in enumerate(trades):
            if trade.get('type') == 'sell' and i > 0:
                prev_trade = trades[i-1]
                if prev_trade.get('type') == 'buy':
                    # Calcular lucro/prejuízo aproximado
                    buy_price = float(prev_trade.get('price', 0))
                    sell_price = float(trade.get('price', 0))
                    amount = float(prev_trade.get('amount', 0))
                    
                    if buy_price > 0:
                        profit = (sell_price - buy_price) * (amount / buy_price)
                        total_profit += profit
                        if profit > 0:
                            profitable_trades += 1
        
        self.stats['total_profit'] = total_profit
        if self.stats['trades_today'] > 0:
            self.stats['win_rate'] = (profitable_trades / (self.stats['trades_today'] / 2)) * 100
    
    def display_header(self):
        """Exibe cabeçalho do dashboard"""
        now = datetime.now()
        print("🤖 AI TRADING AGENT - MONITOR EM TEMPO REAL")
        print("=" * 70)
        print(f"⏰ {now.strftime('%Y-%m-%d %H:%M:%S')} | Atualização automática a cada 5s")
        print("=" * 70)
    
    def display_system_status(self, status: Dict):
        """Exibe status do sistema"""
        print("\n🔧 STATUS DO SISTEMA")
        print("-" * 30)
        
        if status.get('status') == 'online':
            print("🟢 Sistema: ONLINE")
            print(f"🏦 Exchange: {'✅ Conectada' if status.get('exchange_connected') else '❌ Desconectada'}")
            print(f"📊 Símbolo: {status.get('default_symbol', 'N/A')}")
            print(f"🧪 Testnet: {'Não' if not status.get('testnet_mode') else 'Sim'}")
        else:
            print("🔴 Sistema: OFFLINE")
            print("⚠️  Backend não está respondendo")
    
    def display_market_data(self, market: Dict):
        """Exibe dados do mercado"""
        print("\n📈 DADOS DO MERCADO")
        print("-" * 30)
        
        if market:
            price = float(market.get('price', 0))
            change_24h = float(market.get('change_24h', 0))
            volume = float(market.get('volume', 0))
            
            change_symbol = "📈" if change_24h >= 0 else "📉"
            print(f"💰 Preço: ${price:.6f}")
            print(f"{change_symbol} Variação 24h: {change_24h:+.2f}%")
            print(f"📊 Volume 24h: {volume:,.0f}")
        else:
            print("❌ Dados não disponíveis")
    
    def display_agent_stats(self):
        """Exibe estatísticas do agente"""
        print("\n🤖 ESTATÍSTICAS DO AGENTE")
        print("-" * 30)
        print(f"📊 Trades Hoje: {self.stats['trades_today']}")
        print(f"💰 P&L Estimado: ${self.stats['total_profit']:+.2f}")
        print(f"📈 Taxa de Acerto: {self.stats['win_rate']:.1f}%")
        
        if self.stats['current_position']:
            print(f"🎯 Posição Atual: {self.stats['current_position']}")
        else:
            print("🎯 Posição Atual: Nenhuma")
    
    def display_recent_trades(self, trades: List[Dict]):
        """Exibe trades recentes"""
        print("\n💼 TRADES RECENTES (HOJE)")
        print("-" * 50)
        
        if trades:
            for trade in trades[-5:]:  # Últimos 5 trades
                timestamp = trade.get('timestamp', '')
                trade_type = trade.get('type', 'N/A')
                symbol = trade.get('symbol', 'N/A')
                price = float(trade.get('price', 0))
                amount = float(trade.get('amount', 0))
                
                try:
                    time_str = datetime.fromisoformat(timestamp.replace('Z', '')).strftime('%H:%M:%S')
                except:
                    time_str = timestamp[:8] if len(timestamp) >= 8 else 'N/A'
                
                action_symbol = "🟢" if trade_type.lower() == 'buy' else "🔴"
                print(f"{action_symbol} {time_str} | {trade_type.upper()} {amount:.2f} @ ${price:.6f}")
        else:
            print("📭 Nenhum trade hoje")
    
    def display_recent_logs(self):
        """Exibe logs recentes"""
        print("\n📋 LOGS RECENTES")
        print("-" * 50)
        
        logs = self.read_recent_logs(5)
        if logs:
            for log in logs:
                # Limitar tamanho da linha
                clean_log = log.strip()
                if len(clean_log) > 70:
                    clean_log = clean_log[:67] + "..."
                print(f"📝 {clean_log}")
        else:
            print("📭 Nenhum log encontrado")
    
    def display_controls(self):
        """Exibe controles disponíveis"""
        print("\n🎮 CONTROLES")
        print("-" * 20)
        print("⏹️  Ctrl+C: Parar monitor")
        print("🔄 Auto-refresh: 5 segundos")
    
    def update_display(self):
        """Atualiza todo o dashboard"""
        self.clear_screen()
        
        # Cabeçalho
        self.display_header()
        
        # Status do sistema
        system_status = self.get_system_status()
        self.display_system_status(system_status)
        
        # Dados do mercado
        market_data = self.get_market_data()
        self.display_market_data(market_data)
        
        # Trades recentes
        recent_trades = self.get_recent_trades()
        self.calculate_stats(recent_trades)
        
        # Estatísticas do agente
        self.display_agent_stats()
        
        # Trades recentes
        self.display_recent_trades(recent_trades)
        
        # Logs recentes
        self.display_recent_logs()
        
        # Controles
        self.display_controls()
    
    def start_monitoring(self):
        """Inicia o monitoramento"""
        self.is_monitoring = True
        print("🚀 Iniciando monitor do AI Trading Agent...")
        print("⏳ Pressione Ctrl+C para parar")
        time.sleep(2)
        
        try:
            while self.is_monitoring:
                self.update_display()
                time.sleep(5)  # Atualiza a cada 5 segundos
                
        except KeyboardInterrupt:
            self.clear_screen()
            print("🛑 Monitor parado pelo usuário")
        except Exception as e:
            print(f"❌ Erro no monitor: {e}")
        finally:
            self.is_monitoring = False

def main():
    """Função principal"""
    monitor = AgentMonitor()
    
    print("🤖 AI Trading Agent Monitor")
    print("=" * 40)
    print("Este monitor mostra o status em tempo real do agente")
    print("Certifique-se de que o backend está rodando")
    print("\nPressione Enter para continuar...")
    input()
    
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
