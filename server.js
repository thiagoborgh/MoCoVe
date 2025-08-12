const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const axios = require('axios');
const Binance = require('node-binance-api');
const app = express();
const port = process.env.PORT || 5000; // Usar porta do .env

// Middleware
app.use(express.json());
app.use(express.static('frontend'));

// Configuração CORS
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  next();
});

// Endpoint para decisão inteligente via modelo Python externo
app.post('/ai-decision', async (req, res) => {
  // Espera receber features: { price, sma9, sma21, sma50, rsi, min24h, max24h, var24h, volume, sentiment, ... }
  const features = req.body;
  try {
    // Exemplo: URL do modelo Python (ajuste conforme necessário)
    const modelUrl = process.env.AI_MODEL_URL || 'http://localhost:5001/predict';
    const response = await axios.post(modelUrl, features);
    // Espera resposta: { decision: 'BUY' | 'SELL' | 'HOLD', probability: 0.92, ... }
    res.json(response.data);
  } catch (err) {
    res.status(500).json({ error: 'Erro ao consultar modelo AI', details: err.message });
  }
});
// Endpoint para simular compra
app.post('/buy', async (req, res) => {
  const { symbol, quantity } = req.body;
  try {
    const order = await binance.marketBuy(symbol, quantity);
    if (order) {
      db.run(`INSERT INTO orders (symbol, side, quantity, price, timestamp) VALUES (?, ?, ?, ?, ?)`,
        [symbol, 'BUY', quantity, order.fills && order.fills[0] ? order.fills[0].price : 0, new Date()]);
    }
    res.json({ success: true, order });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Endpoint para simular venda
app.post('/sell', async (req, res) => {
  const { symbol, quantity } = req.body;
  try {
    const order = await binance.marketSell(symbol, quantity);
    if (order) {
      db.run(`INSERT INTO orders (symbol, side, quantity, price, timestamp) VALUES (?, ?, ?, ?, ?)`,
        [symbol, 'SELL', quantity, order.fills && order.fills[0] ? order.fills[0].price : 0, new Date()]);
    }
    res.json({ success: true, order });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Endpoint para histórico de ordens (para frontend)
app.get('/orders', (req, res) => {
  db.all(`SELECT * FROM orders ORDER BY timestamp DESC LIMIT 50`, [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
// Funções auxiliares para indicadores
function calcSMA(data, period) {
  if (data.length < period) return null;
  return data.slice(-period).reduce((sum, v) => sum + v, 0) / period;
}
function calcRSI(prices, period = 14) {
  if (prices.length < period + 1) return null;
  let gains = 0, losses = 0;
  for (let i = prices.length - period; i < prices.length; i++) {
    const diff = prices[i] - prices[i - 1];
    if (diff > 0) gains += diff;
    else losses -= diff;
  }
  if (gains + losses === 0) return 50;
  const rs = gains / (losses || 1e-9);
  return 100 - (100 / (1 + rs));
}

// Endpoint de indicadores para trading
app.get('/indicators/:coin_id', (req, res) => {
  const { coin_id } = req.params;
  db.all(`SELECT price, timestamp FROM prices WHERE coin_id = ? ORDER BY timestamp ASC`, [coin_id], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!rows || rows.length === 0) return res.status(404).json({ error: 'Sem dados' });
    const prices = rows.map(r => r.price);
    const timestamps = rows.map(r => r.timestamp);
    const last = prices[prices.length - 1];
    const min24h = Math.min(...prices.slice(-24));
    const max24h = Math.max(...prices.slice(-24));
    const min7d = Math.min(...prices);
    const max7d = Math.max(...prices);
    const var24h = ((last - prices[prices.length - 24] || last) / (prices[prices.length - 24] || last)) * 100;
    const sma9 = calcSMA(prices, 9);
    const sma21 = calcSMA(prices, 21);
    const sma50 = calcSMA(prices, 50);
    const rsi = calcRSI(prices);
    res.json({
      price: last,
      min24h, max24h, min7d, max7d,
      var24h,
      sma9, sma21, sma50,
      rsi,
      timestamps
    });
  });
});
// Endpoint para memecoins mais hype
app.get('/hype', (req, res) => {
  // Critério: maior variação de volume e preço nas últimas 24h
  db.all(`SELECT coin_id, symbol, MAX(price) as max_price, MIN(price) as min_price, MAX(volume_change) as max_vol, COUNT(*) as count
          FROM prices
          WHERE timestamp >= datetime('now', '-1 day')
          GROUP BY coin_id
          ORDER BY (max_price - min_price) * max_vol DESC
          LIMIT 5`, [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    // Adicionar um score de hype simples
    const hypeList = rows.map(r => ({
      coin_id: r.coin_id,
      symbol: r.symbol || '',
      hype_score: ((r.max_price - r.min_price) * (r.max_vol || 1)).toFixed(4)
    }));
    res.json(hypeList);
  });
});
// Endpoint para sentimento médio
app.get('/sentiment', (req, res) => {
  db.get('SELECT AVG(score) as average_sentiment FROM sentiment', [], (err, row) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ average_sentiment: row && row.average_sentiment !== null ? row.average_sentiment : 0.5 });
  });
});

// Configurar middleware
app.use(express.json());
app.use(express.static('public'));

// Conectar ao SQLite
const db = new sqlite3.Database('memecoin.db', (err) => {
  if (err) console.error('Erro ao conectar ao SQLite:', err);
  else console.log('Conectado ao SQLite');
});

// Criar tabelas
db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id TEXT,
    timestamp DATETIME,
    price REAL,
    volume_change REAL
  )`);
  db.run(`CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    side TEXT,
    quantity REAL,
    price REAL,
    timestamp DATETIME
  )`);
  db.run(`CREATE TABLE IF NOT EXISTS sentiment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id TEXT,
    score REAL,
    timestamp DATETIME
  )`);
});

// Configurar Binance Testnet
const binance = new Binance().options({
  APIKEY: process.env.API_KEY,
  APISECRET: process.env.API_SECRET,
  test: true
});

// Função para coletar preços (CoinGecko)
async function getMemecoinPrice(coin_id) {
  try {
    const response = await axios.get(`https://api.coingecko.com/api/v3/coins/${coin_id}/market_chart?vs_currency=usd&days=1`);
    const prices = response.data.prices.map(([timestamp, price]) => ({ timestamp, price }));
    const latest_price = prices[prices.length - 1].price;
    const volume_change = (prices[prices.length - 1].price / prices[prices.length - 2].price - 1);
    db.run(`INSERT INTO prices (coin_id, timestamp, price, volume_change) VALUES (?, ?, ?, ?)`,
      [coin_id, new Date(), latest_price, volume_change]);
    return { latest_price, volume_change };
  } catch (err) {
    console.error('Erro ao coletar preços:', err);
    return null;
  }
}

// Função de decisão
function tradingDecision(volume_spike, sentiment_score) {
  if (volume_spike > 0.5 && sentiment_score > 0.7) return 'BUY';
  if (volume_spike < -0.1) return 'SELL';
  return 'HOLD';
}

// Endpoint para monitoramento e ordens
app.post('/monitor', async (req, res) => {
  const { coin_id, symbol, quantity, sentiment_score, start_hour, end_hour } = req.body;
  const now = new Date().getHours();
  if (start_hour <= now && now < end_hour) {
    const data = await getMemecoinPrice(coin_id);
    if (!data) return res.status(500).json({ error: 'Erro ao coletar preços' });

    const decision = tradingDecision(data.volume_change, sentiment_score);
    let order = null;
    if (decision === 'BUY') {
      order = await binance.marketBuy(symbol, quantity);
      if (order) {
        const stop_price = data.latest_price * 0.9;
        await binance.sell(symbol, quantity, null, { stopPrice: stop_price, type: 'STOP_LOSS' });
        db.run(`INSERT INTO orders (symbol, side, quantity, price, timestamp) VALUES (?, ?, ?, ?, ?)`,
          [symbol, 'BUY', quantity, data.latest_price, new Date()]);
      }
    } else if (decision === 'SELL') {
      order = await binance.marketSell(symbol, quantity);
      if (order) {
        db.run(`INSERT INTO orders (symbol, side, quantity, price, timestamp) VALUES (?, ?, ?, ?, ?)`,
          [symbol, 'SELL', quantity, data.latest_price, new Date()]);
      }
    }
    res.json({ decision, price: data.latest_price, volume_change: data.volume_change, order });
  } else {
    res.json({ message: `Fora do horário (${start_hour}h-${end_hour}h)` });
  }
});

// Endpoint para histórico
app.get('/history', (req, res) => {
  db.all(`SELECT * FROM orders ORDER BY timestamp DESC`, [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

// Endpoint para preços
app.get('/prices', (req, res) => {
  db.all(`SELECT * FROM prices ORDER BY timestamp DESC LIMIT 50`, [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

// Iniciar servidor
app.listen(port, () => console.log(`Servidor rodando na porta ${port}`));