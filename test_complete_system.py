#!/usr/bin/env python3
"""
Sistema Completo de Teste - MoCoVe
Teste integrado de todas as funcionalidades implementadas
"""

import requests
import json
import time
from datetime import datetime

# Configuração
API_BASE = "http://localhost:5000/api"

def print_header(title):
    print("\n" + "="*70)
    print(f"🚀 {title}")
    print("="*70)

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

def test_system_status():
    """Testar status do sistema"""
    print_header("TESTE DO STATUS DO SISTEMA")
    
    result = make_request("/system/status")
    if result and result.get('success'):
        status = result['status']
        
        print(f"✅ Timestamp: {status['timestamp']}")
        print(f"🖥️  Backend: {'✅ Online' if status['backend_running'] else '❌ Offline'}")
        print(f"🔗 Binance: {'✅ Conectado' if status['binance_connected'] else '❌ Desconectado'}")
        print(f"🤖 AI Agent: {'✅ Ativo' if status['ai_agent_active'] else '❌ Inativo'}")
        print(f"📋 Watchlist: {'✅ Carregada' if status['watchlist_loaded'] else '❌ Erro'}")
        print(f"💰 Saldo: {status['balance_updated']}")
        print(f"📊 Mercado: {'✅ Atualizado' if status['market_data_fresh'] else '❌ Desatualizado'}")
        
        if status['warnings']:
            print(f"⚠️  Avisos: {', '.join(status['warnings'])}")
        
        print(f"🔢 Erros: {status['error_count']}")
        
        return True
    return False

def test_binance_connection():
    """Testar conexão Binance"""
    print_header("TESTE DA CONEXÃO BINANCE")
    
    result = make_request("/system/test-binance", method="POST")
    if result and result.get('success'):
        binance = result['binance']
        
        print(f"🔗 Conectado: {'✅ Sim' if binance['connected'] else '❌ Não'}")
        print(f"🔧 Tipo: {binance.get('account_type', 'N/A')}")
        print(f"📝 Permissões: {binance.get('permissions', [])}")
        print(f"💱 Pode Tradear: {'✅ Sim' if binance.get('can_trade') else '❌ Não'}")
        
        if binance.get('error'):
            print(f"❌ Erro: {binance['error']}")
        
        return binance['connected']
    return False

def test_watchlist():
    """Testar watchlist"""
    print_header("TESTE DA WATCHLIST")
    
    # Testar resumo
    result = make_request("/watchlist/summary")
    if result and result.get('success'):
        summary = result['summary']
        
        print(f"📊 Total de Moedas: {summary['total_coins']}")
        print(f"🚀 Trading Habilitado: {summary['trading_enabled']}")
        print(f"📈 Performers Positivos: {summary['price_stats']['positive_performers']}")
        print(f"📉 Performers Negativos: {summary['price_stats']['negative_performers']}")
        
        print("\n🏷️ Distribuição por Tier:")
        for tier, count in summary['tier_distribution'].items():
            print(f"   • {tier}: {count} moedas")
    
    # Testar top performers
    result = make_request("/watchlist/top-performers?limit=5")
    if result and result.get('success'):
        performers = result['top_performers']
        
        print(f"\n🏆 Top 5 Performers:")
        for i, coin in enumerate(performers, 1):
            change = coin.get('change_24h', 0) * 100
            print(f"   {i}. {coin['symbol']}: {change:+.2f}%")
    
    return True

def test_balance_update():
    """Testar atualização de saldo"""
    print_header("TESTE DE ATUALIZAÇÃO DE SALDO")
    
    result = make_request("/system/update-balance", method="POST")
    if result and result.get('success'):
        balance = result['balance']
        
        print(f"💰 Total USD: ${balance.get('total_usd', 0):.2f}")
        
        if balance.get('balances'):
            print("\n💳 Principais Saldos:")
            for asset, data in list(balance['balances'].items())[:5]:
                print(f"   • {asset}: {data['total']:.8f} (${data.get('usd_value', 0):.2f})")
        
        return True
    return False

def test_market_data_update():
    """Testar atualização de dados de mercado"""
    print_header("TESTE DE ATUALIZAÇÃO DE MERCADO")
    
    result = make_request("/system/update-market-data", method="POST")
    if result and result.get('success'):
        market = result['market_data']
        
        print(f"📊 Moedas Atualizadas: {market.get('updated_coins', 0)}")
        print(f"❌ Erros: {len(market.get('errors', []))}")
        
        if market.get('updated_coins'):
            print(f"✅ Exemplos: {', '.join(market.get('updated_coins', [])[:5])}")
        
        return True
    return False

def test_sentiment_update():
    """Testar atualização de sentimento"""
    print_header("TESTE DE SENTIMENTO SOCIAL")
    
    result = make_request("/system/update-sentiment", method="POST")
    if result and result.get('success'):
        sentiment = result['sentiment']
        
        print(f"📱 Símbolos Atualizados: {sentiment.get('updated_symbols', 0)}")
        
        # Obter dados de sentimento
        result = make_request("/system/sentiment")
        if result and result.get('success'):
            sentiments = result['sentiment']['sentiments']
            
            print(f"\n📊 Sentimentos Atuais:")
            for s in sentiments[:5]:
                sentiment_emoji = "😊" if s['avg_sentiment'] > 0.3 else "😐" if s['avg_sentiment'] > -0.3 else "😞"
                print(f"   {sentiment_emoji} {s['symbol']}: {s['avg_sentiment']:.2f} ({s['total_mentions']} menções)")
        
        return True
    return False

def test_ai_agent_control():
    """Testar controle do AI Agent"""
    print_header("TESTE DE CONTROLE DO AI AGENT")
    
    # Verificar status atual
    status_result = make_request("/system/status")
    if status_result and status_result.get('success'):
        ai_active = status_result['status']['ai_agent_active']
        print(f"🤖 AI Agent Status Atual: {'✅ Ativo' if ai_active else '❌ Inativo'}")
        
        if not ai_active:
            # Tentar iniciar
            print("🚀 Tentando iniciar AI Agent...")
            start_result = make_request("/system/start-ai-agent", method="POST")
            if start_result and start_result.get('success'):
                print("✅ AI Agent iniciado com sucesso!")
                time.sleep(2)
                
                # Verificar novamente
                status_result = make_request("/system/status")
                if status_result and status_result.get('success'):
                    ai_active = status_result['status']['ai_agent_active']
                    print(f"🔄 Novo Status: {'✅ Ativo' if ai_active else '❌ Ainda Inativo'}")
            else:
                print("❌ Falha ao iniciar AI Agent")
        
        return True
    return False

def test_alerts():
    """Testar sistema de alertas"""
    print_header("TESTE DO SISTEMA DE ALERTAS")
    
    result = make_request("/watchlist/alerts?limit=10")
    if result and result.get('success'):
        alerts = result['alerts']
        
        print(f"🚨 Total de Alertas: {len(alerts)}")
        
        if alerts:
            print("\n📋 Alertas Recentes:")
            for alert in alerts[:5]:
                timestamp = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
                time_str = timestamp.strftime('%H:%M:%S')
                
                emoji = {
                    'PUMP': '🚀',
                    'DUMP': '📉',
                    'VOLUME_SPIKE': '📊'
                }.get(alert['type'], '⚠️')
                
                print(f"   {emoji} {time_str} | {alert['symbol']} | {alert['message']}")
        else:
            print("📊 Nenhum alerta recente encontrado")
        
        return True
    return False

def run_comprehensive_test():
    """Executar teste abrangente"""
    print("🎯 MoCoVe Sistema Completo - Teste Integrado")
    print("🕐", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    tests = [
        ("Status do Sistema", test_system_status),
        ("Conexão Binance", test_binance_connection),
        ("Watchlist", test_watchlist),
        ("Atualização de Saldo", test_balance_update),
        ("Dados de Mercado", test_market_data_update),
        ("Sentimento Social", test_sentiment_update),
        ("Controle AI Agent", test_ai_agent_control),
        ("Log do Agente Robusto IA", test_robust_ai_log),
        ("Sistema de Alertas", test_alerts),
    ]


# Novo teste: Verificar log do agente robusto de IA
def test_robust_ai_log():
    """Testar endpoint de log do agente robusto de IA"""
    print_header("TESTE DO LOG DO AGENTE ROBUSTO IA")
    result = make_request("/ai-robust-log")
    if result and 'log' in result:
        log_lines = result['log'].split('\n')
        print(f"🧠 Últimas linhas do log do agente robusto:")
        for line in log_lines[-5:]:
            print(f"   {line}")
        return True
    else:
        print("❌ Não foi possível obter o log do agente robusto.")
        return False
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Executando: {test_name}")
            success = test_func()
            results[test_name] = "✅ PASSOU" if success else "❌ FALHOU"
            time.sleep(1)  # Pausa entre testes
        except Exception as e:
            results[test_name] = f"❌ ERRO: {e}"
    
    # Relatório final
    print_header("RELATÓRIO FINAL DE TESTES")
    
    for test_name, result in results.items():
        print(f"{result} | {test_name}")
    
    success_count = sum(1 for r in results.values() if "✅" in r)
    total_tests = len(results)
    
    print(f"\n📊 Resumo: {success_count}/{total_tests} testes bem-sucedidos")
    print(f"🎯 Taxa de Sucesso: {success_count/total_tests*100:.1f}%")
    
    if success_count == total_tests:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("🚀 Sistema MoCoVe 100% funcional!")
    elif success_count >= total_tests * 0.8:
        print("\n✅ Sistema majoritariamente funcional!")
        print("⚠️ Alguns componentes precisam de atenção")
    else:
        print("\n⚠️ Sistema com problemas significativos")
        print("🔧 Verificação e correção necessárias")

if __name__ == "__main__":
    try:
        # Verificar conectividade básica
        test_result = make_request("/system/status")
        if not test_result:
            print("❌ ERRO: Backend não está respondendo!")
            print("🔧 Certifique-se de que o servidor está rodando em http://localhost:5000")
            print("   Comando: python backend/app_real.py")
            exit(1)
        
        # Executar testes
        run_comprehensive_test()
        
    except KeyboardInterrupt:
        print("\n⏹️ Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
