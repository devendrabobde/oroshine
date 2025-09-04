#!/bin/bash
# Update the package list
sudo apt update

# Install necessary dependencies
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up Docker stable repository
echo "deb [signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Add the current user to the docker group to run Docker without sudo
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Display Docker and Docker Compose versions
docker --version
docker-compose --version

cd /home/ubuntu
sudo apt install -y git 
git clone https://github.com/devendrabobde/oroshine.git
ls -ltr
cd oroshine/oroshine_app/
pwd
echo " Inside oroshine/oroshine_app/ "
ls -ltr
echo " after this we will run docker-compose"
sudo docker-compose down && docker-compose up -d















