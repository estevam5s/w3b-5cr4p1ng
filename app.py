# ------------------------------------------------------------------------------
# Vercsao nova
# ------------------------------------------------------------------------------
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import subprocess
import os
from datetime import datetime
import time
import queue
import logging
import eventlet
from urllib.parse import urlparse

# Patch para o eventlet
eventlet.monkey_patch()

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
        # Cria pasta de downloads e logs se não existirem
        os.makedirs('downloads', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
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