#!/bin/bash

apt update -y
apt install -y docker.io

systemctl start docker
systemctl enable docker

usermod -aG docker ubuntu

echo "Docker installed successfully" > /home/ubuntu/setup.log