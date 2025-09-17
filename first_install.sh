#!/bin/bash

mkdir -p /var/lib/sirius-installer
mkdir -p /var/lib/sirius-installer/.keys
apt install python3-venv python3 -y
python3 -m venv /var/lib/sirius-installer/.venv

source /var/lib/sirius-installer/.venv/bin/activate
pip install -r requirements.txt
source ./authentication_key.txt
./client.py register $AUTH_KEY 217.144.56.118

