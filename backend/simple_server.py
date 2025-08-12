"""
MoCoVe Backend Simplificado - Para Demonstração
Versão simplificada sem dependências externas
"""

import json
import sqlite3
import os
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

DB_PATH = 'memecoin.db'

class MoCoVeHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Definir o diretório do frontend corretamente
        import os
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        super().__init__(*args, directory=frontend_dir, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.startswith('/api/'):
            self.handle_api_request(parsed_path)
        else:
            # Servir arquivos estáticos
            if parsed_path.path == '/':
                self.path = '/index.html'
            super().do_GET()
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path.startswith('/api/'):
            self.handle_api_request(parsed_path)
    
    def handle_api_request(self, parsed_path):
        try:
            # Headers CORS
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            path = parsed_path.path
            response = {}
            
            if path == '/api/status':
                response = {
                    'status': 'online',
                    'exchange_connected': True,
                    'testnet_mode': True,
                    'database': {'prices_count': 0, 'trades_count': 0},
                    'timestamp': datetime.now().isoformat()
                }
            
            elif path == '/api/trades':
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM trades ORDER BY date DESC LIMIT 10')
                trades = []
                for row in cursor.fetchall():
                    trades.append({
                        'id': row[0],
                        'date': row[1],
                        'type': row[2],
                        'symbol': row[3],
                        'amount': row[4],
                        'price': row[5],
                        'total': row[6]
                    })
                conn.close()
                response = trades
            
            elif path == '/api/prices':
                query = parse_qs(parsed_path.query)
                symbol = query.get('symbol', ['DOGE/BUSD'])[0]
                
                # Simular dados de preços
                response = [
                    {
                        'symbol': symbol,
                        'timestamp': datetime.now().isoformat(),
                        'price': 0.08 + (hash(datetime.now().isoformat()) % 100) / 10000,
                        'volume': 1000000
                    }
                ]
            
            elif path == '/api/volatility':
                response = {
                    'symbol': 'DOGE/BUSD',
                    'volatility': 0.03,
                    'threshold': 0.05,
                    'is_high': False,
                    'current_price': 0.08,
                    'price_count': 10
                }
            
            elif path == '/api/settings':
                if self.command == 'GET':
                    response = {
                        'symbol': 'DOGE/BUSD',
                        'amount': 100,
                        'volatility_threshold': 0.05,
                        'is_active': True
                    }
                else:  # POST
                    response = {'message': 'Configurações salvas (simulado)'}
            
            elif path == '/api/market_data':
                response = {
                    'symbol': 'DOGE/BUSD',
                    'price': 0.08123,
                    'high': 0.0843,
                    'low': 0.0789,
                    'volume': 15420000,
                    'change': 0.0012,
                    'percentage': 1.54,
                    'timestamp': datetime.now().isoformat()
                }
            
            else:
                response = {'error': 'Endpoint não encontrado'}
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

def init_database():
    """Inicializa banco de dados SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATETIME NOT NULL,
            type TEXT NOT NULL,
            symbol TEXT NOT NULL,
            amount REAL NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            price REAL NOT NULL,
            volume REAL DEFAULT 0
        )
    ''')
    
    # Inserir dados de exemplo
    cursor.execute('SELECT COUNT(*) FROM trades')
    if cursor.fetchone()[0] == 0:
        sample_trades = [
            (datetime.now(), 'buy', 'DOGE/BUSD', 1000, 0.08, 80),
            (datetime.now(), 'sell', 'DOGE/BUSD', 500, 0.082, 41),
        ]
        cursor.executemany(
            'INSERT INTO trades (date, type, symbol, amount, price, total) VALUES (?, ?, ?, ?, ?, ?)',
            sample_trades
        )
    
    conn.commit()
    conn.close()

def main():
    print("🚀 Iniciando MoCoVe Backend Simplificado...")
    
    # Inicializar banco
    init_database()
    
    # Iniciar servidor
    server_address = ('localhost', 5000)
    httpd = HTTPServer(server_address, MoCoVeHandler)
    
    print(f"✅ Servidor rodando em http://localhost:5000")
    print(f"📊 Frontend: http://localhost:5000")
    print(f"🔌 API: http://localhost:5000/api/status")
    print(f"💾 Banco de dados: {DB_PATH}")
    print("\n🛑 Pressione Ctrl+C para parar")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor interrompido")
        httpd.shutdown()

if __name__ == "__main__":
    main()
