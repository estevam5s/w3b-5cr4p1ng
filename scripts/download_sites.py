import subprocess
import os
from datetime import datetime
import time

# Lista de URLs para download
urls = [
    "https://themes.potenzaglobalsolutions.com/html/it-infinite/",
    "https://elementor.deverust.com/encrypt/template-kit/home/",
    "https://askproject.net/fortnet/home/",
    "https://freevetis.com/cybersp",
    "https://dkkit.rometheme.pro/devshield/",
    "https://cyberciti.1onestrong.com/",
    "https://shine.creativemox.com/sentinelpro/template-kit/home/",
    "https://kitpro.site/cyberty",
    "https://askproject.net/cyrion/home/",
    "https://templateup.site/lockbyte/",
    "https://freevetis.com/cyberb/",
    "https://demo.moxcreative.com/vanguard/template-kit/homepage/",
    "https://template-kit.evonicmedia.com/layout60/",
    "https://templates.heydenstd.com/securety/template-kit/home/",
    "https://tykit.rometheme.pro/tenet/",
    "https://www.wordpress.codeinsolution.com/jarvis/",
    "https://demo.moxcreative.com/hasto/template-kit/homepage/"
]

def create_cyber_folder(counter):
    """Cria uma pasta com o prefixo Cyber e um número"""
    folder_name = f"Cyber{counter}"
    os.makedirs(folder_name, exist_ok=True)
    return folder_name

def download_site(url, folder_name):
    """Faz o download de um site específico"""
    print(f"\nIniciando download de: {url}")
    print(f"Salvando em: {folder_name}")
    
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
        process = subprocess.Popen(wget_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            print(f"Download concluído com sucesso: {url}")
            return True
        else:
            print(f"Erro no download de {url}")
            print(f"Erro: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"Erro ao executar o download de {url}: {str(e)}")
        return False

def main():
    counter = 1
    total_sites = len(urls)
    successful_downloads = 0
    
    for index, url in enumerate(urls, 1):
        print(f"\nProcessando site {index}/{total_sites}")
        
        # Cria pasta com o prefixo Cyber e o contador atual
        folder_name = create_cyber_folder(counter)
        
        if download_site(url, folder_name):
            successful_downloads += 1
            counter += 1  # Só incrementa o contador se o download for bem-sucedido
        
        # Aguarda 5 segundos entre downloads
        if index < total_sites:
            print("Aguardando 5 segundos antes do próximo download...")
            time.sleep(5)
    
    # Relatório final
    print(f"\nDownload finalizado!")
    print(f"Sites processados com sucesso: {successful_downloads}/{total_sites}")
    print(f"Último diretório criado: Cyber{counter-1}")

if __name__ == "__main__":
    main()