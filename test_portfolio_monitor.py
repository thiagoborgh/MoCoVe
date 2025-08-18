#!/usr/bin/env python3
"""
Teste do Sistema de Monitoramento de Performance do Portfólio
"""

import requests
import time
from portfolio_monitor import PortfolioMonitor, PortfolioPosition

def test_portfolio_monitor():
    """Testa as funcionalidades do Portfolio Monitor"""
    print("🧪 === TESTE DO PORTFOLIO MONITOR ===\n")
    
    # Criar instância do monitor
    monitor = PortfolioMonitor()
    
    # 1. Teste de adição de posições manualmente
    print("1️⃣ Testando adição de posições...")
    monitor.add_position("DOGEUSDT", 0.08, 125.0, "2025-08-18T10:00:00")
    monitor.add_position("BTCUSDT", 65000.0, 0.00015, "2025-08-18T11:00:00")
    monitor.add_position("ETHUSDT", 2500.0, 0.004, "2025-08-18T12:00:00")
    print("✅ Posições adicionadas\n")
    
    # 2. Teste de atualização de preços
    print("2️⃣ Testando atualização de preços...")
    monitor.update_prices()
    print("✅ Preços atualizados\n")
    
    # 3. Teste de performance
    print("3️⃣ Testando cálculo de performance...")
    portfolio = monitor.get_portfolio_performance()
    
    print(f"📊 Posições: {portfolio['total_positions']}")
    print(f"📊 Total investido: ${portfolio['total_invested']:.2f}")
    print(f"📊 Valor atual: ${portfolio['total_current_value']:.2f}")
    print(f"📊 P&L: ${portfolio['total_pnl']:.2f} ({portfolio['portfolio_performance_pct']:+.2f}%)")
    
    if portfolio['positions']:
        print("\n📊 Performance por posição:")
        for pos in portfolio['positions']:
            status_emoji = {
                'excellent': '🚀',
                'good': '📈',
                'positive': '✅',
                'slight_loss': '⚠️',
                'loss': '📉',
                'heavy_loss': '🚨'
            }.get(pos['status'], '❓')
            
            print(f"  {status_emoji} {pos['symbol']}: {pos['performance_pct']:+.2f}% | "
                  f"${pos['pnl_usd']:+.2f} | {pos['days_held']} dias")
    
    print("✅ Performance calculada\n")
    
    # 4. Teste de alertas
    print("4️⃣ Testando sistema de alertas...")
    alerts = monitor.check_alerts()
    if alerts:
        for alert in alerts:
            print(f"🚨 {alert['message']}")
    else:
        print("ℹ️ Nenhum alerta ativo")
    print("✅ Alertas verificados\n")
    
    # 5. Teste da API
    print("5️⃣ Testando API backend...")
    try:
        response = requests.get("http://localhost:5000/api/portfolio/performance", timeout=5)
        if response.status_code == 200:
            api_data = response.json()
            print(f"✅ API respondeu: {api_data['success']}")
            if api_data['success']:
                api_portfolio = api_data['portfolio']
                print(f"📊 API - Posições: {api_portfolio['total_positions']}")
                print(f"📊 API - P&L: ${api_portfolio['total_pnl']:.2f}")
            else:
                print(f"⚠️ API erro: {api_data.get('error', 'Desconhecido')}")
        else:
            print(f"❌ API erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao testar API: {e}")
    
    print("\n🧪 === TESTE CONCLUÍDO ===")

def test_position_class():
    """Testa a classe PortfolioPosition individualmente"""
    print("\n🧪 === TESTE DA CLASSE POSITION ===\n")
    
    # Criar posição de teste
    position = PortfolioPosition(
        symbol="TESTUSDT",
        buy_price=1.0,
        quantity=100.0,
        buy_date="2025-08-18T10:00:00"
    )
    
    # Testar diferentes cenários de preço
    scenarios = [
        (1.15, "Alta de 15% - Excelente"),
        (1.08, "Alta de 8% - Boa"),
        (1.02, "Alta de 2% - Positiva"),
        (0.98, "Queda de 2% - Pequena perda"),
        (0.92, "Queda de 8% - Perda"),
        (0.85, "Queda de 15% - Perda pesada")
    ]
    
    for current_price, description in scenarios:
        position.update_current_price(current_price)
        perf = position.get_performance()
        
        status_emoji = {
            'excellent': '🚀',
            'good': '📈',
            'positive': '✅',
            'slight_loss': '⚠️',
            'loss': '📉',
            'heavy_loss': '🚨'
        }.get(perf['status'], '❓')
        
        print(f"{status_emoji} {description}: {perf['performance_pct']:+.2f}% | ${perf['pnl_usd']:+.2f}")
    
    print("✅ Cenários testados\n")

def simulate_real_trading():
    """Simula um cenário real de trading"""
    print("🎮 === SIMULAÇÃO DE TRADING REAL ===\n")
    
    monitor = PortfolioMonitor()
    
    # Simular compras em momentos diferentes
    trades = [
        ("DOGEUSDT", 0.08, 125.0, "2025-08-17T09:00:00"),
        ("SHIBUSDT", 0.000025, 200000.0, "2025-08-17T14:30:00"),
        ("PEPEUSDT", 0.000012, 416666.67, "2025-08-18T08:15:00"),
    ]
    
    print("📝 Simulando compras...")
    for symbol, price, quantity, date in trades:
        monitor.add_position(symbol, price, quantity, date)
        print(f"  ✅ Compra: {quantity:.2f} {symbol} @ ${price:.8f}")
    
    print("\n⏱️ Simulando passagem de tempo e mudanças de preço...")
    time.sleep(2)
    
    # Atualizar preços (vai buscar preços reais da API)
    monitor.update_prices()
    
    # Mostrar resultado
    portfolio = monitor.get_portfolio_performance()
    print(f"\n📊 RESULTADO DA SIMULAÇÃO:")
    print(f"Total investido: ${portfolio['total_invested']:.2f}")
    print(f"Valor atual: ${portfolio['total_current_value']:.2f}")
    print(f"P&L Total: ${portfolio['total_pnl']:.2f} ({portfolio['portfolio_performance_pct']:+.2f}%)")
    
    # Verificar alertas
    alerts = monitor.check_alerts()
    if alerts:
        print(f"\n🚨 ALERTAS ATIVOS:")
        for alert in alerts:
            print(f"  {alert['message']} - {alert['recommendation']}")
    
    print("\n🎮 === SIMULAÇÃO CONCLUÍDA ===")

if __name__ == "__main__":
    # Executar todos os testes
    test_position_class()
    test_portfolio_monitor()
    
    # Perguntar se quer simular trading
    response = input("\n❓ Executar simulação de trading real? (s/n): ")
    if response.lower() in ['s', 'sim', 'y', 'yes']:
        simulate_real_trading()
    
    print("\n🏁 Todos os testes concluídos!")