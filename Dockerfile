# Dockerfile para MoCoVe Backend
FROM python:3.9-slim

# Configurar diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p logs ai/models

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV DB_PATH=/app/memecoin.db
ENV MODEL_PATH=/app/ai/memecoin_rf_model.pkl

# Porta da aplicação
EXPOSE 5000

# Comando de inicialização
CMD ["python", "backend/app.py"]
