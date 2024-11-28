# Pare os containers existentes
sudo docker-compose down

# Remova as imagens antigas
sudo docker-compose down --rmi all

# Limpe os caches do Docker (opcional)
sudo docker system prune -a

# Reconstrua e inicie
sudo docker-compose up --build