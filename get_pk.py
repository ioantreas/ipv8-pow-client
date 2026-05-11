from ipv8.keyvault.crypto import default_eccrypto

with open("mykey.pem", "rb") as f:
    key_data = f.read()

key = default_eccrypto.key_from_private_bin(key_data)

print(key.pub().key_to_bin().hex())