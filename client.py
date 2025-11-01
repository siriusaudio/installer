#!/usr/bin/env python3
import os
import sys
import uuid
import json
import requests
import zipfile
import tempfile
import subprocess
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

CLIENT_PRIVATE = "/var/lib/sirius-installer/.keys/client_private.pem"
CLIENT_PUBLIC = "/var/lib/sirius-installer/.keys/client_public.pem"


def get_mac() -> str:
    node = uuid.getnode()
    mac = ':'.join(f"{(node >> ele) & 0xff:02x}" for ele in range(40, -1, -8))
    if mac == "00:00:00:00:00:00":
        raise RuntimeError("No MAC address found")
    return mac


def generate_keypair() -> (rsa.RSAPrivateKey, rsa.RSAPublicKey):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
    public_key = private_key.public_key()

    # write private key (PKCS8 PEM)
    with open(CLIENT_PRIVATE, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # write public key (SubjectPublicKeyInfo PEM)
    with open(CLIENT_PUBLIC, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    return private_key, public_key


def load_keys() -> (rsa.RSAPrivateKey, rsa.RSAPublicKey):
    with open(CLIENT_PRIVATE, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
    with open(CLIENT_PUBLIC, "rb") as f:
        public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
    return private_key, public_key


def sign_data(private_key: rsa.RSAPrivateKey, data: str) -> bytes:
    signature = private_key.sign(
        data.encode(),
        padding.PKCS1v15(),        
        hashes.SHA256()
    )
    return signature


def main():
    if len(sys.argv) < 3:
        print("Usage: python client.py <register|authenticate> [ACTIVATION_KEY] <SERVER_IP>")
        sys.exit(1)

    mode = sys.argv[1]
    activation_key = ""
    server_ip = ""

    if mode == "register":
        if len(sys.argv) < 4:
            print("Usage for registration: python client.py register <ACTIVATION_KEY> <SERVER_IP>")
            sys.exit(1)
        activation_key = sys.argv[2]
        server_ip = sys.argv[3]
    elif mode == "authenticate":
        server_ip = sys.argv[2]
    else:
        print('Unknown mode. Use "register" or "authenticate".')
        sys.exit(1)

    mac = get_mac()

    if not (Path(CLIENT_PRIVATE).exists() and Path(CLIENT_PUBLIC).exists()):
        private_key, public_key = generate_keypair()
    else:
        private_key, public_key = load_keys()

    if mode == "register":
        reg_data = mac + activation_key
        signature = sign_data(private_key, reg_data)
        with open(CLIENT_PUBLIC, "r", encoding="utf-8") as f:
            pub_pem = f.read()
        payload = {
            "mac": mac,
            "activationKey": activation_key,
            "publicKey": pub_pem,
            "signature": signature.hex()
        }
        url = f"http://{server_ip}:3000/register"
        res = requests.post(url, json=payload)
        print("Registration:", res.text)
    else:  # authenticate
        auth_sig = sign_data(private_key, mac)
        with open(CLIENT_PUBLIC, "r", encoding="utf-8") as f:
            pub_pem = f.read()
        payload = {
            "mac": mac,
            "publicKey": pub_pem,
            "signature": auth_sig.hex()
        }
        url = f"http://{server_ip}:3000/authenticate"
        res = requests.post(url, json=payload)
        # Check if response is a zip file
        if res.headers.get("Content-Type") == "application/zip":
            # with tempfile.TemporaryDirectory() as tmpdir:
            #     zip_path = os.path.join(tmpdir, "response.zip")
            #     with open(zip_path, "wb") as f:
            #         f.write(res.content)
            #     with zipfile.ZipFile(zip_path, "r") as zip_ref:
            #         zip_ref.extractall(tmpdir)
            #     install_sh = os.path.join(tmpdir, "install.sh")
            #     if os.path.exists(install_sh):
            #         os.chmod(install_sh, 0o755)
            #         subprocess.run([install_sh], check=True, cwd=tmpdir)
            #     else:
            #         print("install.sh not found in the zip file.")
            zip_path = os.path.join(os.getcwd(), "response.zip")
            with open(zip_path, "wb") as f:
                f.write(res.content)
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(os.getcwd())
            install_sh = os.path.join(os.getcwd(), "install.sh")
            if os.path.exists(install_sh):
                os.chmod(install_sh, 0o755)
                subprocess.run([install_sh], check=True, cwd=os.getcwd())
            else:
                print("install.sh not found in the zip file.")
        else:
            print("Authentication:", res.text)


if __name__ == "__main__":
    main()
