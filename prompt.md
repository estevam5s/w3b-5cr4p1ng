Com base no codigo python abaixo:

# Monkey patch precisa ser o primeiro
import eventlet
eventlet.monkey_patch()

# Cria diretórios necessários antes de configurar logging
import os
import shutil
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import threading
import subprocess
from datetime import datetime
import time
import queue
import logging
from urllib.parse import urlparse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cyber-download-secret'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
socketio = SocketIO(app, 
                   async_mode='eventlet',
                   cors_allowed_origins="*",
                   ping_timeout=60,
                   ping_interval=25)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Filas e estados
download_queue = queue.Queue()
current_downloads = {}
active_clients = set()

def validate_url(url):
    """Valida se a URL é segura e acessível"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception as e:
        logger.error(f"Erro na validação da URL: {str(e)}")
        return False

def create_cyber_folder(counter):
    """Cria uma pasta com o prefixo Cyber e um número"""
    try:
        folder_name = f"downloads/Cyber{counter}"
        os.makedirs(folder_name, exist_ok=True)
        os.chmod(folder_name, 0o755)  # Permissões adequadas
        logger.info(f"Pasta criada: {folder_name}")
        return folder_name
    except Exception as e:
        logger.error(f"Erro ao criar pasta: {str(e)}")
        return None

def format_size(size):
    """Formata o tamanho em bytes para formato legível"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

def calculate_progress(output):
    """Calcula o progresso baseado na saída do wget"""
    try:
        if '%' in output:
            return int(output.split('%')[0].split()[-1])
        return 0
    except:
        return 0

def download_site(url, folder_name, client_id):
    """Faz o download de um site específico"""
    logger.info(f"Iniciando download de: {url}")
    socketio.emit('log', {'message': f"Iniciando download de: {url}"}, room=client_id)
    
    if not validate_url(url):
        error_msg = f"URL inválida: {url}"
        logger.error(error_msg)
        socketio.emit('log', {'message': error_msg}, room=client_id)
        return False

    wget_command = [
        "wget",
        "--mirror",
        "--convert-links",
        "--adjust-extension",
        "--page-requisites",
        "--no-parent",
        "--progress=bar:force",
        "--tries=3",
        "--timeout=30",
        "--directory-prefix=" + folder_name,
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "--reject=exe,zip,tar,gz,iso,dmg",  # Rejeita arquivos potencialmente perigosos
        url
    ]
    
    try:
        process = subprocess.Popen(
            wget_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitora o progresso em tempo real
        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                progress = calculate_progress(output)
                if progress > 0:
                    socketio.emit('progress', {
                        'url': url,
                        'status': 'downloading',
                        'progress': progress
                    }, room=client_id)
                socketio.emit('log', {'message': output.strip()}, room=client_id)
                logger.debug(output.strip())
        
        rc = process.poll()
        if rc == 0:
            success_msg = f"Download concluído com sucesso: {url}"
            logger.info(success_msg)
            socketio.emit('log', {'message': success_msg}, room=client_id)
            return True
        else:
            error_msg = f"Erro no download de {url}"
            logger.error(error_msg)
            socketio.emit('log', {'message': error_msg}, room=client_id)
            return False
            
    except Exception as e:
        error_msg = f"Erro ao executar o download de {url}: {str(e)}"
        logger.error(error_msg)
        socketio.emit('log', {'message': error_msg}, room=client_id)
        return False

def process_download_queue():
    """Processa a fila de downloads"""
    counter = 1
    while True:
        try:
            if not download_queue.empty():
                url, client_id = download_queue.get()
                
                # Verifica se o cliente ainda está conectado
                if client_id not in active_clients:
                    logger.info(f"Cliente {client_id} desconectado, pulando download")
                    continue
                
                folder_name = create_cyber_folder(counter)
                if not folder_name:
                    continue
                
                socketio.emit('progress', {
                    'url': url,
                    'status': 'starting',
                    'progress': 0
                }, room=client_id)
                
                success = download_site(url, folder_name, client_id)
                
                if success:
                    counter += 1
                    socketio.emit('progress', {
                        'url': url,
                        'status': 'completed',
                        'progress': 100
                    }, room=client_id)
                else:
                    socketio.emit('progress', {
                        'url': url,
                        'status': 'error',
                        'progress': 0
                    }, room=client_id)
                
                time.sleep(5)  # Espera entre downloads
            else:
                time.sleep(1)  # Evita consumo excessivo de CPU
        except Exception as e:
            logger.error(f"Erro no processamento da fila: {str(e)}")
            time.sleep(5)  # Espera antes de tentar novamente

@app.route('/')
def home():
    """Rota principal que renderiza a interface"""
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def start_download():
    """Inicia o processo de download"""
    try:
        data = request.json
        urls = data.get('urls', [])
        client_id = data.get('client_id')
        
        if not urls:
            return jsonify({'error': 'Nenhuma URL fornecida'}), 400
        
        if not client_id:
            return jsonify({'error': 'ID do cliente não fornecido'}), 400
        
        if client_id not in active_clients:
            return jsonify({'error': 'Cliente não está conectado'}), 400
        
        # Valida todas as URLs antes de adicionar à fila
        invalid_urls = [url for url in urls if not validate_url(url)]
        if invalid_urls:
            return jsonify({
                'error': 'URLs inválidas encontradas',
                'invalid_urls': invalid_urls
            }), 400
        
        # Adiciona URLs à fila
        for url in urls:
            download_queue.put((url, client_id))
        
        return jsonify({'message': 'Downloads adicionados à fila com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao iniciar download: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<folder_name>', methods=['GET'])
def download_folder(folder_name):
    """Faz o download da pasta compactada"""
    folder_path = f"downloads/{folder_name}"
    zip_file_path = f"downloads/{folder_name}.zip"

    # Compacta a pasta
    shutil.make_archive(folder_path, 'zip', folder_path)

    return send_file(zip_file_path, as_attachment=True)

@socketio.on('connect')
def handle_connect():
    """Gerencia conexão do cliente"""
    client_id = request.sid
    active_clients.add(client_id)
    logger.info(f"Cliente conectado: {client_id}")
    emit('client_id', {'client_id': client_id})

@socketio.on('disconnect')
def handle_disconnect():
    """Gerencia desconexão do cliente"""
    client_id = request.sid
    active_clients.discard(client_id)
    logger.info(f"Cliente desconectado: {client_id}")

@app.errorhandler(404)
def not_found_error(error):
    """Trata erro 404"""
    return jsonify({'error': 'Página não encontrada'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Trata erro 500"""
    logger.error(f"Erro interno do servidor: {str(error)}")
    return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/health')
def health_check():
    """Endpoint para verificação de saúde da aplicação"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_clients': len(active_clients),
        'queue_size': download_queue.qsize()
    })

if __name__ == '__main__':
    try:
        # Inicia o processador de fila em uma thread separada
        download_thread = threading.Thread(target=process_download_queue, daemon=True)
        download_thread.start()
        
        # Inicia o servidor Flask com SocketIO
        socketio.run(
            app,
            debug=True,
            host='0.0.0.0',
            port=5000,
            allow_unsafe_werkzeug=True,
            log_output=True
        )
    except Exception as e:
        logger.critical(f"Erro fatal ao iniciar aplicação: {str(e)}")
        raise

E no codigo html:

<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Cyber Site Downloader</title>
    <link
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
      rel="stylesheet"
    />
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      }

      :root {
        --primary-color: #00ff88;
        --dark-bg: #1a1a1a;
        --darker-bg: #0f0f0f;
        --light-text: #ffffff;
        --gray-text: #b3b3b3;
        --error-color: #ff4444;
        --success-color: #00cc6a;
      }

      body {
        background: var(--dark-bg);
        color: var(--light-text);
        min-height: 100vh;
        line-height: 1.6;
      }

      .container {
        max-width: 1000px;
        margin: 0 auto;
        padding: 20px;
      }

      header {
        text-align: center;
        padding: 40px 20px;
        background: linear-gradient(45deg, #2b2b2b, #1a1a1a);
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        border: 1px solid #333;
      }

      h1 {
        color: var(--primary-color);
        margin-bottom: 15px;
        font-size: 2.5em;
        text-transform: uppercase;
        letter-spacing: 2px;
      }

      .description {
        color: var(--gray-text);
        margin-bottom: 20px;
        font-size: 1.1em;
      }

      .connection-status {
        padding: 10px;
        border-radius: 5px;
        font-size: 0.9em;
        margin-top: 10px;
      }

      .connected {
        background: var(--success-color);
        color: white;
      }

      .disconnected {
        background: var(--error-color);
        color: white;
      }

      .main-content {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 20px;
        margin-bottom: 30px;
      }

      .url-input-container {
        background: #2b2b2b;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid #333;
      }

      .input-group {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
      }

      .input-group .btn {
        flex: 1;
      }
      #downloadFolderBtn {
        background: #4a90e2; /* Cor diferente para distinguir */
      }

      #downloadFolderBtn:hover {
        background: #357abd;
      }

      #downloadFolderBtn.disabled {
        background: #666;
        cursor: not-allowed;
        pointer-events: none;
      }

      input[type="url"] {
        flex: 1;
        padding: 15px;
        border: 1px solid #444;
        background: #333;
        color: var(--light-text);
        border-radius: 8px;
        outline: none;
        font-size: 1em;
        transition: all 0.3s ease;
      }

      input[type="url"]:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 5px rgba(0, 255, 136, 0.3);
      }

      input[type="url"].error {
        border-color: var(--error-color);
        box-shadow: 0 0 5px rgba(255, 68, 68, 0.3);
      }

      .error-text {
        color: var(--error-color);
        font-size: 0.9em;
        margin-top: 5px;
        display: none;
      }

      .btn {
        background: var(--primary-color);
        color: var(--dark-bg);
        border: none;
        padding: 12px 25px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: bold;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
      }

      .btn i {
        font-size: 1.1em;
      }

      .btn:hover {
        background: var(--success-color);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 255, 136, 0.2);
      }

      .btn:disabled {
        background: #666;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
      }

      #downloadProgress {
        display: none;
        margin-top: 20px;
        padding: 20px;
        background: #333;
        border-radius: 10px;
      }

      .progress-container {
        margin-top: 15px;
      }

      .progress-bar {
        width: 100%;
        height: 20px;
        background: #444;
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 10px;
      }

      .progress {
        width: 0%;
        height: 100%;
        background: linear-gradient(
          45deg,
          var(--primary-color),
          var(--success-color)
        );
        transition: width 0.3s ease;
      }

      #urlList {
        background: #2b2b2b;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid #333;
        max-height: 400px;
        overflow-y: auto;
      }

      .url-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px;
        background: #333;
        margin-bottom: 10px;
        border-radius: 8px;
        transition: all 0.3s ease;
      }

      .url-item:hover {
        background: #3a3a3a;
        transform: translateX(5px);
      }

      .url-text {
        flex: 1;
        margin-right: 15px;
        word-break: break-all;
      }

      .delete-btn {
        background: var(--error-color);
        padding: 8px 15px;
        font-size: 0.9em;
      }

      .delete-btn:hover {
        background: #cc0000;
      }

      #logsContainer {
        background: #1a1a1a;
        border: 1px solid #333;
        padding: 20px;
        margin-top: 20px;
        border-radius: 10px;
        max-height: 300px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 0.9em;
      }

      .log-entry {
        padding: 5px 0;
        border-bottom: 1px solid #333;
        color: var(--primary-color);
      }

      .status-message {
        padding: 15px;
        margin: 20px 0;
        border-radius: 8px;
        display: none;
        animation: fadeIn 0.3s ease;
      }

      .status-success {
        background: var(--success-color);
      }

      .status-error {
        background: var(--error-color);
      }

      @keyframes fadeIn {
        from {
          opacity: 0;
          transform: translateY(-10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      /* Scrollbar personalizada */
      ::-webkit-scrollbar {
        width: 8px;
      }

      ::-webkit-scrollbar-track {
        background: #1a1a1a;
      }

      ::-webkit-scrollbar-thumb {
        background: #444;
        border-radius: 4px;
      }

      ::-webkit-scrollbar-thumb:hover {
        background: #555;
      }

      /* Responsividade */
      @media (max-width: 768px) {
        .main-content {
          grid-template-columns: 1fr;
        }

        .container {
          padding: 10px;
        }

        header {
          padding: 30px 15px;
        }

        h1 {
          font-size: 2em;
        }

        .input-group {
          flex-direction: column;
        }

        .btn {
          width: 100%;
          justify-content: center;
        }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <header>
        <h1><i class="fas fa-download"></i> Cyber Site Downloader</h1>
        <p class="description">Ferramenta avançada para download de sites</p>
        <div id="connectionStatus" class="connection-status">
          Conectando ao servidor...
        </div>
      </header>

      <div class="main-content">
        <div class="url-input-container">
          <div class="input-group">
            <input
              type="url"
              id="urlInput"
              placeholder="Digite a URL do site (ex: https://exemplo.com)"
              required
            />
            <button class="btn" onclick="addURL()" id="addUrlBtn" disabled>
              <i class="fas fa-plus"></i> Adicionar URL
            </button>
          </div>
          <p id="urlError" class="error-text">
            URL inválida. Certifique-se de incluir http:// ou https://
          </p>

          <div class="input-group">
            <button
              class="btn"
              id="startDownload"
              onclick="startDownload()"
              disabled
            >
              <i class="fas fa-cloud-download-alt"></i> Iniciar Downloads
            </button>
            <button
              class="btn"
              id="downloadFolderBtn"
              onclick="downloadFolder()"
            >
              <i class="fas fa-file-archive"></i> Baixar Pasta
            </button>
          </div>

          <div id="downloadProgress">
            <h3>Progresso do Download</h3>
            <div class="progress-container">
              <div class="progress-bar">
                <div class="progress" id="progressBar"></div>
              </div>
              <p id="progressText">0%</p>
            </div>
          </div>
        </div>

        <div id="urlList">
          <h3>URLs Adicionadas</h3>
          <div id="urls"></div>
        </div>
      </div>

      <div id="logsContainer">
        <div class="log-entry">Aguardando conexão com o servidor...</div>
      </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
      let socket;
      let urlList = [];
      let downloadInProgress = false;
      let clientId = null;
      let folderName = ""; // Variável global para armazenar o nome da pasta

      // Inicializa Socket.IO com retry automático
      function initializeSocket() {
        socket = io({
          reconnection: true,
          reconnectionAttempts: 5,
          reconnectionDelay: 1000,
        });

        socket.on("connect", () => {
          console.log("Conectado ao servidor");
          updateConnectionStatus(true);
          document.getElementById("addUrlBtn").disabled = false;
        });

        socket.on("disconnect", () => {
          console.log("Desconectado do servidor");
          updateConnectionStatus(false);
          document.getElementById("addUrlBtn").disabled = true;
        });

        socket.on("client_id", (data) => {
          clientId = data.client_id;
          console.log("ID do cliente recebido:", clientId);
          addLog("Conectado e pronto para downloads");
        });

        socket.on("progress", handleProgress);
        socket.on("log", handleLog);
      }

      function updateConnectionStatus(connected) {
        const statusDiv = document.getElementById("connectionStatus");
        if (connected) {
          statusDiv.className = "connection-status connected";
          statusDiv.textContent = "Conectado ao servidor";
        } else {
          statusDiv.className = "connection-status disconnected";
          statusDiv.textContent = "Desconectado do servidor";
        }
      }

      function validateUrl(url) {
        try {
          new URL(url);
          return true;
        } catch {
          return false;
        }
      }

      function addURL() {
        const urlInput = document.getElementById("urlInput");
        const url = urlInput.value.trim();
        const urlError = document.getElementById("urlError");

        if (!url) {
          showError("Por favor, insira uma URL");
          return;
        }

        if (!validateUrl(url)) {
          showError(
            "URL inválida. Certifique-se de incluir http:// ou https://"
          );
          urlInput.classList.add("url-error");
          urlError.style.display = "block";
          return;
        }

        if (urlList.includes(url)) {
          showError("Esta URL já foi adicionada");
          return;
        }

        urlInput.classList.remove("url-error");
        urlError.style.display = "none";
        urlList.push(url);
        updateURLList();
        urlInput.value = "";
        document.getElementById("startDownload").disabled = false;
        addLog(`URL adicionada: ${url}`);
      }

      function removeURL(index) {
        const removedUrl = urlList[index];
        urlList.splice(index, 1);
        updateURLList();
        document.getElementById("startDownload").disabled =
          urlList.length === 0;
        addLog(`URL removida: ${removedUrl}`);
      }

      function updateURLList() {
        const urlsDiv = document.getElementById("urls");
        urlsDiv.innerHTML = "";

        urlList.forEach((url, index) => {
          const urlItem = document.createElement("div");
          urlItem.className = "url-item";
          urlItem.innerHTML = `
                    <span class="url-text">${url}</span>
                    <button class="btn delete-btn" onclick="removeURL(${index})">
                        <i class="fas fa-trash"></i>
                    </button>
                `;
          urlsDiv.appendChild(urlItem);
        });
      }

      function showError(message) {
        const existingError = document.querySelector(".status-message");
        if (existingError) {
          existingError.remove();
        }

        const statusDiv = document.createElement("div");
        statusDiv.className = "status-message status-error";
        statusDiv.textContent = message;

        const container = document.querySelector(".container");
        container.insertBefore(
          statusDiv,
          document.querySelector(".main-content")
        );

        statusDiv.style.display = "block";
        setTimeout(() => {
          statusDiv.remove();
        }, 3000);
      }

      function showSuccess(message) {
        const existingSuccess = document.querySelector(".status-message");
        if (existingSuccess) {
          existingSuccess.remove();
        }

        const statusDiv = document.createElement("div");
        statusDiv.className = "status-message status-success";
        statusDiv.textContent = message;

        const container = document.querySelector(".container");
        container.insertBefore(
          statusDiv,
          document.querySelector(".main-content")
        );

        statusDiv.style.display = "block";
        setTimeout(() => {
          statusDiv.remove();
        }, 3000);
      }

      function addLog(message) {
        const logEntry = document.createElement("div");
        logEntry.className = "log-entry";
        logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;

        const logsContainer = document.getElementById("logsContainer");
        logsContainer.appendChild(logEntry);
        logsContainer.scrollTop = logsContainer.scrollHeight;

        // Limite de logs para evitar consumo excessivo de memória
        const maxLogs = 100;
        const logs = logsContainer.getElementsByClassName("log-entry");
        if (logs.length > maxLogs) {
          logsContainer.removeChild(logs[0]);
        }
      }

      function handleProgress(data) {
        const { url, status, progress } = data;
        const progressBar = document.getElementById("progressBar");
        const progressText = document.getElementById("progressText");
        const progressDiv = document.getElementById("downloadProgress");
        const downloadFolderBtn = document.getElementById("downloadFolderBtn");

        progressDiv.style.display = "block";
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${progress}%`;

        switch (status) {
          case "starting":
            downloadFolderBtn.classList.add("disabled");
            addLog(`Iniciando download de: ${url}`);
            break;
          case "downloading":
            downloadFolderBtn.classList.add("disabled");
            break;
          case "completed":
            downloadFolderBtn.classList.remove("disabled");
            addLog(`Download completo: ${url}`);
            showSuccess(`Download concluído: ${url}`);
            break;
          case "error":
            downloadFolderBtn.classList.add("disabled");
            showError(`Erro no download de ${url}`);
            addLog(`Erro no download: ${url}`);
            break;
        }

        if (progress === 100) {
          setTimeout(() => {
            downloadInProgress = false;
            progressDiv.style.display = "none";
            urlList = [];
            updateURLList();
            document.getElementById("startDownload").disabled = true;
            showSuccess("Todos os downloads concluídos");
          }, 2000);
        }
      }
      function handleLog(data) {
        addLog(data.message);
      }

      function startDownload() {
        if (downloadInProgress || !clientId || urlList.length === 0) {
          showError("Não é possível iniciar o download agora");
          return;
        }

        downloadInProgress = true;
        const progressDiv = document.getElementById("downloadProgress");
        const downloadFolderBtn = document.getElementById("downloadFolderBtn");
        progressDiv.style.display = "block";
        downloadFolderBtn.classList.add("disabled");

        addLog("Iniciando processo de download...");

        // Defina o nome da pasta com base no número de URLs
        folderName = `Cyber${urlList.length}`;

        fetch("/api/download", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            urls: urlList,
            client_id: clientId,
          }),
        })
          .then((response) => {
            if (!response.ok) {
              throw new Error("Erro na resposta do servidor");
            }
            return response.json();
          })
          .then((data) => {
            if (data.error) {
              throw new Error(data.error);
            }
            addLog("Downloads iniciados com sucesso");
            showSuccess("Downloads iniciados");
          })
          .catch((error) => {
            showError(error.message || "Erro ao iniciar downloads");
            downloadInProgress = false;
            progressDiv.style.display = "none";
            console.error("Error:", error);
          });
      }

      function downloadFolder() {
        const folderNumber = document.querySelectorAll(".log-entry").length; // Usar número de logs como referência
        const folderName = `Cyber${folderNumber}`;
        window.location.href = `/download/${folderName}`;
        addLog("Iniciando download da pasta compactada...");
      }

      // Adicione no início do script, junto com as outras variáveis globais
      let currentFolderNumber = 1;

      // Eventos de teclado e carregamento
      document.addEventListener("DOMContentLoaded", () => {
        initializeSocket();

        const urlInput = document.getElementById("urlInput");
        urlInput.addEventListener("keypress", function (e) {
          if (
            e.key === "Enter" &&
            !document.getElementById("addUrlBtn").disabled
          ) {
            addURL();
          }
        });

        urlInput.addEventListener("input", function () {
          this.classList.remove("url-error");
          document.getElementById("urlError").style.display = "none";
        });
      });
    </script>
  </body>
</html>

Houve um erro ao fazer o download:

FileNotFoundError: [Errno 2] No such file or directory: 'downloads/Cyber100'

Traceback (most recent call last)
File "/home/estevam/Documentos/w3b-5cr4p1ng/venv/lib/python3.13/site-packages/flask/app.py", line 1514, in wsgi_app
response = self.handle_exception(e)
           ^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/estevam/Documentos/w3b-5cr4p1ng/venv/lib/python3.13/site-packages/flask/app.py", line 1511, in wsgi_app
response = self.full_dispatch_request()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/estevam/Documentos/w3b-5cr4p1ng/venv/lib/python3.13/site-packages/flask/app.py", line 919, in full_dispatch_request
rv = self.handle_user_exception(e)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/estevam/Documentos/w3b-5cr4p1ng/venv/lib/python3.13/site-packages/flask/app.py", line 917, in full_dispatch_request
rv = self.dispatch_request()
     ^^^^^^^^^^^^^^^^^^^^^^^
File "/home/estevam/Documentos/w3b-5cr4p1ng/venv/lib/python3.13/site-packages/flask/app.py", line 902, in dispatch_request
return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/estevam/Documentos/w3b-5cr4p1ng/app.py", line 243, in download_folder
shutil.make_archive(folder_path, 'zip', folder_path)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/lib/python3.13/shutil.py", line 1153, in make_archive
stmd = os.stat(root_dir).st_mode
       ^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'downloads/Cyber100'
The debugger caught an exception in your WSGI application. You can now look at the traceback which led to the error.
To switch between the interactive traceback and the plaintext one, you can click on the "Traceback" headline. From the text traceback you can also create a paste of it.