#!/usr/bin/env python3
"""
Teste do Sistema de Trading - Verificar se está comprando e vendendo
"""

import json
import sqlite3
from datetime import datetime, timedelta
import os

def check_system_status():
    print('🔍 VERIFICANDO STATUS DO SISTEMA DE TRADING')
    print('=' * 50)

    # 1. Verificar se AI agent está rodando
    try:
        with open('ai_agent_status.txt', 'r') as f:
            status = f.read().strip()
        print(f'✅ AI Agent Status: {status}')
    except:
        print('❌ AI Agent status não encontrado')

    # 2. Verificar configuração de trading
    try:
        with open('ai_trading_config.json', 'r') as f:
            config = json.load(f)
        print(f'✅ Trading Mode: {config.get("trading_mode", "N/A")}')
        print(f'✅ Max Investment: {config.get("max_investment_per_trade", "N/A")} USDT')
        print(f'✅ Stop Loss: {config.get("stop_loss_percent", "N/A")}%')
        print(f'✅ Take Profit: {config.get("take_profit_percent", "N/A")}%')
        print(f'✅ Trading Enabled: {config.get("trading_enabled", "N/A")}')
    except Exception as e:
        print(f'❌ Erro ao ler configuração: {e}')

def check_binance_balance():
    print(f'\n💰 VERIFICANDO SALDO NA BINANCE:')
    try:
        from binance.client import Client
        from ai_trading_config import BINANCE_API_KEY, BINANCE_SECRET_KEY
        
        client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
        account = client.get_account()
        
        print("Saldos disponíveis:")
        for balance in account['balances']:
            if float(balance['free']) > 0 or float(balance['locked']) > 0:
                total = float(balance['free']) + float(balance['locked'])
                print(f'  {balance["asset"]}: {total:.6f} (Free: {balance["free"]}, Locked: {balance["locked"]})')
        
        return True
    except Exception as e:
        print(f'❌ Erro ao verificar saldo: {e}')
        return False

def check_recent_trades():
    print(f'\n📊 VERIFICANDO TRADES RECENTES NO BANCO:')
    try:
        conn = sqlite3.connect('memecoin.db')
        cursor = conn.cursor()
        
        # Verificar se tabela de trades existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
        if not cursor.fetchone():
            print('❌ Tabela de trades não encontrada')
            conn.close()
            return
        
        # Buscar trades das últimas 24 horas
        yesterday = datetime.now() - timedelta(days=1)
        cursor.execute("""
            SELECT timestamp, symbol, side, quantity, price, status 
            FROM trades 
            WHERE timestamp > ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        """, (yesterday.isoformat(),))
        
        trades = cursor.fetchall()
        if trades:
            print(f"Trades das últimas 24h ({len(trades)} encontrados):")
            for trade in trades:
                timestamp, symbol, side, quantity, price, status = trade
                print(f'  {timestamp} | {symbol} | {side} | {quantity} @ {price} | Status: {status}')
        else:
            print('❌ Nenhum trade encontrado nas últimas 24h')
        
        conn.close()
        
    except Exception as e:
        print(f'❌ Erro ao verificar trades: {e}')

def check_portfolio_positions():
    print(f'\n📈 VERIFICANDO POSIÇÕES DO PORTFOLIO:')
    try:
        # Verificar se existe arquivo de portfolio
        if os.path.exists('portfolio_positions.json'):
            with open('portfolio_positions.json', 'r') as f:
                positions = json.load(f)
            
            if positions:
                print("Posições ativas:")
                for symbol, position in positions.items():
                    print(f'  {symbol}:')
                    print(f'    Quantidade: {position.get("quantity", "N/A")}')
                    print(f'    Preço médio: {position.get("avg_price", "N/A")}')
                    print(f'    Performance: {position.get("performance_pct", "N/A")}%')
                    print(f'    Valor atual: {position.get("current_value", "N/A")}')
            else:
                print('❌ Nenhuma posição ativa encontrada')
        else:
            print('❌ Arquivo de posições não encontrado')
            
    except Exception as e:
        print(f'❌ Erro ao verificar posições: {e}')

def check_logs():
    print(f'\n📝 VERIFICANDO LOGS RECENTES:')
    try:
        # Verificar logs do AI agent
        if os.path.exists('ai_trading_agent_robust.log'):
            with open('ai_trading_agent_robust.log', 'r') as f:
                lines = f.readlines()
            
            # Pegar últimas 10 linhas
            recent_lines = lines[-10:] if len(lines) >= 10 else lines
            print("Últimas atividades do AI Agent:")
            for line in recent_lines:
                if line.strip():
                    print(f'  {line.strip()}')
        else:
            print('❌ Log do AI agent não encontrado')
            
    except Exception as e:
        print(f'❌ Erro ao verificar logs: {e}')

def test_trading_capabilities():
    print(f'\n🧪 TESTANDO CAPACIDADES DE TRADING:')
    try:
        from binance.client import Client
        from ai_trading_config import BINANCE_API_KEY, BINANCE_SECRET_KEY
        
        client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY, testnet=False)
        
        # Testar se conseguimos obter dados de mercado
        ticker = client.get_symbol_ticker(symbol="BTCUSDT")
        print(f'✅ Conexão com Binance OK - BTC: ${ticker["price"]}')
        
        # Testar se conseguimos obter informações da conta
        account = client.get_account()
        print(f'✅ Acesso à conta OK - Status: {account["accountType"]}')
        
        # Verificar se trading está habilitado
        if account["canTrade"]:
            print('✅ Trading habilitado na conta')
        else:
            print('❌ Trading não habilitado na conta')
        
        return True
        
    except Exception as e:
        print(f'❌ Erro ao testar trading: {e}')
        return False

if __name__ == "__main__":
    check_system_status()
    
    binance_ok = check_binance_balance()
    if binance_ok:
        test_trading_capabilities()
    
    check_recent_trades()
    check_portfolio_positions()
    check_logs()
    
    print('\n' + '=' * 50)
    print('✅ Verificação completa! Analise os resultados acima.')