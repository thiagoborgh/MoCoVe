#!/usr/bin/env python3
"""
Configurador e Controlador do AI Trading Agent
Interface para configurar e monitorar o agente de IA
"""

import json
import os
from datetime import datetime
import requests

class AgentConfig:
    """Configurações do agente de trading"""
    
    def __init__(self):
        self.config_file = "ai_agent_config.json"
        self.default_config = {
            "trading_enabled": False,
            "symbol": "DOGEUSDT",
            "monitoring_interval": 30,
            "min_confidence": 0.7,
            "max_position_size": 50.0,
            "max_daily_trades": 10,
            "stop_loss_pct": 0.02,
            "take_profit_pct": 0.03,
            "min_trade_interval": 300,
            "risk_level": "conservative",  # conservative, moderate, aggressive
            "strategies_enabled": {
                "moving_averages": True,
                "rsi": True,
                "bollinger_bands": True,
                "trend_following": True,
                "volatility_filter": True
            },
            "notifications": {
                "trade_execution": True,
                "high_confidence_signals": True,
                "daily_summary": True
            }
        }
        self.load_config()
    
    def load_config(self):
        """Carrega configurações do arquivo"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                print("✅ Configurações carregadas")
            except Exception as e:
                print(f"❌ Erro ao carregar config: {e}")
                self.config = self.default_config.copy()
        else:
            self.config = self.default_config.copy()
            self.save_config()
    
    def save_config(self):
        """Salva configurações no arquivo"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print("✅ Configurações salvas")
        except Exception as e:
            print(f"❌ Erro ao salvar config: {e}")
    
    def set_risk_level(self, level: str):
        """Define nível de risco"""
        risk_profiles = {
            "conservative": {
                "min_confidence": 0.8,
                "max_position_size": 25.0,
                "max_daily_trades": 5,
                "stop_loss_pct": 0.015,
                "take_profit_pct": 0.02
            },
            "moderate": {
                "min_confidence": 0.7,
                "max_position_size": 50.0,
                "max_daily_trades": 10,
                "stop_loss_pct": 0.02,
                "take_profit_pct": 0.03
            },
            "aggressive": {
                "min_confidence": 0.6,
                "max_position_size": 100.0,
                "max_daily_trades": 20,
                "stop_loss_pct": 0.03,
                "take_profit_pct": 0.05
            }
        }
        
        if level in risk_profiles:
            self.config.update(risk_profiles[level])
            self.config["risk_level"] = level
            print(f"✅ Nível de risco definido para: {level}")
        else:
            print(f"❌ Nível de risco inválido: {level}")

class AgentController:
    """Controlador para o agente de IA"""
    
    def __init__(self):
        self.api_base = "http://localhost:5000"
        self.config = AgentConfig()
    
    def check_system_status(self):
        """Verifica se o sistema está pronto"""
        try:
            response = requests.get(f"{self.api_base}/api/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("🟢 Sistema Status:")
                print(f"   API: {'Online' if data.get('status') == 'online' else 'Offline'}")
                print(f"   Exchange: {'✅ Conectada' if data.get('exchange_connected') else '❌ Desconectada'}")
                print(f"   Testnet: {'Não' if not data.get('testnet_mode') else 'Sim'}")
                print(f"   Símbolo padrão: {data.get('default_symbol')}")
                return True
            else:
                print(f"❌ Sistema offline: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro ao verificar sistema: {e}")
            return False
    
    def get_account_balance(self):
        """Mostra saldos da conta"""
        try:
            response = requests.get(f"{self.api_base}/api/balance", timeout=10)
            if response.status_code == 200:
                balances = response.json()
                print("💰 Saldos da Conta:")
                for currency, amounts in balances.items():
                    if amounts['total'] > 0.001:
                        print(f"   {currency}: {amounts['total']:.6f} (livre: {amounts['free']:.6f})")
                return True
            else:
                print(f"❌ Erro ao obter saldos: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
    
    def show_current_config(self):
        """Mostra configuração atual"""
        print("\n⚙️  CONFIGURAÇÃO ATUAL DO AGENTE")
        print("=" * 50)
        print(f"🔄 Trading Habilitado: {'✅ SIM' if self.config.config['trading_enabled'] else '❌ NÃO'}")
        print(f"📊 Símbolo: {self.config.config['symbol']}")
        print(f"⏱️  Intervalo de Monitoramento: {self.config.config['monitoring_interval']}s")
        print(f"🎯 Confiança Mínima: {self.config.config['min_confidence']}")
        print(f"💰 Valor Máximo por Trade: ${self.config.config['max_position_size']}")
        print(f"📈 Trades Máximos por Dia: {self.config.config['max_daily_trades']}")
        print(f"🛡️  Stop Loss: {self.config.config['stop_loss_pct']*100:.1f}%")
        print(f"🎯 Take Profit: {self.config.config['take_profit_pct']*100:.1f}%")
        print(f"⚡ Nível de Risco: {self.config.config['risk_level'].upper()}")
        
        print(f"\n📊 Estratégias Habilitadas:")
        for strategy, enabled in self.config.config['strategies_enabled'].items():
            status = "✅" if enabled else "❌"
            print(f"   {status} {strategy.replace('_', ' ').title()}")
    
    def configure_agent(self):
        """Interface interativa para configurar o agente"""
        print("\n🔧 CONFIGURAÇÃO DO AI TRADING AGENT")
        print("=" * 50)
        
        while True:
            print(f"\n1. Habilitar/Desabilitar Trading")
            print(f"2. Definir Símbolo (atual: {self.config.config['symbol']})")
            print(f"3. Intervalo de Monitoramento (atual: {self.config.config['monitoring_interval']}s)")
            print(f"4. Confiança Mínima (atual: {self.config.config['min_confidence']})")
            print(f"5. Valor Máximo por Trade (atual: ${self.config.config['max_position_size']})")
            print(f"6. Nível de Risco (atual: {self.config.config['risk_level']})")
            print(f"7. Ver Configuração Completa")
            print(f"8. Salvar e Sair")
            
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == "1":
                enabled = input("Habilitar trading? (s/n): ").lower().startswith('s')
                self.config.config['trading_enabled'] = enabled
                print(f"✅ Trading {'habilitado' if enabled else 'desabilitado'}")
                
            elif choice == "2":
                symbol = input("Digite o símbolo (ex: DOGEUSDT, BTCUSDT): ").upper()
                if symbol:
                    self.config.config['symbol'] = symbol
                    print(f"✅ Símbolo definido: {symbol}")
                    
            elif choice == "3":
                try:
                    interval = int(input("Intervalo em segundos (mín: 10): "))
                    if interval >= 10:
                        self.config.config['monitoring_interval'] = interval
                        print(f"✅ Intervalo definido: {interval}s")
                    else:
                        print("❌ Intervalo deve ser pelo menos 10 segundos")
                except ValueError:
                    print("❌ Valor inválido")
                    
            elif choice == "4":
                try:
                    confidence = float(input("Confiança mínima (0.1 a 1.0): "))
                    if 0.1 <= confidence <= 1.0:
                        self.config.config['min_confidence'] = confidence
                        print(f"✅ Confiança mínima definida: {confidence}")
                    else:
                        print("❌ Confiança deve estar entre 0.1 e 1.0")
                except ValueError:
                    print("❌ Valor inválido")
                    
            elif choice == "5":
                try:
                    amount = float(input("Valor máximo por trade ($): "))
                    if amount > 0:
                        self.config.config['max_position_size'] = amount
                        print(f"✅ Valor máximo definido: ${amount}")
                    else:
                        print("❌ Valor deve ser positivo")
                except ValueError:
                    print("❌ Valor inválido")
                    
            elif choice == "6":
                print("\nNíveis de Risco:")
                print("1. Conservative (Baixo risco, poucos trades)")
                print("2. Moderate (Risco médio, balanced)")
                print("3. Aggressive (Alto risco, mais trades)")
                
                risk_choice = input("Escolha (1-3): ").strip()
                risk_map = {"1": "conservative", "2": "moderate", "3": "aggressive"}
                
                if risk_choice in risk_map:
                    self.config.set_risk_level(risk_map[risk_choice])
                else:
                    print("❌ Opção inválida")
                    
            elif choice == "7":
                self.show_current_config()
                
            elif choice == "8":
                self.config.save_config()
                break
                
            else:
                print("❌ Opção inválida")
    
    def show_safety_warnings(self):
        """Mostra avisos de segurança"""
        print("\n🚨 AVISOS IMPORTANTES DE SEGURANÇA")
        print("=" * 60)
        print("⚠️  Este agente fará TRADES REAIS com sua conta Binance")
        print("💰 Certifique-se de que entende os riscos envolvidos")
        print("📊 Comece com valores pequenos para testar")
        print("👀 Monitore o agente regularmente")
        print("🛑 Use Ctrl+C para parar a qualquer momento")
        print("💼 Defina limites de risco apropriados")
        print("🔒 Nunca deixe o agente rodando sem supervisão")
        print("=" * 60)

def main():
    """Menu principal"""
    controller = AgentController()
    
    print("🤖 AI TRADING AGENT - CONFIGURADOR")
    print("=" * 50)
    
    while True:
        print(f"\n1. Verificar Status do Sistema")
        print(f"2. Ver Saldos da Conta")
        print(f"3. Configurar Agente")
        print(f"4. Ver Configuração Atual")
        print(f"5. Avisos de Segurança")
        print(f"6. Iniciar Agente (python ai_trading_agent.py)")
        print(f"7. Sair")
        
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == "1":
            controller.check_system_status()
            
        elif choice == "2":
            controller.get_account_balance()
            
        elif choice == "3":
            controller.configure_agent()
            
        elif choice == "4":
            controller.show_current_config()
            
        elif choice == "5":
            controller.show_safety_warnings()
            
        elif choice == "6":
            print("\n🚀 Para iniciar o agente, execute:")
            print("   python ai_trading_agent.py")
            print("\n⚠️  Certifique-se de que:")
            print("   1. O backend está rodando")
            print("   2. A configuração está correta")
            print("   3. Você entende os riscos")
            
        elif choice == "7":
            print("👋 Até logo!")
            break
            
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main()
