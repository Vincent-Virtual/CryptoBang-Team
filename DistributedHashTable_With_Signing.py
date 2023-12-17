import hashlib
import time
import cryptography

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

class DataNode:
    def __init__(self, data, private_key):
        self.data = data
        self.hash = self.generate_hash()
        self.size = len(data)
        self.signature = self.sign_data(private_key)
        self.timestamp = time.time()

    def generate_hash(self):
        return hashlib.sha256(self.data.encode()).hexdigest()

    def sign_data(self, private_key):
        return private_key.sign(
            self.data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

class DHT:
    def __init__(self, private_key, public_key):
        self.nodes = {}
        self.private_key = private_key
        self.public_key = public_key

    def add_data(self, data):
        node = DataNode(data, self.private_key)
        self.nodes[node.hash] = node

    def verify_data(self, data):
        new_node = DataNode(data, self.private_key)
        original_node = self.nodes.get(new_node.hash)

        if not original_node:
            return False

        # Verifying the signature of the original node using the public key
        try:
            self.public_key.verify(
                original_node.signature,
                original_node.data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            signature_valid = True
        except Exception:
            signature_valid = False

        return (original_node.size == new_node.size and
                signature_valid and
                original_node.timestamp <= new_node.timestamp)

# RSA key generation for demonstration
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# Create an instance of DHT with RSA keys
dht = DHT(private_key, public_key)

# Add source data to the DHT
dht.add_data("1324")

# Now, try to verify data "1234" which is different from the source data "12345"
verification_result = dht.verify_data("1324")

# Print the verification result
print("Verification result:", verification_result)  # Expected to be False
