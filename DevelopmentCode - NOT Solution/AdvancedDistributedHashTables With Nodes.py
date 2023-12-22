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

# Create 10 instances of DHT with RSA keys
dht_nodes = []
for _ in range(10):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    dht_nodes.append(DHT(private_key, public_key))

# Add data to each DHT node
for i, dht_node in enumerate(dht_nodes):
    data = f"Data for Node {i}"
    dht_node.add_data(data)

# Verify data independently for each node
verification_results = []
for i, dht_node in enumerate(dht_nodes):
    data_to_verify = f"Data for Node {i}"
    verification_result = dht_node.verify_data(data_to_verify)
    verification_results.append((i, verification_result))

# Count the number of nodes that verified as True
true_count = sum(1 for _, result in verification_results if result)

# Print the verification results for each node
for i, result in verification_results:
    print(f"Node {i} VERIFICATION RESULT:", result)

# Print Data Consensus result based on the count
if true_count >= 7:
    print("Overall Result: Data Consensus PASSED")
else:
    print("Overall Result: Data Consensus FAILED")
