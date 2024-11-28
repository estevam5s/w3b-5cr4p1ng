# 🌟 Cyber Site Downloader

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![Flask Version](https://img.shields.io/badge/flask-2.3.3-green.svg)
![Docker](https://img.shields.io/badge/docker-supported-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Socket.IO](https://img.shields.io/badge/socket.io-v4.0.1-brightgreen.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

</div>

<p align="center">Um aplicativo web moderno para download de sites completos, utilizando tecnologias avançadas de web scraping e interface em tempo real.</p>

## 📑 Índice

- [Características](#-características)
- [Tecnologias](#️-tecnologias)
- [Instalação](#-instalação)
  - [Usando Docker](#-usando-docker-recomendado)
  - [Instalação Manual](#-instalação-manual)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Configuração Detalhada](#-configuração-detalhada)
- [Exemplos de Código](#-exemplos-de-código)
- [Uso](#-uso)
- [Docker](#-docker)
- [Monitoramento](#-monitoramento)
- [Segurança](#-segurança)
- [Troubleshooting](#-troubleshooting)
- [Contribuindo](#-contribuindo)
- [Equipe](#-equipe)
- [Contato](#-contato)
- [Licença](#-licença)

## 🌟 Características

### Core Features
- ✨ Interface moderna e responsiva
- 🔄 Download em tempo real com feedback
- 📊 Monitoramento de progresso
- 🚦 Sistema de filas
- 📝 Logs detalhados
- 🔒 Validação de segurança
- 🐳 Suporte a Docker

### Features Avançadas
- 🔄 Auto-retry em caso de falha
- 📈 Progresso em tempo real via WebSocket
- 🎨 Interface responsiva e moderna
- 🔍 Logs detalhados e pesquisáveis
- 🛡️ Proteção contra sobrecarga
- 📁 Organização automática de downloads
- 🔗 Suporte a múltiplas URLs

## 🛠️ Tecnologias

### Backend
- Python 3.11
- Flask & Flask-SocketIO
- Eventlet
- WebSocket
- Wget
- Threading
- Queue Management
- Logging System

### Frontend
- HTML5 & CSS3
- JavaScript (ES6+)
- Socket.IO Client
- Font Awesome Icons
- Responsive Design
- Real-time Updates

### Infraestrutura
- Docker
- Docker Compose
- Nginx (opcional)
- Sistema de Logs
- Monitoramento em Tempo Real

## 📥 Instalação

### 🐳 Usando Docker (Recomendado)

1. **Clone o repositório:**
```bash
git clone https://github.com/estevam5s/cyber-site-downloader.git
cd cyber-site-downloader
```

2. **Construa e inicie os containers:**
```bash
# Construir e iniciar
docker-compose up --build

# Rodar em background
docker-compose up -d

# Parar os containers
docker-compose down

# Remover volumes
docker-compose down -v
```

3. **Verificar logs:**
```bash
# Todos os logs
docker-compose logs

# Logs em tempo real
docker-compose logs -f

# Logs específicos
docker-compose logs web
```

### 🔧 Instalação Manual

1. **Requisitos do Sistema:**
   - Python 3.11+
   - wget
   - pip
   - Virtualenv

2. **Configure o Ambiente:**
```bash
# Clone o repositório
git clone https://github.com/estevam5s/cyber-site-downloader.git
cd cyber-site-downloader

# Crie e ative o ambiente virtual
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
./venv/Scripts/activate

# Instale as dependências
pip install -r requirements.txt
```

3. **Configure as Variáveis de Ambiente:**
```bash
# Linux/macOS
export FLASK_APP=app.py
export FLASK_ENV=development

# Windows
set FLASK_APP=app.py
set FLASK_ENV=development
```

4. **Execute a Aplicação:**
```bash
python server.py
```

## 📁 Estrutura do Projeto

```
cyber-site-downloader/
├── app.py                 # Aplicação Flask principal
├── templates/            # Templates HTML
│   └── index.html       # Interface principal
├── static/              # Arquivos estáticos
│   ├── css/
│   └── js/
├── downloads/           # Pasta de downloads
├── logs/               # Logs do sistema
├── Dockerfile          # Configuração Docker
├── docker-compose.yml  # Configuração Docker Compose
├── requirements.txt    # Dependências Python
├── LICENSE            # Licença do projeto
└── README.md          # Documentação
```

## ⚙️ Configuração Detalhada

### Configuração do Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    wget \
    python3-distutils \
    python3-dev \
    build-essential

COPY requirements.txt .
COPY app.py .
COPY templates/ templates/

RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["./venv/bin/python", "app.py"]
```

```yaml
# docker-compose.yml
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./downloads:/app/downloads
      - ./logs:/app/logs
    environment:
      - FLASK_APP=app.py
      - FLASK_ENV=production
    restart: unless-stopped
    networks:
      - cyber-network

networks:
  cyber-network:
    driver: bridge
```

### Configuração do Backend

```python
# app.py (trecho principal)
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

@app.route('/')
def home():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    emit('client_id', {'client_id': client_id})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
```

## 💻 Exemplos de Código

### Frontend Socket.IO
```javascript
const socket = io({
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
});

socket.on('connect', () => {
    console.log('Conectado ao servidor');
    updateConnectionStatus(true);
});

socket.on('progress', (data) => {
    updateProgress(data.progress);
    updateStatus(data.status);
});
```

### Backend Download Function
```python
def download_site(url, folder_name, client_id):
    """Faz o download de um site específico"""
    try:
        wget_command = [
            "wget",
            "--mirror",
            "--convert-links",
            "--page-requisites",
            "--no-parent",
            url
        ]
        process = subprocess.Popen(wget_command)
        return True
    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        return False
```

## 📋 Uso

1. **Iniciar o Sistema:**
   ```bash
   # Com Docker
   docker-compose up -d

   # Sem Docker
   python server.py
   ```

2. **Acessar a Interface:**
   - Abra o navegador
   - Acesse `http://localhost:5000`

3. **Usar a Aplicação:**
   - Cole as URLs desejadas
   - Clique em "Adicionar URL"
   - Inicie os downloads
   - Monitore o progresso

## 🔍 Monitoramento

### Logs do Sistema
- Logs em tempo real na interface
- Registro de eventos no servidor
- Histórico de downloads
- Status de conexão

### Métricas
- Progresso dos downloads
- Status do sistema
- Uso de recursos
- Performance

## 🔐 Segurança

### Medidas Implementadas
- Validação de URLs
- Proteção contra DDoS
- Rate Limiting
- Sanitização de inputs
- Controle de acesso

### Boas Práticas
- Limitação de recursos
- Validação de dados
- Logs de segurança
- Backup automático

## 🔧 Troubleshooting

### Problemas Comuns

1. **Erro de Conexão:**
```bash
# Verificar status do Docker
docker-compose ps

# Verificar logs
docker-compose logs web
```

2. **Problemas de Permissão:**
```bash
# Ajustar permissões
chmod -R 755 downloads/
chmod -R 755 logs/
```

3. **Erros de Download:**
   - Verificar conexão com internet
   - Validar URLs
   - Checar logs específicos

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add: nova funcionalidade'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Guia de Contribuição
- Siga o estilo de código
- Documente as mudanças
- Adicione testes
- Atualize a documentação

## 👥 Equipe

**Estevam Innovations**
- Desenvolvimento Full Stack
- DevOps e Infraestrutura
- Design e UX/UI
- Qualidade e Testes

## 📫 Contato

- **GitHub:** [@estevam5s](https://github.com/estevam5s)
- **Email:** contato@estevamsouza.com.br
- **Website:** [Estevam Innovations](https://estevaminnovations.com.br)

## 📜 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<div align="center">

Desenvolvido com ❤️ por **Estevam Innovations**

[⬆ Voltar ao topo](#cyber-site-downloader)

</div>