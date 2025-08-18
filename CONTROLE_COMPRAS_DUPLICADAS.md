# 🛡️ Sistema de Controle de Compras Duplicadas

## Visão Geral

O sistema de controle de compras duplicadas foi implementado para evitar que o agente de trading compre a mesma moeda mais de uma vez, reduzindo o risco e melhorando a diversificação do portfólio.

## Como Funciona

### 1. Carregamento Automático
- Ao iniciar, o agente carrega automaticamente todas as moedas que já foram compradas (trades do tipo "buy") do histórico
- Utiliza a API `/api/trades` para obter o histórico de transações

### 2. Verificação Durante Análise
- Antes de executar uma compra, o agente verifica se a moeda já está na lista de compradas
- Se a moeda já foi comprada, a oportunidade é ignorada e o log mostra: `🚫 SÍMBOLO: JÁ COMPRADA - Pulando para evitar duplicata`

### 3. Atualização Automática
- Quando uma compra é executada com sucesso, a moeda é automaticamente adicionada à lista
- Isto garante que futuras análises não considerem esta moeda para compra

## Funcionalidades Principais

### Controle Automático
```python
# Verificação automática durante análise
if action == "buy" and symbol in self.purchased_coins:
    log.info(f"🚫 {symbol}: JÁ COMPRADA - Pulando para evitar duplicata")
    continue
```

### Visualizar Moedas Compradas
```python
agent = SimpleAgent()
purchased_coins = agent.show_purchased_coins()
# Mostra: 🛡️ Moedas compradas (3): BTCUSDT, DOGEUSDT, ETHUSDT
```

### Permitir Recompra
```python
# Remover uma moeda da lista (permite recompra)
agent.remove_purchased_coin("DOGEUSDT")
# Log: 🛡️ DOGEUSDT removida da lista de moedas compradas - recompra permitida
```

### Reset Completo
```python
# Limpar toda a lista (permite recompra de todas)
agent.reset_purchased_coins()
# Log: 🛡️ Lista de moedas compradas foi resetada
```

## Script de Gerenciamento

Execute o script `manage_purchased_coins.py` para gerenciar a lista interativamente:

```bash
python manage_purchased_coins.py
```

### Opções disponíveis:
1. **Mostrar moedas compradas** - Lista todas as moedas já compradas
2. **Remover moeda da lista** - Permite recompra de uma moeda específica
3. **Resetar lista completa** - Limpa toda a lista (permite recompra de todas)

## Logs e Monitoramento

### Logs de Inicialização
```
🛡️ Controle de duplicatas: 3 moedas já compradas: BTCUSDT, DOGEUSDT, ETHUSDT...
```

### Logs de Verificação
```
🚫 DOGEUSDT: JÁ COMPRADA - Pulando para evitar duplicata
```

### Logs de Compra
```
🛡️ BTCUSDT adicionada à lista de moedas compradas
```

## Vantagens

1. **Diversificação Forçada** - Previne concentração em uma única moeda
2. **Redução de Risco** - Evita over-trading na mesma posição
3. **Controle Transparente** - Logs claros sobre decisões bloqueadas
4. **Flexibilidade** - Permite override manual quando necessário

## Configuração

O sistema é ativado automaticamente. Não requer configuração adicional.

### Variáveis de Controle
- `self.purchased_coins`: Set contendo símbolos das moedas já compradas
- Carregado automaticamente do histórico de trades via API
- Atualizado automaticamente a cada compra bem-sucedida

## Casos de Uso

### Cenário 1: Primeira Execução
- Lista vazia, todas as moedas podem ser compradas
- Após primeira compra de DOGEUSDT, esta fica bloqueada

### Cenário 2: Reinício do Agente
- Carrega automaticamente DOGEUSDT como já comprada
- Continua operação sem permitir recompra

### Cenário 3: Gestão Manual
- Usuário decide permitir recompra de DOGEUSDT
- Executa `agent.remove_purchased_coin("DOGEUSDT")`
- DOGEUSDT volta a ser elegível para compra

## Observações Importantes

- ⚠️ O controle se aplica apenas a **compras (buy)**
- ✅ **Vendas (sell)** não são afetadas pelo controle
- 🔄 O histórico é carregado via API, garantindo persistência entre execuções
- 🛡️ Moedas podem ser removidas manualmente da lista quando necessário

## Integração com Dashboard

O sistema funciona perfeitamente com o dashboard existente:
- Trades são salvos normalmente no banco de dados
- Histórico de trades permanece inalterado
- Controle é transparente para o usuário final