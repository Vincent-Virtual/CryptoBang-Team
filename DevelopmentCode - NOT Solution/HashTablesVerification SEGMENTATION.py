import hashlib
import time
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

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

        # Always include the first and last 500 characters
        segments.append(data[:500])  # First 500 characters
        segments.append(data[-500:]) # Last 500 characters

        # Checking a 100-character segment at every 7.5% interval
        interval_percentage = 7.5 / 100
        segment_size = 100  # 100 characters
        interval_length = int(data_length * interval_percentage)

        for start in range(500, data_length - 500, interval_length):
            segment = data[start:start + segment_size]
            segments.append(segment)

        return segments

    def verify_data_segment(self, data_segment):
        new_hash = DataNode.generate_hash(data_segment)
        original_node = self.nodes.get(new_hash)

        if not original_node:
            print("Segment not found in DHT.")
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
            print("Segment index not found.")
            return False
        except Exception as e:
            print(f"Verification failed: {e}")
            return False

# Example usage
dht_nodes = []
for _ in range(10):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    dht_nodes.append(DHT(private_key, public_key))

# Add data to each DHT node
for i, dht_node in enumerate(dht_nodes):
    data = f"Data for Node {i} " * 10000  # Example large data
    dht_node.add_data(data)

# Verification loop
total_true_count = 0
total_checks = 0

for i, dht_node in enumerate(dht_nodes):
    data_to_verify = f"Data for Node {i} " * 10000  # Same example data
    data_segments = dht_node.segment_data(data_to_verify)
    verification_results = [dht_node.verify_data_segment(segment) for segment in data_segments]
    print(f"Node {i} VERIFICATION RESULTS:", verification_results)

    # Counting the number of True results and total checks for summary
    total_true_count += sum(result is True for result in verification_results)
    total_checks += len(verification_results)

# Determining overall verification success
percentage_true = (total_true_count / total_checks) * 100
overall_verification = "PASS" if percentage_true >= 70 else "FAIL"
print(f"\nOverall Verification: {overall_verification} ({percentage_true:.2f}% True)")

 