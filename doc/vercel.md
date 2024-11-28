# Implantando Aplicativo Python na Vercel

## 1. Estrutura de Arquivos

Primeiro, precisamos criar os arquivos necessários para a Vercel:

### vercel.json
```json
{
    "version": 2,
    "builds": [
        {
            "src": "app.py",
            "use": "@vercel/python"
        }
    ],
    "routes": [
        {
            "src": "/(.*)",
            "dest": "app.py"
        }
    ]
}
```

### requirements.txt (atualizado para Vercel)
```text
flask==2.3.3
flask-socketio==5.3.6
python-engineio==4.8.0
python-socketio==5.10.0
gunicorn==21.2.0
```

### wsgi.py
```python
from app import app

if __name__ == '__main__':
    app.run()
```

## 2. Adaptação do Código

### app.py (modificado para Vercel)
```python
from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

# Configuração básica para a Vercel
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'cyber-download-secret')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def start_download():
    # Lógica do download adaptada para Vercel
    return jsonify({'message': 'Download iniciado'})

# Remova a parte do __main__ do arquivo original
# A Vercel usará o wsgi.py para iniciar a aplicação
```

## 3. Configuração da Vercel CLI

1. Instale a Vercel CLI:
```bash
npm install -g vercel
```

2. Faça login na Vercel:
```bash
vercel login
```

## 4. Deploy

1. Deploy inicial:
```bash
vercel
```

2. Deploy em produção:
```bash
vercel --prod
```

## 5. Variáveis de Ambiente

Configure as variáveis de ambiente no dashboard da Vercel:

1. Acesse o dashboard da Vercel
2. Vá para seu projeto
3. Settings > Environment Variables
4. Adicione as variáveis necessárias:
   - `FLASK_ENV`
   - `SECRET_KEY`

## 6. Limitações e Considerações

1. **WebSocket:**
   - A Vercel tem limitações com WebSocket
   - Considere usar alternativas como HTTP polling ou Servidor WebSocket separado

2. **Sistema de Arquivos:**
   - A Vercel não suporta escrita em arquivo
   - Use serviços externos para armazenamento (S3, Firebase, etc.)

3. **Processos em Segundo Plano:**
   - Não suporta processos longos
   - Use serviços externos para downloads (AWS Lambda, etc.)

## 7. Alternativas para Funcionalidades Não Suportadas

### Armazenamento
```python
import boto3

s3 = boto3.client('s3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY')
)

def save_file(data, filename):
    s3.put_object(
        Bucket='seu-bucket',
        Key=filename,
        Body=data
    )
```

### WebSocket Alternativo
```python
from flask_sse import sse

app.register_blueprint(sse, url_prefix='/stream')

@app.route('/progress')
def progress():
    def generate():
        yield 'data: {"progress": 50}\n\n'
    return Response(generate(), mimetype='text/event-stream')
```

## 8. Monitoramento

1. Use o dashboard da Vercel para:
   - Logs
   - Performance
   - Erros
   - Métricas

2. Adicione serviços externos:
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="sua-dsn",
    integrations=[FlaskIntegration()]
)
```

## 9. CI/CD

### Exemplo de Github Actions
```yaml
name: Deploy to Vercel
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID}}
          vercel-project-id: ${{ secrets.PROJECT_ID}}
```