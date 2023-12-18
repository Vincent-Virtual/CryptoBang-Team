import hashlib
import time
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

# DataNode class to handle data segments, hashing, and signing
class DataNode:
    def __init__(self, data_segments, private_key):
        self.data_segments = data_segments
        self.hashes = [self.generate_hash(segment) for segment in data_segments]
        self.signatures = [self.sign_data(segment, private_key) for segment in data_segments]
        self.timestamp = time.time()

    @staticmethod
    def generate_hash(data_segment):
        return hashlib.sha256(data_segment.encode()).hexdigest()

    def sign_data(self, data_segment, private_key):
        return private_key.sign(
            data_segment.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

# DHT class to simulate a distributed hash table
class DHT:
    def __init__(self, private_key, public_key):
        self.nodes = {}
        self.private_key = private_key
        self.public_key = public_key

    def add_data(self, data):
        data_segments = self.segment_data(data)
        node = DataNode(data_segments, self.private_key)
        for hash in node.hashes:
            self.nodes[hash] = node

    def segment_data(self, data):
        segments = []
        data_length = len(data)
        segments.append(data[:500])  
        segments.append(data[-500:]) 

        interval_percentage = 7.5 / 100
        segment_size = 100  
        interval_length = int(data_length * interval_percentage)

        for start in range(500, data_length - 500, interval_length):
            segment = data[start:start + segment_size]
            segments.append(segment)

        return segments

    def verify_data_segment(self, data_segment):
        new_hash = DataNode.generate_hash(data_segment)
        original_node = self.nodes.get(new_hash)

        if not original_node:
            return False

        try:
            index = original_node.data_segments.index(data_segment)
            self.public_key.verify(
                original_node.signatures[index],
                data_segment.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except ValueError:
            return False
        except Exception:
            return False

def fetch_data_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None

data_url = 'https://www.gutenberg.org/files/1342/1342-0.txt'  # Pride and Prejudice by Jane Austen

dht_nodes = []
for _ in range(10):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    dht_nodes.append(DHT(private_key, public_key))

source_data = fetch_data_from_url(data_url)
if source_data:
    for i, dht_node in enumerate(dht_nodes):
        dht_node.add_data(source_data)

total_true_count = 0
total_checks = 0

for i, dht_node in enumerate(dht_nodes):
    data_to_verify = fetch_data_from_url(data_url)  
    if data_to_verify:
        data_segments = dht_node.segment_data(data_to_verify)
        verification_results = [dht_node.verify_data_segment(segment) for segment in data_segments]
        print(f"Node {i} VERIFICATION RESULTS:", verification_results)

        total_true_count += sum(result is True for result in verification_results)
        total_checks += len(verification_results)

percentage_true = (total_true_count / total_checks) * 100 if total_checks > 0 else 0
overall_verification = "PASS" if percentage_true >= 70 else "FAIL"
print(f"\nOverall Verification: {overall_verification} ({percentage_true:.2f}% True)")
