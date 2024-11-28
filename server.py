from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import subprocess
import os
from datetime import datetime
import time
import queue
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cyber-download-secret'
socketio = SocketIO(app)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fila para gerenciar downloads
download_queue = queue.Queue()
current_downloads = {}

def create_cyber_folder(counter):
    """Cria uma pasta com o prefixo Cyber e um número"""
    folder_name = f"Cyber{counter}"
    os.makedirs(folder_name, exist_ok=True)
    return folder_name

def download_site(url, folder_name, client_id):
    """Faz o download de um site específico"""
    logger.info(f"Iniciando download de: {url}")
    socketio.emit('log', {'message': f"Iniciando download de: {url}"}, room=client_id)
    
    wget_command = [
        "wget",
        "--mirror",
        "--convert-links",
        "--adjust-extension",
        "--page-requisites",
        "--no-parent",
        "--no-verbose",
        "--directory-prefix=" + folder_name,
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        url
    ]
    
    try:
        process = subprocess.Popen(
            wget_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                socketio.emit('log', {'message': output.strip()}, room=client_id)
        
        rc = process.poll()
        if rc == 0:
            logger.info(f"Download concluído com sucesso: {url}")
            socketio.emit('log', {'message': f"Download concluído com sucesso: {url}"}, room=client_id)
            return True
        else:
            logger.error(f"Erro no download de {url}")
            socketio.emit('log', {'message': f"Erro no download de {url}"}, room=client_id)
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
                folder_name = create_cyber_folder(counter)
                
                socketio.emit('progress', {
                    'url': url,
                    'status': 'downloading',
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def start_download():
    data = request.json
    urls = data.get('urls', [])
    client_id = data.get('client_id')  # Recebe o client_id do frontend
    
    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400
    
    if not client_id:
        return jsonify({'error': 'No client ID provided'}), 400
    
    for url in urls:
        download_queue.put((url, client_id))
    
    return jsonify({'message': 'Downloads queued successfully'})

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    logger.info(f"Cliente conectado: {client_id}")
    emit('client_id', {'client_id': client_id})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Cliente desconectado: {request.sid}")

if __name__ == '__main__':
    # Inicia o processador de fila em uma thread separada
    download_thread = threading.Thread(target=process_download_queue, daemon=True)
    download_thread.start()
    
    # Inicia o servidor Flask com SocketIO
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
