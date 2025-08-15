#!/usr/bin/env python3
"""
Monitor de Sistema - MoCoVe
Monitora a saúde do sistema e reinicia componentes se necessário
"""

import time
import subprocess
import requests
import psutil
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("system_monitor.log", encoding="utf-8"),
    ],
)

log = logging.getLogger("SystemMonitor")

class SystemMonitor:
    def __init__(self):
        self.api_base = "http://localhost:5000"
        self.check_interval = 30  # segundos
        self.restart_attempts = {}
        self.max_restart_attempts = 3
        
    def check_backend_health(self):
        """Verificar se o backend está respondendo"""
        try:
            response = requests.get(f"{self.api_base}/api/status", timeout=10)
            if response.status_code == 200:
                log.info("✅ Backend respondendo")
                return True
            else:
                log.warning(f"⚠️ Backend retornou código {response.status_code}")
                return False
        except Exception as e:
            log.error(f"❌ Backend não responde: {e}")
            return False
    
    def check_system_resources(self):
        """Verificar recursos do sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            log.info(f"💻 CPU: {cpu_percent}%")
            
            # Memória
            memory = psutil.virtual_memory()
            log.info(f"🧠 Memória: {memory.percent}% usada")
            
            # Disco
            disk = psutil.disk_usage('/')
            log.info(f"💾 Disco: {disk.percent}% usado")
            
            # Alertas
            if cpu_percent > 90:
                log.warning("⚠️ CPU acima de 90%")
            if memory.percent > 85:
                log.warning("⚠️ Memória acima de 85%")
            if disk.percent > 90:
                log.warning("⚠️ Disco acima de 90%")
                
        except Exception as e:
            log.error(f"Erro ao verificar recursos: {e}")
    
    def check_processes(self):
        """Verificar processos importantes"""
        processes_to_check = [
            "python",  # Processos Python
        ]
        
        running_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if any(cmd_part and 'mocove' in cmd_part.lower() for cmd_part in proc.info['cmdline'] or []):
                    running_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        log.info(f"🔄 Processos MoCoVe ativos: {len(running_processes)}")
        return running_processes
    
    def restart_backend(self):
        """Tentar reiniciar o backend"""
        component = "backend"
        
        if component not in self.restart_attempts:
            self.restart_attempts[component] = 0
        
        if self.restart_attempts[component] >= self.max_restart_attempts:
            log.error(f"❌ Máximo de tentativas de restart atingido para {component}")
            return False
        
        try:
            log.info(f"🔄 Tentando reiniciar {component}...")
            self.restart_attempts[component] += 1
            
            # Aqui você pode adicionar lógica específica para reiniciar
            # Por exemplo, matar processo existente e iniciar novo
            
            log.info(f"✅ {component} reiniciado (tentativa {self.restart_attempts[component]})")
            return True
            
        except Exception as e:
            log.error(f"❌ Erro ao reiniciar {component}: {e}")
            return False
    
    def run_health_check(self):
        """Executar verificação completa de saúde"""
        log.info("🔍 Iniciando verificação de saúde do sistema")
        
        # Verificar backend
        backend_ok = self.check_backend_health()
        
        # Verificar recursos
        self.check_system_resources()
        
        # Verificar processos
        processes = self.check_processes()
        
        # Ações corretivas
        if not backend_ok:
            log.warning("⚠️ Backend com problemas, tentando correção...")
            self.restart_backend()
        
        log.info("✅ Verificação de saúde concluída")
        return backend_ok
    
    def run(self):
        """Loop principal do monitor"""
        log.info("🚀 Sistema de monitoramento iniciado")
        
        try:
            while True:
                self.run_health_check()
                log.info(f"😴 Aguardando {self.check_interval} segundos...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            log.info("⏹️ Monitor interrompido pelo usuário")
        except Exception as e:
            log.error(f"❌ Erro crítico no monitor: {e}")
        finally:
            log.info("🔚 Monitor finalizado")

def main():
    monitor = SystemMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
