from pbft_chain_util import ChainUtil  # Assuming you have a ChainUtil module with the required functions
from cryptography.hazmat.primitives import serialization

from pbft_transaction import Transaction  # Assuming you have a Transaction class defined
from cryptography.hazmat.primitives.asymmetric import ed25519


class Wallet:
    def __init__(self, secret):
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        secret_bytes = secret.encode('utf-8')
        signature = private_key.sign(secret_bytes)

        self.public_key_hex = public_key.public_bytes(
            # encoding=ed25519.Encoding.Raw,
            # format=ed25519.PublicFormat.Raw
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        ).hex()
        self.signature_hex = signature.hex()

        # Additional code related to ChainUtil, assuming it has a similar structure
        # Replace this with the actual implementation in your code
        # For example, self.key_pair = ChainUtil.gen_key_pair(secret)

        # Print statements for testing
        print(f"{secret} in the Wallet section")
        print(f"Public Key: {self.public_key_hex}")
        print(f"Signature: {self.signature_hex}")

    def __str__(self):
        return f"Wallet - \n" \
               f"    publicKey: {self.public_key}"

    def sign(self, data_hash):
        return self.key_pair.sign(data_hash.encode()).hex()

    def create_transaction(self, data):
        return Transaction(data, self)

    def get_public_key(self):
        #return self.public_key
        return self.public_key_hex

# Assuming you have a ChainUtil module with the required functions
# and a Transaction class defined
