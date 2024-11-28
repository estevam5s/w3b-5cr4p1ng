# Imagem base Python
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala o wget e outras dependências necessárias
RUN apt-get update && \
    apt-get install -y \
    wget \
    python3-distutils \
    python3-dev \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos necessários
COPY requirements.txt .
COPY app.py .
COPY templates/ templates/

# Cria e ativa o ambiente virtual, instala as dependências
RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Cria diretório para downloads e logs
RUN mkdir -p downloads logs && \
    chmod 777 downloads && \
    chmod 777 logs

# Expõe a porta que o Flask usará
EXPOSE 5000

# Variáveis de ambiente para produção
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Comando para rodar a aplicação
CMD ["./venv/bin/python", "app.py"]