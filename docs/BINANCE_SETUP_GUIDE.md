# 🔐 Guia Completo: Conectar Conta Binance Real ao MoCoVe

## 📋 Passo a Passo para Configuração

### **1. 🔑 Obter Chaves da API Binance**

#### **A. Acessar Binance API Management:**
1. Faça login na [Binance](https://binance.com)
2. Vá em **Profile → API Management**
3. Clique em **Create API**

#### **B. Configurações de Segurança:**
```
✅ Nome da API: MoCoVe Trading Bot
✅ Restrições IP: Adicione seu IP (recomendado)
✅ Permissões necessárias:
   - ✅ Enable Reading
   - ✅ Enable Spot & Margin Trading
   - ❌ Enable Futures (NÃO recomendado para início)
   - ❌ Enable Withdrawals (NÃO necessário)
```

#### **C. Salvar Credenciais:**
```
🔑 API Key: (sua chave pública)
🔐 Secret Key: (sua chave privada - NUNCA compartilhe!)
```

---

### **2. ⚙️ Configurar Arquivo .env**

#### **A. Criar arquivo .env na raiz do projeto:**
```bash
# Copiar do template
cp config/.env.example .env
```

#### **B. Editar .env com suas credenciais:**
```bash
# MoCoVe Configuration - PRODUÇÃO
# ⚠️ NUNCA compartilhe este arquivo!

# Database
DB_PATH=./memecoin.db

# 🔥 BINANCE API REAL (PRODUÇÃO)
BINANCE_API_KEY=sua_api_key_aqui
BINANCE_API_SECRET=sua_secret_key_aqui
USE_TESTNET=false

# AI Model
MODEL_PATH=./ai/memecoin_rf_model.pkl
AI_MODEL_URL=http://localhost:5000

# Server Configuration
PORT=5000
DEBUG=false

# 💰 Trading Parameters
DEFAULT_SYMBOL=DOGEUSDT
DEFAULT_AMOUNT=10.0          # Comece com valores baixos!
DEFAULT_VOLATILITY_THRESHOLD=0.02

# Data Collection
COLLECTION_INTERVAL=60
COINGECKO_API_KEY=

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/mocove.log
```

---

### **3. � Executar Script de Configuração Automática**

#### **A. Usar o script setup_binance.py:**
```bash
# Na pasta raiz do MoCoVe
python setup_binance.py
```

#### **B. Seguir o assistente interativo:**
```
🚀 MoCoVe - Setup de Conta Binance Real
=====================================

📋 Opções:
1. 🔧 Configurar credenciais Binance
2. 🔍 Testar conexão
3. 🛡️  Ver checklist de segurança
4. 📄 Ver arquivo .env atual
5. ❌ Sair
```

---

### **4. 🔧 Modificações no Código (Automáticas)**

#### **A. O script já configura automaticamente:**
- ✅ Arquivo .env com suas credenciais
- ✅ Teste de conexão com Binance
- ✅ Verificação de permissões
- ✅ Validação de saldos
- ✅ Checklist de segurança

#### **B. Configurações de segurança aplicadas:**
```python
# Limites de segurança automáticos
MAX_TRADE_AMOUNT = 100.0      # Máximo por trade
DAILY_LOSS_LIMIT = 50.0       # Limite de perda diária
DEFAULT_AMOUNT = 10.0         # Valor inicial baixo
VOLATILITY_THRESHOLD = 0.02   # 2% de volatilidade
```

---

### **5. 🛡️ Medidas de Segurança Implementadas**

#### **A. Limitações de Trading:**
```python
# No backend/app.py - já implementado
def validate_trade_amount(amount, symbol):
    max_amount = float(os.getenv('MAX_TRADE_AMOUNT', 100.0))
    if amount > max_amount:
        raise ValueError(f"Valor acima do limite: ${amount} > ${max_amount}")
    return True

def check_daily_limits():
    # Verifica perdas do dia
    today_loss = calculate_daily_pnl()
    limit = float(os.getenv('DAILY_LOSS_LIMIT', 50.0))
    if today_loss < -limit:
        raise ValueError(f"Limite de perda diária atingido: ${today_loss}")
    return True
```

#### **B. Monitoramento de Riscos:**
```python
# Sistema de alertas automático
def risk_management_check(trade_data):
    checks = [
        validate_trade_amount(trade_data['amount'], trade_data['symbol']),
        check_daily_limits(),
        verify_account_balance(),
        validate_market_conditions()
    ]
    return all(checks)
```

---

### **6. 🎯 Testando a Integração**

#### **A. Verificação Passo a Passo:**
```bash
# 1. Executar setup
python setup_binance.py

# 2. Testar backend com conta real
python backend/app.py

# 3. Abrir interface
# http://localhost:5000

# 4. Verificar logs
tail -f logs/mocove.log
```

#### **B. Primeira Operação de Teste:**
1. **Configure valores baixos** (ex: $5-10)
2. **Monitore em tempo real**
3. **Verifique saldos antes/depois**
4. **Analise os logs de execução**

---

### **7. 📊 Monitoramento da Conta Real**

#### **A. Dashboard Atualizado:**
```html
<!-- Novo painel para conta real -->
<div className="bg-white p-6 rounded-lg shadow">
    <h3 className="text-lg font-semibold mb-4">💰 Conta Binance Real</h3>
    <div className="grid grid-cols-2 gap-4">
        <div>
            <p className="text-sm text-gray-500">Saldo USDT</p>
            <p className="text-xl font-bold">${balance.USDT}</p>
        </div>
        <div>
            <p className="text-sm text-gray-500">P&L Hoje</p>
            <p className={`text-xl font-bold ${pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                ${pnl.toFixed(2)}
            </p>
        </div>
    </div>
</div>
```

---

### **8. 🚨 Alertas e Notificações**

#### **A. Sistema de Alertas:**
```python
# Alertas automáticos implementados
ALERT_CONDITIONS = {
    'high_loss': -20.0,        # Perda de $20
    'high_profit': 50.0,       # Lucro de $50
    'api_error': True,         # Erros de API
    'balance_low': 10.0        # Saldo baixo
}

def send_alert(condition, message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    alert = f"🚨 ALERTA [{condition}] {timestamp}: {message}"
    
    # Log
    logger.warning(alert)
    
    # Notificação (pode adicionar email/Telegram)
    print(alert)
```

---

## ⚠️ **AVISOS IMPORTANTES**

### **🔥 RISCOS E PRECAUÇÕES:**

1. **💰 Comece com Valores Pequenos**
   - Primeiros trades: $5-10 máximo
   - Aumente gradualmente conforme ganhar confiança

2. **📊 Monitore Constantemente**
   - Verifique trades a cada 30 minutos
   - Configure alertas de perda/lucro
   - Mantenha logs ativos

3. **🛡️ Segurança da API**
   - NUNCA compartilhe suas chaves
   - Use restrição de IP
   - Desabilite withdrawals
   - Revise permissões regularmente

4. **🎯 Configurações Recomendadas**
   - Volatilidade máxima: 2-3%
   - Trade máximo: $50-100
   - Perda diária máxima: $50
   - Stop-loss automático

### **📞 Suporte e Emergência:**

```bash
# Em caso de problemas
# 1. Parar o sistema
Ctrl+C no terminal

# 2. Verificar logs
cat logs/mocove.log | tail -20

# 3. Desabilitar trading
# Editar .env: DEFAULT_AMOUNT=0

# 4. Verificar saldos na Binance
# Login manual na conta
```

---

## 🎯 **Resumo dos Próximos Passos**

### **✅ Lista de Verificação:**

1. **🔑 Obter chaves API da Binance**
2. **🚀 Executar `python setup_binance.py`**
3. **🔍 Testar conexão (opção 2 do script)**
4. **⚙️ Configurar valores conservadores**
5. **🎮 Fazer primeiro trade de teste**
6. **📊 Monitorar resultados**
7. **🔄 Ajustar parâmetros conforme necessário**

### **🎖️ Status Final:**
Após seguir este guia, você terá:
- ✅ Conta Binance real integrada
- ✅ Configurações de segurança ativas
- ✅ Sistema de monitoramento completo
- ✅ Alertas automáticos configurados
- ✅ Logs detalhados de todas as operações

**🚀 Seu MoCoVe estará pronto para trading real com máxima segurança!**
