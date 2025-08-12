#!/usr/bin/env node
/**
 * SETUP FINAL - MoCoVe AI Trading System
 * Script de configuração final e verificação do sistema
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class FinalSetup {
    constructor() {
        this.projectRoot = __dirname;
        this.setupComplete = false;
        this.checkedItems = [];
    }

    log(message) {
        console.log(`🔧 [SETUP] ${message}`);
    }

    success(message) {
        console.log(`✅ [SUCCESS] ${message}`);
    }

    error(message) {
        console.error(`❌ [ERROR] ${message}`);
    }

    warning(message) {
        console.warn(`⚠️  [WARNING] ${message}`);
    }

    // Verificar estrutura de arquivos
    checkFileStructure() {
        this.log('Verificando estrutura de arquivos...');

        const requiredFiles = [
            'ai_trading_agent.py',
            'ai_agent_config.py', 
            'ai_agent_monitor.py',
            'start_ai_trading.py',
            'frontend/dashboard.html',
            'backend/api_extensions.py',
            'deploy-surge.js',
            'quick-start.js',
            'package.json',
            'DOCUMENTATION.md',
            'AI_TRADING_README.md'
        ];

        let missingFiles = [];

        requiredFiles.forEach(file => {
            const filePath = path.join(this.projectRoot, file);
            if (fs.existsSync(filePath)) {
                this.success(`${file} ✓`);
            } else {
                this.error(`${file} não encontrado`);
                missingFiles.push(file);
            }
        });

        if (missingFiles.length === 0) {
            this.success('Estrutura de arquivos OK');
            this.checkedItems.push('file_structure');
            return true;
        } else {
            this.error(`${missingFiles.length} arquivos não encontrados`);
            return false;
        }
    }

    // Verificar backend integrado
    checkBackendIntegration() {
        this.log('Verificando integração do backend...');

        try {
            const backendPath = path.join(this.projectRoot, 'backend/app_real.py');
            
            if (fs.existsSync(backendPath)) {
                const content = fs.readFileSync(backendPath, 'utf8');
                
                // Verificar se as integrações foram feitas
                const hasApiExtensionsImport = content.includes('from api_extensions import');
                const hasExtensionRegistration = content.includes('register_extensions');
                
                if (hasApiExtensionsImport && hasExtensionRegistration) {
                    this.success('Backend integração completa');
                    this.checkedItems.push('backend_integration');
                    return true;
                } else {
                    this.warning('Backend parcialmente integrado');
                    return false;
                }
            } else {
                this.error('Backend principal não encontrado');
                return false;
            }
        } catch (error) {
            this.error(`Erro ao verificar backend: ${error.message}`);
            return false;
        }
    }

    // Criar arquivo de configuração padrão
    createDefaultConfig() {
        this.log('Criando configuração padrão...');

        const defaultConfig = {
            system: {
                name: "MoCoVe AI Trading System",
                version: "2.0.0",
                environment: "development"
            },
            backend: {
                port: 5000,
                host: "localhost",
                testnet: true,
                cors_enabled: true
            },
            frontend: {
                port: 3000,
                host: "localhost",
                api_base_url: "http://localhost:5000"
            },
            ai_agent: {
                enabled: false,
                symbol: "DOGEUSDT",
                investment_amount: 25.0,
                risk_level: "conservative",
                confidence_threshold: 0.7
            },
            trading: {
                testnet_mode: true,
                max_trades_per_day: 5,
                stop_loss_percentage: 5.0,
                take_profit_percentage: 10.0
            },
            notifications: {
                enabled: true,
                email: false,
                webhook: false,
                telegram: false
            },
            deploy: {
                surge_enabled: false,
                domain: "mocove-ai-trading.surge.sh",
                auto_deploy: false
            }
        };

        const configPath = path.join(this.projectRoot, 'mocove-config.json');
        
        try {
            fs.writeFileSync(configPath, JSON.stringify(defaultConfig, null, 2));
            this.success('Configuração padrão criada');
            this.checkedItems.push('default_config');
            return true;
        } catch (error) {
            this.error(`Erro ao criar configuração: ${error.message}`);
            return false;
        }
    }

    // Criar arquivo de exemplo de ambiente
    createEnvExample() {
        this.log('Criando arquivo .env de exemplo...');

        const envExample = `# MoCoVe AI Trading System - Environment Variables

# =================================
# BINANCE API CONFIGURATION
# =================================
# IMPORTANTE: Use TESTNET para desenvolvimento!
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
BINANCE_TESTNET=true

# =================================
# TRADING CONFIGURATION
# =================================
DEFAULT_SYMBOL=DOGEUSDT
INVESTMENT_AMOUNT=25.0
RISK_LEVEL=conservative

# =================================
# SYSTEM CONFIGURATION
# =================================
FLASK_ENV=development
FLASK_DEBUG=true
DATABASE_URL=sqlite:///memecoin.db

# =================================
# SOCIAL SENTIMENT APIs (opcional)
# =================================
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# =================================
# DEPLOYMENT CONFIGURATION
# =================================
SURGE_DOMAIN=mocove-ai-trading.surge.sh
AUTO_DEPLOY=false

# =================================
# NOTIFICATION SETTINGS
# =================================
EMAIL_NOTIFICATIONS=false
WEBHOOK_URL=
TELEGRAM_CHAT_ID=

# =================================
# SECURITY
# =================================
SECRET_KEY=your_flask_secret_key_here
JWT_SECRET=your_jwt_secret_here
`;

        const envExamplePath = path.join(this.projectRoot, '.env.example');
        
        try {
            fs.writeFileSync(envExamplePath, envExample);
            this.success('Arquivo .env.example criado');
            this.checkedItems.push('env_example');
            return true;
        } catch (error) {
            this.error(`Erro ao criar .env.example: ${error.message}`);
            return false;
        }
    }

    // Verificar dependências Python
    checkPythonDeps() {
        this.log('Verificando dependências Python...');

        const pythonDeps = [
            'flask',
            'flask-cors', 
            'pandas',
            'numpy',
            'requests'
        ];

        let missingDeps = [];

        pythonDeps.forEach(dep => {
            try {
                execSync(`python -c "import ${dep.replace('-', '_')}"`, { stdio: 'ignore' });
                this.success(`${dep} ✓`);
            } catch (error) {
                this.warning(`${dep} não instalado`);
                missingDeps.push(dep);
            }
        });

        if (missingDeps.length === 0) {
            this.success('Dependências Python OK');
            this.checkedItems.push('python_deps');
            return true;
        } else {
            this.warning(`${missingDeps.length} dependências Python não instaladas`);
            this.log(`Execute: pip install ${missingDeps.join(' ')}`);
            return false;
        }
    }

    // Verificar dependências Node.js
    checkNodeDeps() {
        this.log('Verificando dependências Node.js...');

        const packageJsonPath = path.join(this.projectRoot, 'package.json');
        const nodeModulesPath = path.join(this.projectRoot, 'node_modules');

        if (!fs.existsSync(packageJsonPath)) {
            this.error('package.json não encontrado');
            return false;
        }

        if (!fs.existsSync(nodeModulesPath)) {
            this.warning('node_modules não encontrado');
            this.log('Execute: npm install');
            return false;
        }

        this.success('Dependências Node.js OK');
        this.checkedItems.push('node_deps');
        return true;
    }

    // Criar scripts de conveniência
    createConvenienceScripts() {
        this.log('Criando scripts de conveniência...');

        // Script para Windows
        const startBat = `@echo off
echo MoCoVe AI Trading System - Startup
echo =====================================

echo Starting system...
node quick-start.js

pause`;

        // Script para Linux/Mac
        const startSh = `#!/bin/bash
echo "MoCoVe AI Trading System - Startup"
echo "====================================="

echo "Starting system..."
node quick-start.js

read -p "Press enter to continue..."`;

        try {
            fs.writeFileSync(path.join(this.projectRoot, 'start.bat'), startBat);
            fs.writeFileSync(path.join(this.projectRoot, 'start.sh'), startSh);
            
            // Tornar script shell executável
            if (process.platform !== 'win32') {
                execSync('chmod +x start.sh', { cwd: this.projectRoot });
            }

            this.success('Scripts de conveniência criados');
            this.checkedItems.push('convenience_scripts');
            return true;
        } catch (error) {
            this.error(`Erro ao criar scripts: ${error.message}`);
            return false;
        }
    }

    // Mostrar relatório final
    showFinalReport() {
        console.log('\n🎯 RELATÓRIO FINAL DO SETUP');
        console.log('============================');

        const totalChecks = 7;
        const completedChecks = this.checkedItems.length;
        const completionRate = (completedChecks / totalChecks * 100).toFixed(1);

        console.log(`📊 Progress: ${completedChecks}/${totalChecks} (${completionRate}%)`);
        console.log('\n✅ Items Completados:');
        
        this.checkedItems.forEach(item => {
            const descriptions = {
                'file_structure': 'Estrutura de arquivos verificada',
                'backend_integration': 'Backend integrado com API extensions',
                'default_config': 'Configuração padrão criada',
                'env_example': 'Arquivo .env de exemplo criado',
                'python_deps': 'Dependências Python verificadas',
                'node_deps': 'Dependências Node.js verificadas',
                'convenience_scripts': 'Scripts de conveniência criados'
            };
            console.log(`  • ${descriptions[item] || item}`);
        });

        if (completedChecks < totalChecks) {
            console.log('\n⚠️  Items Pendentes:');
            const allItems = ['file_structure', 'backend_integration', 'default_config', 'env_example', 'python_deps', 'node_deps', 'convenience_scripts'];
            const pendingItems = allItems.filter(item => !this.checkedItems.includes(item));
            
            pendingItems.forEach(item => {
                const descriptions = {
                    'file_structure': 'Verificar estrutura de arquivos',
                    'backend_integration': 'Integrar backend com API extensions',
                    'default_config': 'Criar configuração padrão',
                    'env_example': 'Criar arquivo .env de exemplo',
                    'python_deps': 'Instalar dependências Python',
                    'node_deps': 'Instalar dependências Node.js',
                    'convenience_scripts': 'Criar scripts de conveniência'
                };
                console.log(`  • ${descriptions[item] || item}`);
            });
        }

        console.log('\n🚀 PRÓXIMOS PASSOS:');
        console.log('1. Configure suas chaves API no arquivo .env');
        console.log('2. Execute: npm run config (configuração interativa)');
        console.log('3. Execute: npm start (iniciar sistema)');
        console.log('4. Acesse: http://localhost:3000 (dashboard)');
        console.log('5. Teste primeiro no TESTNET!');
        
        console.log('\n📚 DOCUMENTAÇÃO:');
        console.log('• README.md - Guia geral');
        console.log('• DOCUMENTATION.md - Documentação completa');
        console.log('• AI_TRADING_README.md - Guia do AI Agent');
        
        console.log('\n🔧 COMANDOS ÚTEIS:');
        console.log('• npm start - Iniciar sistema');
        console.log('• npm run config - Configuração');
        console.log('• npm run deploy - Deploy Surge.sh');
        console.log('• npm run ai-config - Config AI Agent');
        console.log('• npm run status - Status do sistema');

        this.setupComplete = completedChecks >= 5; // Pelo menos 5 de 7 itens
        
        if (this.setupComplete) {
            console.log('\n🎉 SETUP CONCLUÍDO COM SUCESSO!');
            console.log('Sistema pronto para uso!');
        } else {
            console.log('\n⚠️  SETUP PARCIALMENTE CONCLUÍDO');
            console.log('Complete os itens pendentes antes de prosseguir.');
        }
    }

    // Executar setup completo
    async run() {
        console.log('🤖 MoCoVe AI Trading System - Setup Final');
        console.log('===========================================');
        console.log('Verificando e configurando sistema...\n');

        // Executar todas as verificações
        this.checkFileStructure();
        this.checkBackendIntegration();
        this.createDefaultConfig();
        this.createEnvExample();
        this.checkPythonDeps();
        this.checkNodeDeps();
        this.createConvenienceScripts();

        // Mostrar relatório final
        this.showFinalReport();

        return this.setupComplete;
    }
}

// Executar se chamado diretamente
if (require.main === module) {
    const setup = new FinalSetup();
    setup.run().then(success => {
        process.exit(success ? 0 : 1);
    });
}

module.exports = FinalSetup;
