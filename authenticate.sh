#!/bin/bash

source /var/lib/sirius-installer/.venv/bin/activate
SERVER_IP="217.144.56.118"
python3 /var/lib/sirius-installer/client.py authenticate $SERVER_IP
