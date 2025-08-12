#!/usr/bin/env node
/**
 * Quick Start Script - MoCoVe AI Trading System
 * Usando configuração .env existente na porta 5000
 */

const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

class MoCoVeStarter {
    constructor() {
        this.processes = [];
        this.isRunning = false;
        this.config = this.loadConfig();
    }

    loadConfig() {
        // Configuração baseada no .env existente
        const defaultConfig = {
            backend: {
                port: 5000, // Porta configurada no .env
                auto_start_agent: false
            },
            frontend: {
                port: 3000,
                api_url: 'http://localhost:5000'
            },
            ai_agent: {
                enabled: false,
                symbol: 'DOGEUSDT',
                investment_amount: 10.0, // Valor do .env
                risk_level: 'conservative'
            }
        };

        try {
            if (fs.existsSync('mocove-config.json')) {
                const userConfig = JSON.parse(fs.readFileSync('mocove-config.json', 'utf8'));
                return { ...defaultConfig, ...userConfig };
            }
        } catch (error) {
            console.log('⚠️  Usando configuração padrão');
        }

        return defaultConfig;
    }

    log(message) {
        console.log(`🚀 [MOCOVE] ${message}`);
    }

    error(message) {
        console.error(`❌ [ERROR] ${message}`);
    }

    success(message) {
        console.log(`✅ [SUCCESS] ${message}`);
    }

    // Verificar .env existente
    checkEnvFile() {
        this.log('Verificando .env existente...');
        
        if (fs.existsSync('.env')) {
            const envContent = fs.readFileSync('.env', 'utf8');
            
            if (envContent.includes('PORT=5000')) {
                this.success('.env encontrado com porta 5000 ✓');
                return true;
            }
        }
        
        this.error('Arquivo .env não encontrado ou inválido');
        return false;
    }

    // Iniciar backend Python na porta 5000
    async startBackend() {
        this.log('Iniciando backend Python na porta 5000...');
        
        try {
            const backendProcess = spawn('python', ['backend/app_real.py'], {
                stdio: 'pipe',
                env: { ...process.env }
            });

            backendProcess.stdout.on('data', (data) => {
                console.log(`🖥️  [BACKEND] ${data.toString().trim()}`);
            });

            backendProcess.stderr.on('data', (data) => {
                console.error(`🖥️  [BACKEND] ${data.toString().trim()}`);
            });

            this.processes.push({
                name: 'backend',
                process: backendProcess,
                port: 5000
            });

            // Aguardar inicialização
            await new Promise(resolve => setTimeout(resolve, 3000));
            this.success('Backend Python iniciado na porta 5000');
            return true;
            
        } catch (error) {
            this.error(`Erro ao iniciar backend: ${error.message}`);
            return false;
        }
    }

    // Iniciar frontend na porta 3000
    startFrontend() {
        this.log('Iniciando frontend na porta 3000...');
        
        const http = require('http');
        const url = require('url');
        
        const server = http.createServer((req, res) => {
            const parsedUrl = url.parse(req.url, true);
            let pathname = parsedUrl.pathname;
            
            // Roteamento
            if (pathname === '/' || pathname === '/dashboard') {
                pathname = '/frontend/dashboard.html';
            }
            
            const filePath = path.join(__dirname, pathname);
            
            if (fs.existsSync(filePath)) {
                const ext = path.extname(filePath);
                let contentType = 'text/html';
                
                if (ext === '.js') contentType = 'text/javascript';
                else if (ext === '.css') contentType = 'text/css';
                
                res.writeHead(200, { 
                    'Content-Type': contentType,
                    'Access-Control-Allow-Origin': '*'
                });
                res.end(fs.readFileSync(filePath));
            } else {
                res.writeHead(404);
                res.end('Página não encontrada');
            }
        });
        
        server.listen(3000, () => {
            this.success('Frontend rodando na porta 3000');
        });

        return true;
    }

    // AI Agent (opcional)
    async startAIAgent() {
        if (!this.config.ai_agent.enabled) {
            this.log('AI Agent desabilitado');
            return true;
        }

        this.log('Iniciando AI Agent...');
        
        try {
            const agentProcess = spawn('python', ['ai_trading_agent.py'], {
                stdio: 'pipe'
            });

            agentProcess.stdout.on('data', (data) => {
                console.log(`🤖 [AI] ${data.toString().trim()}`);
            });

            this.processes.push({
                name: 'ai_agent',
                process: agentProcess
            });

            await new Promise(resolve => setTimeout(resolve, 2000));
            this.success('AI Agent iniciado');
            return true;
            
        } catch (error) {
            this.error(`Erro AI Agent: ${error.message}`);
            return false;
        }
    }

    // Mostrar status
    showStatus() {
        console.log('\n🎯 MOCOVE AI TRADING SYSTEM');
        console.log('===========================');
        console.log('📊 Dashboard: http://localhost:3000');
        console.log('🖥️  Backend: http://localhost:5000 (.env)');
        
        if (this.config.ai_agent.enabled) {
            console.log(`🤖 AI Agent: Ativo`);
        } else {
            console.log('🤖 AI Agent: Inativo');
        }
        
        console.log('\n📋 Comandos:');
        console.log('• Ctrl+C: Parar sistema');
        console.log('• npm run config: Configurar');
    }

    // Configuração interativa
    async configure() {
        const readline = require('readline');
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout
        });

        const question = (query) => new Promise(resolve => rl.question(query, resolve));

        console.log('\n⚙️  CONFIGURAÇÃO');
        console.log('================');

        try {
            const enableAgent = await question('🤖 Habilitar AI Agent? (s/n): ');
            this.config.ai_agent.enabled = enableAgent.toLowerCase() === 's';

            if (this.config.ai_agent.enabled) {
                const symbol = await question('📈 Símbolo (DOGEUSDT): ');
                if (symbol.trim()) this.config.ai_agent.symbol = symbol.trim().toUpperCase();
            }

            // Salvar
            fs.writeFileSync('mocove-config.json', JSON.stringify(this.config, null, 2));
            this.success('Configuração salva!');

        } finally {
            rl.close();
        }
    }

    // Parar sistema
    stop() {
        this.log('Parando sistema...');
        
        this.processes.forEach(({ name, process }) => {
            this.log(`Parando ${name}...`);
            process.kill();
        });

        this.success('Sistema parado');
        process.exit(0);
    }

    // Executar
    async run() {
        console.log('🤖 MoCoVe AI Trading System');
        console.log('============================');
        console.log('🔧 Usando .env na porta 5000');

        // Verificar se é configuração
        if (process.argv.includes('--config')) {
            await this.configure();
            return;
        }

        try {
            // Verificar .env
            if (!this.checkEnvFile()) {
                throw new Error('Arquivo .env necessário');
            }

            // Iniciar serviços
            await this.startBackend();
            this.startFrontend();
            await this.startAIAgent();

            // Status
            this.showStatus();

            // Handlers
            process.on('SIGINT', () => this.stop());
            process.on('SIGTERM', () => this.stop());

            this.success('Sistema iniciado!');

        } catch (error) {
            this.error(`Erro: ${error.message}`);
            process.exit(1);
        }
    }
}

// Executar
if (require.main === module) {
    const starter = new MoCoVeStarter();
    starter.run();
}

module.exports = MoCoVeStarter;
