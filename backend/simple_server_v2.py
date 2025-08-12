"""
MoCoVe Backend Simplificado - Versão Corrigida
Servidor HTTP simples para demonstração
"""

import json
import sqlite3
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import mimetypes

DB_PATH = 'memecoin.db'

class MoCoVeHandler(BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.startswith('/api/'):
            self.handle_api_request(parsed_path, 'GET')
        else:
            self.serve_static_file(parsed_path.path)
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path.startswith('/api/'):
            self.handle_api_request(parsed_path, 'POST')
    
    def serve_static_file(self, path):
        """Serve static files from frontend directory"""
        try:
            # Determinar caminho do arquivo
            if path == '/' or path == '':
                file_path = 'index.html'
            else:
                file_path = path.lstrip('/')
            
            # Caminho completo
            frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
            full_path = os.path.join(frontend_dir, file_path)
            
            # Verificar se arquivo existe
            if not os.path.exists(full_path):
                self.send_error(404, f"File not found: {file_path}")
                return
            
            # Determinar tipo MIME
            mime_type, _ = mimetypes.guess_type(full_path)
            if mime_type is None:
                mime_type = 'text/plain'
            
            # Ler e servir arquivo
            with open(full_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', mime_type)
            self.send_header('Content-length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            print(f"Erro ao servir arquivo {path}: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def handle_api_request(self, parsed_path, method):
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
            
            print(f"API Request: {method} {path}")
            
            if path == '/api/status':
                response = {
                    'status': 'online',
                    'exchange_connected': True,
                    'testnet_mode': True,
                    'database': {'prices_count': 0, 'trades_count': 0},
                    'timestamp': datetime.now().isoformat()
                }
            
            elif path == '/api/trades':
                try:
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
                except Exception as e:
                    response = []
            
            elif path == '/api/prices':
                query = parse_qs(parsed_path.query)
                symbol = query.get('symbol', ['DOGE/BUSD'])[0]
                
                # Simular dados de preços realistas
                import time
                base_price = 0.08
                variation = (hash(str(time.time())) % 1000) / 100000  # Pequena variação
                current_price = base_price + variation
                
                response = []
                # Gerar últimos 20 pontos
                for i in range(20):
                    timestamp = datetime.now().timestamp() - (i * 300)  # A cada 5 minutos
                    price_var = (hash(str(timestamp)) % 200 - 100) / 100000
                    response.append({
                        'id': i,
                        'symbol': symbol,
                        'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                        'price': base_price + price_var,
                        'volume': 1000000 + (hash(str(timestamp)) % 500000)
                    })
                
                response.reverse()  # Ordem cronológica
            
            elif path == '/api/volatility':
                # Simular cálculo de volatilidade
                import random
                vol = random.uniform(0.01, 0.08)
                response = {
                    'symbol': 'DOGE/BUSD',
                    'volatility': vol,
                    'threshold': 0.05,
                    'is_high': vol > 0.05,
                    'current_price': 0.08123,
                    'price_count': 20
                }
            
            elif path == '/api/settings':
                if method == 'GET':
                    response = {
                        'id': 1,
                        'symbol': 'DOGE/BUSD',
                        'amount': 100,
                        'volatility_threshold': 0.05,
                        'is_active': True
                    }
                else:  # POST
                    response = {'message': 'Configurações salvas com sucesso'}
            
            elif path == '/api/market_data':
                import random
                base_price = 0.08123
                change = random.uniform(-0.005, 0.005)
                response = {
                    'symbol': 'DOGE/BUSD',
                    'price': base_price + change,
                    'high': base_price + 0.005,
                    'low': base_price - 0.005,
                    'volume': random.randint(10000000, 20000000),
                    'change': change,
                    'percentage': (change / base_price) * 100,
                    'timestamp': datetime.now().isoformat()
                }
            
            elif path == '/api/execute_trade':
                if method == 'POST':
                    # Simular execução de trade
                    content_length = int(self.headers.get('Content-Length', 0))
                    if content_length > 0:
                        post_data = self.rfile.read(content_length)
                        try:
                            trade_data = json.loads(post_data.decode('utf-8'))
                            
                            # Inserir no banco
                            conn = sqlite3.connect(DB_PATH)
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT INTO trades (date, type, symbol, amount, price, total)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (
                                datetime.now().isoformat(),
                                trade_data.get('type', 'buy'),
                                trade_data.get('symbol', 'DOGE/BUSD'),
                                trade_data.get('amount', 100),
                                0.08123,
                                trade_data.get('amount', 100) * 0.08123
                            ))
                            conn.commit()
                            conn.close()
                            
                            response = {
                                'success': True,
                                'message': f"Ordem de {trade_data.get('type', 'buy')} executada com sucesso (simulado)",
                                'order': {
                                    'id': f'sim_{datetime.now().timestamp()}',
                                    'type': trade_data.get('type', 'buy'),
                                    'symbol': trade_data.get('symbol', 'DOGE/BUSD'),
                                    'amount': trade_data.get('amount', 100),
                                    'price': 0.08123
                                }
                            }
                        except Exception as e:
                            response = {'error': f'Erro ao processar trade: {str(e)}'}
                    else:
                        response = {'error': 'Dados do trade não fornecidos'}
                else:
                    response = {'error': 'Método não suportado'}
            
            else:
                response = {'error': 'Endpoint não encontrado'}
            
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            print(f"Erro na API: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())

def init_database():
    """Inicializa banco de dados SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
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
            timestamp TEXT NOT NULL,
            price REAL NOT NULL,
            volume REAL DEFAULT 0
        )
    ''')
    
    # Inserir dados de exemplo se não existirem
    cursor.execute('SELECT COUNT(*) FROM trades')
    if cursor.fetchone()[0] == 0:
        sample_trades = [
            (datetime.now().isoformat(), 'buy', 'DOGE/BUSD', 1000, 0.08, 80),
            (datetime.now().isoformat(), 'sell', 'DOGE/BUSD', 500, 0.082, 41),
        ]
        cursor.executemany(
            'INSERT INTO trades (date, type, symbol, amount, price, total) VALUES (?, ?, ?, ?, ?, ?)',
            sample_trades
        )
    
    conn.commit()
    conn.close()

def main():
    print("🚀 Iniciando MoCoVe Backend Simplificado v2...")
    
    # Verificar diretórios
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    index_path = os.path.join(frontend_dir, 'index.html')
    
    print(f"📁 Diretório frontend: {frontend_dir}")
    print(f"📄 Index.html existe: {os.path.exists(index_path)}")
    
    # Inicializar banco
    init_database()
    print(f"💾 Banco de dados: {DB_PATH}")
    
    # Iniciar servidor
    server_address = ('localhost', 5000)
    httpd = HTTPServer(server_address, MoCoVeHandler)
    
    print(f"\n✅ Servidor rodando em http://localhost:5000")
    print(f"📊 Frontend: http://localhost:5000")
    print(f"🔌 API Status: http://localhost:5000/api/status")
    print(f"📈 API Trades: http://localhost:5000/api/trades")
    print("\n🛑 Pressione Ctrl+C para parar")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor interrompido")
        httpd.shutdown()

if __name__ == "__main__":
    main()
