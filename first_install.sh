#!/bin/bash

sudo useradd -s /bin/bash siriusaudio_daemon
PASSWORD=$(mkpasswd -m sha-512 siriusaudio)
echo "siriusaudio_daemon:${PASSWORD}" | sudo chpasswd

mkdir -p /var/lib/sirius-installer
mkdir -p /var/lib/sirius-installer/.keys
apt install python3-venv python3 whois -y

python3 -m venv /var/lib/sirius-installer/.venv

source /var/lib/sirius-installer/.venv/bin/activate
pip install -r requirements.txt
source ./authentication_key.txt
./client.py register $AUTH_KEY 217.144.56.118

# Copy authenticate.sh and give execute permissions
cp ./authenticate.sh /var/lib/sirius-installer/
cp ./client.py /var/lib/sirius-installer/
cp ./authentication_key.txt /var/lib/sirius-installer/
chmod +x /var/lib/sirius-installer/authenticate.sh

# Copy systemd service file
cp ./sirius-authenticate.service /lib/systemd/system/sirius-authenticate.service

pushd /var/lib/sirius-installer/
sudo /var/lib/sirius-installer/authenticate.sh
popd


