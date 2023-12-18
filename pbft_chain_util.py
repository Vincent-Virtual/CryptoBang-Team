#from ellipticcurve.eddsa import Eddsa
import uuid
from Crypto.Hash import SHA256
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

class ChainUtil:
    # ed25519 allows us to create key pair from secret
   # eddsa = Eddsa("ed25519")
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # a static function to return keypair generated using a secret phrase
    @staticmethod
    def gen_key_pair(secret):

        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        secret_bytes = secret.encode('utf-8')
        signature = private_key.sign(secret_bytes)
        return signature

    # returns ids used in transactions
    @staticmethod
    def generate_id():
        return str(uuid.uuid4())

    # hashes any data using SHA256
    @staticmethod
    def hash_data(data):
        return SHA256.new(data.encode()).hexdigest()

    # verifies the signed hash by decrypting it with public key
    # and matching it with the hash
    @staticmethod
    def verify_signature(public_key, signature, data_hash):
        try:
            public_key.verify(public_key, data_hash, sig_alg=ed25519.Ed25519())
            return True
        except InvalidSignature:
            return False
#
# # Example usage:
# public_key_bytes = b'\x01\x23\x45\x67\x89\xab\xcd\xef'  # Replace with your actual public key bytes
# signature_bytes = b'\x01\x23\x45\x67\x89\xab\xcd\xef'  # Replace with your actual signature bytes
# data_bytes = b'Your data'  # Replace with your actual data bytes


# def verify_signature(public_key_bytes, signature_bytes, data_bytes):
#     pass
#
#
# if verify_signature(public_key_bytes, signature_bytes, data_bytes):
#     print("Signature is valid.")
# else:
#     print("Signature is invalid.")
# ff = str(uuid.uuid4())
# print(ff)
