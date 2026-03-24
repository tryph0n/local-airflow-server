USER_DATA_SCRIPT = """#!/bin/bash
exec > /var/log/user-data-debug.log 2>&1
set -x
ufw allow 22/tcp

echo "--> STARTING SETUP"

export DEBIAN_FRONTEND=noninteractive

echo "--> Installing Apt Packages..."
apt-get update
apt-get install -y docker.io git python3-pip python3-venv

echo "--> Configuring Docker..."
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu
while [ ! -S /var/run/docker.sock ]; do echo "Waiting for Docker Socket..."; sleep 1; done
chmod 666 /var/run/docker.sock

echo "--> Installing Python Libs..."
sudo -u ubuntu pip3 install mlflow boto3 --break-system-packages

ln -s /home/ubuntu/.local/bin/mlflow /usr/bin/mlflow

echo "--> SETUP COMPLETE"
shutdown -h +180
touch /tmp/airflow_ready
"""
