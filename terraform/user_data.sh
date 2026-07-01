#!/bin/bash

apt update -y

# Install Docker
apt install -y docker.io

# Install Docker Compose V2 plugin (IMPORTANT)
apt install -y docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

echo "Docker + Compose installed successfully" > /home/ubuntu/setup.log