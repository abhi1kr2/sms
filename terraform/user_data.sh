#!/bin/bash

set -e

apt update -y

apt install -y \
  docker.io \
  docker-compose \
  awscli \
  git

systemctl start docker
systemctl enable docker

usermod -aG docker ubuntu

mkdir -p /home/ubuntu/sms
chown -R ubuntu:ubuntu /home/ubuntu/sms

{
  echo "===== Setup Completed ====="
  docker --version
  docker-compose --version
  aws --version
  git --version
} > /home/ubuntu/setup.log

chown ubuntu:ubuntu /home/ubuntu/setup.log