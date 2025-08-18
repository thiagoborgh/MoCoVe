import requests
import json

# Obter informações do preço atual e volume de PLUME
try:
    # Obter ticker de 24h
    response = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=PLUMEUSDT')
    ticker = response.json()
    
    print('PLUME/USDT - Informações 24h:')
    print(f'  Preço atual: ${ticker["lastPrice"]}')
    print(f'  Mudança 24h: {ticker["priceChangePercent"]}%')
    print(f'  Volume 24h: ${float(ticker["quoteVolume"]):,.0f}')
    print(f'  High 24h: ${ticker["highPrice"]}')
    print(f'  Low 24h: ${ticker["lowPrice"]}')
    print(f'  Count de trades: {ticker["count"]}')
    
    volume_usd = float(ticker['quoteVolume'])
    price_change = float(ticker['priceChangePercent'])
    
    # Sugerir categoria baseada no volume e volatilidade
    if volume_usd > 10000000:
        tier_suggestion = 'tier2'
    elif volume_usd > 5000000:
        tier_suggestion = 'tier3'
    else:
        tier_suggestion = 'trending'
        
    volatility_suggestion = abs(price_change) / 100 + 0.15  # Base volatility + daily change
    
    print(f'\nSugestões:')
    print(f'  Tier sugerido: {tier_suggestion}')
    print(f'  Volatilidade alvo: {volatility_suggestion:.2f}')
    print(f'  Trading habilitado: {volume_usd > 5000000}')
    
except Exception as e:
    print(f'Erro ao obter dados: {e}')