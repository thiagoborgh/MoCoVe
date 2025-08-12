#!/usr/bin/env python3
"""
Demo Script - MoCoVe AI Trading System com Watchlist Robusta
Script de demonstração das funcionalidades da watchlist
"""

import asyncio
import requests
import json
import time
from datetime import datetime

# Configuração da API
API_BASE = "http://localhost:5000/api"

def make_request(endpoint, method="GET", data=None):
    """Fazer requisição para API"""
    try:
        url = f"{API_BASE}{endpoint}"
        
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def print_section(title):
    """Imprimir seção formatada"""
    print("\n" + "="*60)
    print(f"📊 {title}")
    print("="*60)

def test_watchlist_summary():
    """Testar resumo da watchlist"""
    print_section("RESUMO DA WATCHLIST")
    
    result = make_request("/watchlist/summary")
    if result and result.get('success'):
        summary = result['summary']
        
        print(f"📈 Total de Moedas: {summary['total_coins']}")
        print(f"🚀 Habilitadas para Trading: {summary['trading_enabled']}")
        print(f"✅ Performers Positivos: {summary['price_stats']['positive_performers']}")
        print(f"❌ Performers Negativos: {summary['price_stats']['negative_performers']}")
        print(f"📊 Variação Média 24h: {summary['price_stats']['avg_change_24h']:.2%}")
        
        print("\n🏷️ Distribuição por Tier:")
        for tier, count in summary['tier_distribution'].items():
            print(f"   • {tier}: {count} moedas")
            
        return True
    return False

def test_watchlist_coins():
    """Testar listagem de moedas"""
    print_section("MOEDAS DA WATCHLIST")
    
    result = make_request("/watchlist/coins")
    if result and result.get('success'):
        coins = result['coins']
        
        print(f"📋 Total: {len(coins)} moedas carregadas\n")
        
        # Mostrar algumas moedas por tier
        tiers = {}
        for symbol, coin in coins.items():
            tier = coin.get('tier', 'unknown')
            if tier not in tiers:
                tiers[tier] = []
            tiers[tier].append((symbol, coin))
        
        for tier, tier_coins in tiers.items():
            print(f"🎯 {tier.upper()}:")
            for symbol, coin in tier_coins[:3]:  # Mostrar apenas 3
                status = "🟢" if coin.get('trading_enabled') else "🔴"
                print(f"   {status} {symbol} - {coin['name']}")
            if len(tier_coins) > 3:
                print(f"   ... e mais {len(tier_coins) - 3} moedas")
            print()
            
        return True
    return False

def test_top_performers():
    """Testar top performers"""
    print_section("TOP PERFORMERS")
    
    result = make_request("/watchlist/top-performers?limit=10")
    if result and result.get('success'):
        performers = result['top_performers']
        
        if performers:
            print("🏆 Top 10 Performers (24h):\n")
            for i, coin in enumerate(performers, 1):
                change = coin.get('change_24h', 0) * 100
                price = coin.get('price', 0)
                volume = coin.get('volume_24h', 0) / 1000000  # Em milhões
                
                emoji = "🚀" if change > 10 else "📈" if change > 0 else "📉"
                
                print(f"{i:2}. {emoji} {coin['symbol']:8} | "
                      f"{change:+6.2f}% | "
                      f"${price:.8f} | "
                      f"Vol: ${volume:.1f}M")
        else:
            print("📊 Nenhum dado de performance disponível ainda")
            
        return True
    return False

def test_alerts():
    """Testar alertas"""
    print_section("ALERTAS RECENTES")
    
    result = make_request("/watchlist/alerts?limit=10")
    if result and result.get('success'):
        alerts = result['alerts']
        
        if alerts:
            print("🚨 Últimos alertas:\n")
            for alert in alerts:
                timestamp = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
                time_str = timestamp.strftime('%H:%M:%S')
                
                emoji = {
                    'PUMP': '🚀',
                    'DUMP': '📉',
                    'VOLUME_SPIKE': '📊'
                }.get(alert['type'], '⚠️')
                
                print(f"{emoji} {time_str} | {alert['symbol']:8} | {alert['message']}")
        else:
            print("📊 Nenhum alerta recente")
            
        return True
    return False

def test_tier_filtering():
    """Testar filtros por tier"""
    print_section("FILTROS POR TIER")
    
    tiers_to_test = ['tier1', 'tier2', 'trending', 'alt_defi']
    
    for tier in tiers_to_test:
        result = make_request(f"/watchlist/coins/tier/{tier}")
        if result and result.get('success'):
            coins = result['coins']
            print(f"🎯 {tier.upper()}: {len(coins)} moedas")
            
            if coins:
                # Mostrar 2 exemplos
                for coin in coins[:2]:
                    print(f"   • {coin['symbol']} - {coin['name']}")
                if len(coins) > 2:
                    print(f"   ... e mais {len(coins) - 2}")
        print()

def test_trading_coins():
    """Testar moedas habilitadas para trading"""
    print_section("MOEDAS HABILITADAS PARA TRADING")
    
    result = make_request("/watchlist/coins/trading")
    if result and result.get('success'):
        trading_coins = result['trading_coins']
        
        print(f"🚀 {len(trading_coins)} moedas habilitadas para trading:\n")
        
        for coin in trading_coins:
            price = coin.get('price')
            change = coin.get('change_24h')
            
            if price and change is not None:
                change_str = f"{change*100:+.2f}%"
                price_str = f"${price:.8f}"
            else:
                change_str = "N/A"
                price_str = "N/A"
                
            print(f"✅ {coin['symbol']:10} | {change_str:8} | {price_str}")
            
        return True
    return False

def test_update_prices():
    """Testar atualização de preços"""
    print_section("ATUALIZAÇÃO DE PREÇOS")
    
    print("🔄 Solicitando atualização de preços...")
    
    result = make_request("/watchlist/update-prices", method="POST")
    if result and result.get('success'):
        print(f"✅ {result['message']}")
        
        if result.get('updated_coins'):
            print(f"📊 Moedas atualizadas: {len(result['updated_coins'])}")
            print("Exemplos:", ", ".join(result['updated_coins'][:5]))
        
        if result.get('errors'):
            print(f"⚠️ Erros: {len(result['errors'])}")
            
        return True
    return False

async def run_demo():
    """Executar demonstração completa"""
    print("🎯 MoCoVe AI Trading System - Demo da Watchlist")
    print("🚀 Sistema de Monitoramento Robusto de Criptomoedas")
    print("⏰", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # Lista de testes
    tests = [
        ("Resumo da Watchlist", test_watchlist_summary),
        ("Listagem de Moedas", test_watchlist_coins),
        ("Top Performers", test_top_performers),
        ("Alertas Recentes", test_alerts),
        ("Filtros por Tier", test_tier_filtering),
        ("Moedas para Trading", test_trading_coins),
        ("Atualização de Preços", test_update_prices),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Executando: {test_name}")
            success = test_func()
            results[test_name] = "✅ OK" if success else "❌ FALHA"
            time.sleep(1)  # Pequena pausa entre testes
        except Exception as e:
            results[test_name] = f"❌ ERRO: {e}"
    
    # Relatório final
    print_section("RELATÓRIO FINAL")
    
    for test_name, result in results.items():
        print(f"{result} | {test_name}")
    
    success_count = sum(1 for r in results.values() if "✅" in r)
    total_tests = len(results)
    
    print(f"\n📊 Resumo: {success_count}/{total_tests} testes bem-sucedidos")
    print(f"🎯 Taxa de Sucesso: {success_count/total_tests*100:.1f}%")
    
    if success_count == total_tests:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("🚀 Sistema de Watchlist totalmente funcional!")
    else:
        print("\n⚠️ Alguns testes falharam. Verifique a configuração.")

def main():
    """Função principal"""
    try:
        # Verificar se o servidor está rodando
        result = make_request("/watchlist/summary")
        if not result:
            print("❌ Erro: Servidor não está respondendo em http://localhost:5000")
            print("🔧 Certifique-se de que o backend está rodando:")
            print("   python backend/app_real.py")
            return
        
        # Executar demo
        asyncio.run(run_demo())
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro na execução: {e}")

if __name__ == "__main__":
    main()
