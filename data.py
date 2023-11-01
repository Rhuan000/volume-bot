import os
import json
from decimal import Decimal
from cryptography.fernet import Fernet
from wallet import Wallet

# Generate and save the key
with open('axbsz', "r") as file:
    key=file.readline()
    if key=="":
        key = Fernet.generate_key()
        with open('axbsz', "w") as file:
            file.write(key.decode())

    cipher = Fernet(key)


def write_data(datas):
    class WalletEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Wallet):
                # Define how to serialize a Wallet object
                return {
                    "private_key": obj.private_key,
                    "name": obj.name,
                    "address": obj.address,
                    "BNB_AMOUNT": obj.BNB_AMOUNT,
                    "TOKEN_AMOUNT": obj.tokens,
                    "active": obj.active,
                    "operation": obj.operation
                    # Add other attributes as needed
                }
            elif isinstance(obj, Decimal):
                # Serialize Decimal objects as strings
                return float(obj)
            return super().default(obj)
        
    encrypted_datas = []
    for data in datas:
        data = json.dumps(data, cls=WalletEncoder)
        data = cipher.encrypt(data.encode())
        encrypted_datas.append(data)
    
    with open("encrypted_data.txt", "wb") as file:
        for encrypted_data in encrypted_datas:
            file.write(encrypted_data + b'\n')


def read_data() -> [Wallet]:
    with open("encrypted_data.txt", "rb") as file:  # Open the file in binary read mode
        encrypted_datas = file.readlines()
        decrypted_datas = []
        for encrypted_data in encrypted_datas:
            decrypted_data = cipher.decrypt(encrypted_data).rstrip(b'\n')  # Convert to bytes and remove newline character
            original_data = json.loads(decrypted_data.decode())  # Decode to string and parse JSON
            decrypted_datas.append(Wallet(original_data['private_key'], original_data['name']))
    return decrypted_datas
