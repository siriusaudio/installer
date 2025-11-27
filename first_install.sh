#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

sudo apt update
sudo apt upgrade -y

sudo apt install python3-venv python3 whois -y

sudo useradd -s /bin/bash siriusaudio_daemon
PASSWORD=$(mkpasswd -m sha-512 siriusaudio)
echo "siriusaudio_daemon:${PASSWORD}" | sudo chpasswd

sudo usermod -aG sudo siriusaudio_daemon
sudo echo "siriusaudio_daemon ALL=(ALL:ALL) NOPASSWD: ALL" | sudo tee "/etc/sudoers.d/dont-prompt-siriusaudio_daemon-for-sudo-password"

sudo mkdir -p /var/lib/sirius-installer
sudo mkdir -p /var/lib/sirius-installer/.keys

sudo chown -R siriusaudio_daemon /var/lib/sirius-installer

python3 -m venv /var/lib/sirius-installer/.venv

source /var/lib/sirius-installer/.venv/bin/activate
pip install -r requirements.txt
source ./authentication-key.txt
./client.py register $AUTH_KEY 217.144.56.118

# Copy run_update.sh and give execute permissions
cp ./run_update.sh /var/lib/sirius-installer/
cp ./client.py /var/lib/sirius-installer/
cp ./authentication-key.txt /var/lib/sirius-installer/
chmod +x /var/lib/sirius-installer/run_update.sh

# Copy systemd service file
sudo cp ./sirius-authenticate.service /lib/systemd/system/sirius-authenticate.service

# Enable systemd service to run at boot
sudo systemctl enable sirius-authenticate.service

# Add cron job to run update script daily at 3am
(crontab -l 2>/dev/null; echo "0 3 * * * /var/lib/sirius-installer/run_update.sh") | crontab -

sudo systemctl restart sirius-authenticate.service

