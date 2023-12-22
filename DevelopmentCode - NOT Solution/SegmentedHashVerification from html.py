import hashlib
import time
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import random
import math

# Define the number of nodes in the system
NUMBER_OF_NODES = 10  # You can change this value to the desired number of nodes

# Define the proportion of nodes that are faulty/dead/malicious (e.g., 1/4, 1/5, 1/10, etc.)
FAULTY_PROPORTION = 1/10  # Adjust this value as needed

# Calculate the number of faulty nodes based on the proportion, rounding down
NUMBER_OF_FAULTY_NODES = math.floor(NUMBER_OF_NODES * FAULTY_PROPORTION)
NUMBER_OF_HEALTHY_NODES = NUMBER_OF_NODES - NUMBER_OF_FAULTY_NODES

# Define the interval percentage (adjust as needed)
interval_percentage = 20 / 100

# Calculate the number of segments based on interval_percentage
number_of_segments = int(1 / interval_percentage) + 2

# Calculate the minimum number of approvals required (e.g., 70%)
MIN_APPROVALS = math.ceil(0.7 * NUMBER_OF_NODES * number_of_segments)

# DataNode class to handle data segments, hashing, and signing
class DataNode:
    # Initialize with data segments and a private key
    def __init__(self, data_segments, private_key):
        self.data_segments = data_segments
        self.hashes = [self.generate_hash(segment) for segment in data_segments]
        self.signatures = [self.sign_data(segment, private_key) for segment in data_segments]
        self.timestamp = time.time()

    # Generate a hash for a given data segment
    @staticmethod
    def generate_hash(data_segment):
        return hashlib.sha256(data_segment.encode()).hexdigest()

    # Sign a given data segment using the private key
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
    def __init__(self, private_key, public_key, interval_percentage):
        self.nodes = {}
        self.private_key = private_key
        self.public_key = public_key
        self.interval_percentage = interval_percentage  # Store interval_percentage as an instance variable
        self.NUMBER_OF_FAULTY_NODES = NUMBER_OF_FAULTY_NODES  # Store NUMBER_OF_FAULTY_NODES as an instance variable

    # Add data to the DHT
    def add_data(self, data):
        # Split data into 1MB chunks
        data_chunks = [data[i:i+1024*1024] for i in range(0, len(data), 1024*1024)]

        for chunk in data_chunks:
            data_segments = self.segment_data(chunk)

            # Create a list of nodes, marking exactly NUMBER_OF_FAULTY_NODES nodes as faulty
            nodes = [DataNode(data_segments, self.private_key) for _ in range(NUMBER_OF_NODES)]
            faulty_node_indices = random.sample(range(NUMBER_OF_NODES), NUMBER_OF_FAULTY_NODES)
            for index in faulty_node_indices:
                nodes[index] = None  # Mark nodes as faulty

            for node in nodes:
                if node is not None:
                    for hash in node.hashes:
                        self.nodes[hash] = node

    # Segment data into specified chunks
    def segment_data(self, data):
        segments = []
        data_length = len(data)
        segments.append(data[:500])  # First 500 characters
        segments.append(data[-500:]) # Last 500 characters

        # Define interval and segment size
        interval_percentage = self.interval_percentage
        segment_size = 100  # 100 characters
        interval_length = int(data_length * interval_percentage)

        # Segmenting the data
        for start in range(500, data_length - 500, interval_length):
            segment = data[start:start + segment_size]
            segments.append(segment)

        return segments

    # Verify a data segment against the stored hash and signature
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

# Function to fetch data from a given URL
def fetch_data_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None

# URL for the source data (sample plain text data)
data_url = 'https://www.gutenberg.org/files/1342/1342-0.txt'  # Pride and Prejudice by Jane Austen

# Creating DHT nodes
dht_nodes = []
for _ in range(NUMBER_OF_NODES):  # Use the NUMBER_OF_NODES variable here
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    dht_nodes.append(DHT(private_key, public_key, interval_percentage))

# Fetching and adding source data to each DHT node
source_data = fetch_data_from_url(data_url)
if source_data:
    for i, dht_node in enumerate(dht_nodes):
        dht_node.add_data(source_data)

# Verification loop
total_true_count = 0
total_checks = 0

for i, dht_node in enumerate(dht_nodes):
    data_to_verify = fetch_data_from_url(data_url)  # Fetching the same data for verification
    if data_to_verify:
        data_segments = dht_node.segment_data(data_to_verify)
        verification_results = [dht_node.verify_data_segment(segment) for segment in data_segments]
        print(f"Node {i} VERIFICATION RESULTS:", verification_results)

        # Counting results
        total_true_count += sum(result is True for result in verification_results)
        total_checks += len(verification_results)

# Calculating overall verification success
percentage_true = (total_true_count / total_checks) * 100 if total_checks > 0 else 0
overall_verification = "PASS" if total_true_count >= MIN_APPROVALS else "FAIL"
print(f"\nOverall Verification: {overall_verification} ({percentage_true:.2f}% True)")
