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
chmod +x /var/lib/sirius-installer/run_update.sh

# Copy systemd service file
cp ./sirius-authenticate.service /lib/systemd/system/sirius-authenticate.service

pushd /var/lib/sirius-installer/
sudo /var/lib/sirius-installer/run_update.sh
popd

# Enable systemd service to run at boot
sudo systemctl enable sirius-authenticate.service

# Add cron job to run update script daily at 3am
(crontab -l 2>/dev/null; echo "0 3 * * * /var/lib/sirius-installer/run_update.sh") | crontab -


