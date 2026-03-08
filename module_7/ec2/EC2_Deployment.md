# EC2 Deployment Steps

1. Launched EC2 instance (Ubuntu 22.04, t3.micro)

2. Installed Docker and Compose

sudo apt update
sudo apt install docker.io docker-compose-plugin -y

3. Cloned repository

git clone <repo>

4. Started services

docker compose up -d --build

5. Verified services

docker compose ps

6. Accessed web app

http://<EC2_PUBLIC_IP>:8080