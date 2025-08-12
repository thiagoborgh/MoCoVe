#!/usr/bin/env python3
"""
Debug das rotas Flask
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar o app
from backend.app_real import app

def list_routes():
    """Listar todas as rotas registradas"""
    print("🔍 ROTAS REGISTRADAS NO FLASK:")
    print("=" * 60)
    
    for rule in app.url_map.iter_rules():
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"{methods:8} {rule.rule}")
    
    print("=" * 60)
    
    # Verificar especificamente nossa rota
    activate_routes = [rule for rule in app.url_map.iter_rules() if 'activate' in rule.rule]
    print(f"\n🎯 ROTAS DE ATIVAÇÃO ({len(activate_routes)}):")
    for route in activate_routes:
        methods = ', '.join(sorted(route.methods - {'HEAD', 'OPTIONS'}))
        print(f"   {methods:8} {route.rule}")

if __name__ == "__main__":
    list_routes()
