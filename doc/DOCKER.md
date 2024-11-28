# Guia de Instalação com Docker

## Pré-requisitos
- Docker instalado
- Docker Compose instalado

## Estrutura do Projeto com Docker
```
cyber-site-downloader/
├── app.py
├── templates/
│   └── index.html
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .gitignore
├── README.md
└── DOCKER.md
```

## Comandos para Execução

### 1. Construir e Iniciar os Containers
```bash
sudo docker-compose up --build
```

### 2. Executar em Segundo Plano
```bash
sudo docker-compose up -d
```

### 3. Parar os Containers
```bash
sudo docker-compose down
```

### 4. Ver Logs
```bash
sudo docker-compose logs -f
```

### 5. Acessar o Shell do Container
```bash
sudo docker-compose exec web bash
```

## Volumes e Persistência
- Os downloads são salvos em './downloads' no host
- O volume é mapeado automaticamente para o container

## Redes
- A aplicação roda na rede 'cyber-network'
- Porta 5000 exposta para acesso local

## Ambiente de Desenvolvimento
1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/cyber-site-downloader.git
cd cyber-site-downloader
```

2. Construa e inicie os containers
```bash
sudo docker-compose up --build
```

3. Acesse a aplicação
```
http://localhost:5000
```

## Troubleshooting

### Problema de Permissão
Se houver problemas de permissão na pasta downloads:
```bash
chmod 777 downloads
```

### Porta em Uso
Se a porta 5000 estiver em uso:
1. Modifique a porta no docker-compose.yml:
```yaml
ports:
  - "5001:5000"
```
2. Reinicie os containers

### Logs do Container
Para ver logs em tempo real:
```bash
sudo docker-compose logs -f web
```

## Produção
Para ambiente de produção:
1. Modifique o Dockerfile:
```dockerfile
ENV FLASK_ENV=production
```

2. Configure variáveis de ambiente seguras:
```bash
cp .env.example .env
# Edite .env com suas configurações
```

3. Use o docker-compose.prod.yml:
```bash
sudo docker-compose -f docker-compose.prod.yml up -d
```

## Limpeza
### Remover Containers
```bash
sudo docker-compose down
```

### Remover Imagens
```bash
sudo docker-compose down --rmi all
```

### Limpar Volumes
```bash
sudo docker-compose down -v
```

## Backup
### Backup dos Downloads
```bash
tar -czf downloads_backup.tar.gz downloads/
```

### Restaurar Backup
```bash
tar -xzf downloads_backup.tar.gz
```

## Monitoramento
### Status dos Containers
```bash
sudo docker-compose ps
```

### Uso de Recursos
```bash
docker stats
```

## Segurança
- Não execute o container como root
- Mantenha as imagens atualizadas
- Use secrets para senhas
- Configure firewalls apropriadamente

## CI/CD
Exemplo de .gitlab-ci.yml:
```yaml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - docker-compose build

test:
  stage: test
  script:
    - docker-compose up -d
    - docker-compose exec -T web python -m pytest

deploy:
  stage: deploy
  script:
    - docker-compose -f docker-compose.prod.yml up -d
  only:
    - master
```

## Contribuindo
1. Use uma branch para features
2. Teste localmente com Docker
3. Submeta PR com logs de teste