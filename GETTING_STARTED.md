# Guia de Instalação e Execução do Cyber Site Downloader

## Requisitos do Sistema
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- wget instalado no sistema

## Estrutura do Projeto
```
cyber-site-downloader/
├── app.py
├── templates/
│   └── index.html
├── requirements.txt
├── GETTING_STARTED.md
└── downloads/
```

## Passo a Passo para Instalação

### 1. Instalando o wget

#### No Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install wget
```

#### No macOS:
```bash
brew install wget
```

#### No Windows:
- Baixe o wget de https://eternallybored.org/misc/wget/
- Adicione ao PATH do sistema

### 2. Configurando o Ambiente Python

1. Clone o repositório ou crie a estrutura de diretórios:
```bash
mkdir cyber-site-downloader
cd cyber-site-downloader
```

2. Crie um ambiente virtual:
```bash
# No Windows
python -m venv venv
.\venv\Scripts\activate

# No Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

### 3. Configurando o Projeto

1. Crie os diretórios necessários:
```bash
mkdir templates
mkdir downloads
```

2. Copie o arquivo `index.html` para a pasta `templates/`
3. Copie o arquivo `app.py` para a raiz do projeto

## Executando o Projeto

1. Certifique-se de que o ambiente virtual está ativado:
```bash
# No Windows
.\venv\Scripts\activate

# No Linux/macOS
source venv/bin/activate
```

2. Inicie o servidor:
```bash
python app.py
```

3. Acesse a aplicação:
- Abra seu navegador
- Acesse `http://localhost:5000`

## Verificando a Instalação

1. A interface web deve carregar sem erros
2. O console deve mostrar a mensagem de servidor iniciado
3. Teste adicionando uma URL de exemplo

## Solução de Problemas Comuns

### Erro: "wget not found"
- Verifique se o wget está instalado corretamente
- Confirme se o wget está no PATH do sistema
- No Windows, reinicie o terminal após adicionar ao PATH

### Erro: "Port already in use"
```bash
# Linux/macOS
lsof -i :5000
kill -9 PID

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Erro: "Module not found"
- Verifique se está no ambiente virtual correto
- Reinstale as dependências:
```bash
pip install -r requirements.txt
```

## Logs e Debug

- Os logs são exibidos no console do servidor
- Logs adicionais são mostrados na interface web
- Para debug mais detalhado, modifique o nível de log em `app.py`

## Atualizações

Para atualizar as dependências:
```bash
pip freeze > requirements.txt
```

## Suporte

Em caso de problemas:
1. Verifique os logs do servidor
2. Confirme as versões das dependências
3. Verifique a conexão com a internet
4. Confirme as permissões do diretório de downloads

## Desenvolvimento

Para desenvolvimento local:
1. Ative o modo debug em `app.py`
2. Use ferramentas de desenvolvimento do navegador
3. Monitore os logs do servidor