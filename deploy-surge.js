#!/usr/bin/env node
/**
 * Deploy Script para Surge.sh
 * Prepara e faz deploy do MoCoVe AI Trading Dashboard
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class SurgeDeployer {
    constructor() {
        this.projectName = 'mocove-ai-trading';
        this.buildDir = 'dist';
        this.sourceDir = 'frontend';
        this.apiBaseUrl = process.env.API_BASE_URL || 'http://localhost:5000'; // Usando porta do .env
    }

    log(message) {
        console.log(`🚀 [DEPLOY] ${message}`);
    }

    error(message) {
        console.error(`❌ [ERROR] ${message}`);
    }

    success(message) {
        console.log(`✅ [SUCCESS] ${message}`);
    }

    // Verificar se Surge está instalado
    checkSurge() {
        try {
            execSync('surge --version', { stdio: 'ignore' });
            this.log('Surge.sh encontrado');
            return true;
        } catch (error) {
            this.error('Surge.sh não está instalado');
            this.log('Instalando Surge.sh...');
            try {
                execSync('npm install -g surge', { stdio: 'inherit' });
                this.success('Surge.sh instalado com sucesso');
                return true;
            } catch (installError) {
                this.error('Falha ao instalar Surge.sh');
                return false;
            }
        }
    }

    // Preparar diretório de build
    prepareBuild() {
        this.log('Preparando build...');

        // Criar diretório dist
        if (fs.existsSync(this.buildDir)) {
            fs.rmSync(this.buildDir, { recursive: true });
        }
        fs.mkdirSync(this.buildDir, { recursive: true });

        // Copiar arquivos do frontend
        this.copyFiles();
        
        // Atualizar URLs da API
        this.updateApiUrls();
        
        // Criar arquivos de configuração
        this.createConfigFiles();

        this.success('Build preparado');
    }

    // Copiar arquivos
    copyFiles() {
        const filesToCopy = [
            'dashboard.html',
            'index.html'
        ];

        filesToCopy.forEach(file => {
            const sourcePath = path.join(this.sourceDir, file);
            const destPath = path.join(this.buildDir, file);
            
            if (fs.existsSync(sourcePath)) {
                fs.copyFileSync(sourcePath, destPath);
                this.log(`Copiado: ${file}`);
            }
        });

        // Renomear dashboard.html para index.html se necessário
        const dashboardPath = path.join(this.buildDir, 'dashboard.html');
        const indexPath = path.join(this.buildDir, 'index.html');
        
        if (fs.existsSync(dashboardPath) && !fs.existsSync(indexPath)) {
            fs.renameSync(dashboardPath, indexPath);
            this.log('Dashboard definido como página principal');
        }
    }

    // Atualizar URLs da API
    updateApiUrls() {
        const indexPath = path.join(this.buildDir, 'index.html');
        
        if (fs.existsSync(indexPath)) {
            let content = fs.readFileSync(indexPath, 'utf8');
            
            // Substituir URLs locais por URLs de produção
            content = content.replace(/http:\/\/localhost:5000/g, this.apiBaseUrl);
            content = content.replace(/\/api\//g, `${this.apiBaseUrl}/api/`);
            
            // Adicionar configuração de API base
            const apiConfig = `
                <script>
                    window.API_BASE_URL = '${this.apiBaseUrl}';
                    
                    // Função para fazer requisições com fallback
                    window.apiRequest = async (endpoint, options = {}) => {
                        const url = window.API_BASE_URL + endpoint;
                        try {
                            const response = await fetch(url, {
                                ...options,
                                headers: {
                                    'Content-Type': 'application/json',
                                    ...options.headers
                                }
                            });
                            return response;
                        } catch (error) {
                            console.warn('API não disponível, usando dados mockados');
                            return window.getMockData(endpoint);
                        }
                    };
                    
                    // Dados mockados para quando a API não estiver disponível
                    window.getMockData = (endpoint) => {
                        const mockData = {
                            '/api/status': {
                                ok: true,
                                json: async () => ({
                                    status: 'demo',
                                    exchange_connected: true,
                                    testnet_mode: true,
                                    default_symbol: 'DOGEUSDT'
                                })
                            },
                            '/api/market_data': {
                                ok: true,
                                json: async () => ({
                                    price: '0.224156',
                                    change_24h: '5.23',
                                    volume: '1234567890'
                                })
                            },
                            '/api/trades': {
                                ok: true,
                                json: async () => ([
                                    {
                                        timestamp: new Date().toISOString(),
                                        type: 'buy',
                                        symbol: 'DOGEUSDT',
                                        price: '0.224156',
                                        amount: '25.00',
                                        quantity: '111.42'
                                    }
                                ])
                            },
                            '/api/balance': {
                                ok: true,
                                json: async () => ({
                                    USDT: { total: 1000, free: 1000 },
                                    DOGE: { total: 500, free: 500 }
                                })
                            }
                        };
                        
                        return mockData[endpoint] || {
                            ok: false,
                            json: async () => ({ error: 'Endpoint não encontrado' })
                        };
                    };
                </script>
            `;
            
            content = content.replace('</head>', apiConfig + '\n</head>');
            
            fs.writeFileSync(indexPath, content);
            this.log('URLs da API atualizadas');
        }
    }

    // Criar arquivos de configuração
    createConfigFiles() {
        // CNAME para domínio customizado (opcional)
        const cname = `${this.projectName}.surge.sh`;
        fs.writeFileSync(path.join(this.buildDir, 'CNAME'), cname);

        // 200.html para SPA routing
        const indexContent = fs.readFileSync(path.join(this.buildDir, 'index.html'), 'utf8');
        fs.writeFileSync(path.join(this.buildDir, '200.html'), indexContent);

        // robots.txt
        const robotsTxt = `User-agent: *
Allow: /

Sitemap: https://${cname}/sitemap.xml`;
        fs.writeFileSync(path.join(this.buildDir, 'robots.txt'), robotsTxt);

        // manifest.json para PWA
        const manifest = {
            name: 'MoCoVe AI Trading Dashboard',
            short_name: 'MoCoVe',
            description: 'Dashboard de trading automatizado com IA',
            start_url: '/',
            display: 'standalone',
            background_color: '#667eea',
            theme_color: '#667eea',
            icons: [
                {
                    src: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiByeD0iMTIiIGZpbGw9IiM2NjdlZWEiLz4KPHN2ZyB4PSIxNiIgeT0iMTYiIHdpZHRoPSIzMiIgaGVpZ2h0PSIzMiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+CjxwYXRoIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0tMiAxNWwtNS01aDNWOWg0djNoM2wtNSA1eiIvPgo8L3N2Zz4K',
                    sizes: '64x64',
                    type: 'image/svg+xml'
                }
            ]
        };
        fs.writeFileSync(path.join(this.buildDir, 'manifest.json'), JSON.stringify(manifest, null, 2));

        this.log('Arquivos de configuração criados');
    }

    // Fazer deploy
    deploy() {
        this.log('Iniciando deploy...');
        
        try {
            const domain = `${this.projectName}.surge.sh`;
            const command = `surge ${this.buildDir} ${domain}`;
            
            this.log(`Fazendo deploy para: ${domain}`);
            execSync(command, { stdio: 'inherit' });
            
            this.success(`Deploy concluído com sucesso!`);
            this.success(`URL: https://${domain}`);
            
            return domain;
        } catch (error) {
            this.error('Falha no deploy');
            throw error;
        }
    }

    // Processo completo de deploy
    async run() {
        try {
            console.log('🤖 MoCoVe AI Trading Dashboard - Deploy');
            console.log('=====================================');
            
            // Verificar Surge
            if (!this.checkSurge()) {
                throw new Error('Surge.sh não disponível');
            }

            // Preparar build
            this.prepareBuild();

            // Deploy
            const domain = this.deploy();

            console.log('\n🎉 DEPLOY CONCLUÍDO COM SUCESSO!');
            console.log('================================');
            console.log(`🌐 URL: https://${domain}`);
            console.log(`📱 PWA: Pode ser instalado como app`);
            console.log(`🔄 Auto-deploy: Configure webhook no GitHub`);
            console.log('\n📋 Próximos passos:');
            console.log('1. Configure sua API backend');
            console.log('2. Teste todas as funcionalidades');
            console.log('3. Configure domínio customizado (opcional)');
            console.log('4. Configure SSL certificado');

        } catch (error) {
            this.error(`Deploy falhou: ${error.message}`);
            process.exit(1);
        }
    }
}

// Executar se chamado diretamente
if (require.main === module) {
    const deployer = new SurgeDeployer();
    deployer.run();
}

module.exports = SurgeDeployer;
