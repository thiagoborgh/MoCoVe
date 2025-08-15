#!/usr/bin/env python3
"""
AI Trading Agent - Versão Robusta
"""

import time
import requests
import logging
from datetime import datetime

# Setup básico de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ai_trading_agent_robust.log", encoding="utf-8"),
    ],
)

log = logging.getLogger("AITradingAgent")

class SimpleAgent:
    def __init__(self):
        self.api_base = "http://localhost:5000"
        self.is_running = True
        self.cycle_count = 0
        
    def get_market_data(self, symbol="DOGEUSDT"):
        """Obtém dados de mercado"""
        try:
            url = f"{self.api_base}/api/market_data"
            response = requests.get(url, params={"symbol": symbol}, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            log.error(f"Erro ao obter market data: {e}")
            return None
    
    def get_prices(self, symbol="DOGEUSDT", limit=60):
        """Obtém histórico de preços"""
        try:
            url = f"{self.api_base}/api/prices"
            response = requests.get(url, params={"symbol": symbol, "limit": limit}, timeout=5)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return data
            return data.get("prices", [])
        except Exception as e:
            log.error(f"Erro ao obter prices: {e}")
            return []
    
    def analyze_market(self, market_data, prices):
        """Análise simples de mercado"""
        if not market_data or not prices:
            return "hold", 0.0, "Dados insuficientes"
        
        current_price = float(market_data.get("price", 0))
        change_24h = float(market_data.get("change_24h", 0))
        
        # Lógica simples
        if change_24h > 2:
            return "buy", 0.6, f"Alta de 24h: {change_24h:.2f}%"
        elif change_24h < -2:
            return "sell", 0.6, f"Queda de 24h: {change_24h:.2f}%"
        else:
            return "hold", 0.3, f"Lateral: {change_24h:.2f}%"
    
    def run_cycle(self):
        """Executa um ciclo de análise"""
        self.cycle_count += 1
        log.info(f"=== CICLO {self.cycle_count} ===")
        
        try:
            # Obter dados
            market_data = self.get_market_data()
            if not market_data:
                log.warning("Falha ao obter dados de mercado")
                return
            
            prices = self.get_prices()
            
            # Análise
            action, confidence, reason = self.analyze_market(market_data, prices)
            
            # Log do resultado
            price = market_data.get("price", 0)
            log.info(f"Preço: ${price:.8f} | Ação: {action.upper()} | Confiança: {confidence:.2f} | Razão: {reason}")
            
            # Simulação de trade (modo teste)
            if action in ["buy", "sell"] and confidence > 0.5:
                log.info(f"[SIMULAÇÃO] {action.upper()} executado com confiança {confidence:.2f}")
            
        except Exception as e:
            log.error(f"Erro no ciclo {self.cycle_count}: {e}")
    
    def run(self):
        """Loop principal do agente"""
        log.info("=== AGENTE IA TRADING INICIADO ===")
        heartbeat_count = 0
        while True:
            try:
                self.is_running = True
                self.run_cycle()
                heartbeat_count += 1
                log.info(f"[HEARTBEAT] Agent ativo. Ciclo: {self.cycle_count} | Heartbeat: {heartbeat_count}")
                # Escreve arquivo de status para monitoramento externo
                with open("ai_agent_status.txt", "w", encoding="utf-8") as f:
                    # Formato compatível: 'ACTIVE - YYYY-MM-DD HH:MM:SS'
                    f.write(f"ACTIVE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                # Status a cada 10 ciclos
                if self.cycle_count % 10 == 0:
                    log.info(f"Status: {self.cycle_count} ciclos completados")
                # Aguardar próximo ciclo
                log.info("Aguardando 20 segundos...")
                time.sleep(20)
            except KeyboardInterrupt:
                log.info("Agente interrompido pelo usuário")
                # Marca como inativo
                with open("ai_agent_status.txt", "w", encoding="utf-8") as f:
                    f.write(f"AI_AGENT_STATUS=INACTIVE\nCICLO={self.cycle_count}\nHEARTBEAT={heartbeat_count}\nTIMESTAMP={datetime.now().isoformat()}\n")
                break
            except Exception as e:
                log.error(f"Erro crítico no loop principal: {e}")
                time.sleep(5)
        self.is_running = False
        log.info("=== AGENTE FINALIZADO ===")
        # Marca como inativo ao finalizar
        with open("ai_agent_status.txt", "w", encoding="utf-8") as f:
            f.write(f"AI_AGENT_STATUS=INACTIVE\nCICLO={self.cycle_count}\nHEARTBEAT={heartbeat_count}\nTIMESTAMP={datetime.now().isoformat()}\n")

def main():
    agent = SimpleAgent()
    agent.run()

if __name__ == "__main__":
    main()
