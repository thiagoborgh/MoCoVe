@echo off
title MoCoVe AI Trading System
color 0A

echo ========================================
echo  🚀 MoCoVe AI Trading System
echo ========================================
echo.

echo 📋 Configurando ambiente...

REM Definir variáveis de ambiente
set BINANCE_API_KEY=HxfDczSoWcWa1O3OUU65nSa98VTXrPhVjHYY545r2XSdrnHQAyDJsJoeDw9rs32o
set BINANCE_API_SECRET=lJrrJ55ssd7sE2XBLXJY2mqs2M4TmnpgyhTRtVHU1WXJltpJk7McsDCUeT4jjO0p
set USE_TESTNET=true
set DEFAULT_SYMBOL=DOGE/USDT
set DEFAULT_AMOUNT=25.0

echo ✅ Variáveis de ambiente configuradas
echo.

echo 🔧 Verificando dependências...
python -c "import ccxt, flask, requests" 2>nul
if errorlevel 1 (
    echo ❌ Dependências faltando. Instalando...
    pip install ccxt flask flask-cors requests pandas numpy
) else (
    echo ✅ Dependências OK
)
echo.

echo 🗄️ Inicializando banco de dados...
python -c "from backend.app import init_database; init_database()"
echo ✅ Banco de dados inicializado
echo.

echo 🚀 Iniciando serviços...
echo.

echo 📡 Backend API (Porta 5000)...
start "MoCoVe Backend" cmd /k "cd backend && python app.py"
timeout /t 3 /nobreak >nul

echo 🤖 AI Trading Agent...
start "AI Trading Agent" cmd /k "python ai_trading_agent_robust.py"
timeout /t 2 /nobreak >nul

echo 🌐 Frontend Server (Porta 8000)...
start "Frontend Server" cmd /k "python -m http.server 8000"
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo  ✅ Sistema MoCoVe Iniciado!
echo ========================================
echo.
echo 🌐 Dashboard: http://localhost:8000/frontend/index_complete_dashboard_clean.html
echo 📡 API Backend: http://localhost:5000/api/status
echo 🤖 AI Agent: Executando em background
echo.
echo Pressione qualquer tecla para abrir o dashboard...
pause >nul

start http://localhost:8000/frontend/index_complete_dashboard_clean.html

echo.
echo Sistema rodando! Pressione qualquer tecla para encerrar todos os serviços...
pause >nul

echo 🛑 Encerrando serviços...
taskkill /f /im python.exe /t >nul 2>&1
echo ✅ Serviços encerrados
pause
