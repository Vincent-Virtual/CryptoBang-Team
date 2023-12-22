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

# PBFTNode class
class PBFTNode:
    def __init__(self, node_id, total_nodes, dht_node):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.state = None
        self.pre_prepare_msgs = []
        self.prepare_msgs = []
        self.commit_msgs = []
        self.dht_node = dht_node

    def reset_state(self):
        self.state = None
        self.pre_prepare_msgs = []
        self.prepare_msgs = []
        self.commit_msgs = []

    def pre_prepare(self, data):
        self.state = 'pre-prepared'
        self.pre_prepare_msgs.append(data)
        return self.pre_prepare_msgs

    def prepare(self, data):
        if self.state == 'pre-prepared':
            self.state = 'prepared'
            self.prepare_msgs.append(data)
            return True
        return False

    def commit(self, data):
        if self.state == 'prepared' and len(self.prepare_msgs) >= (2 * self.total_nodes) // 3:
            self.state = 'committed'
            self.commit_msgs.append(data)
            return True
        return False

    def reply(self):
        if self.state == 'committed':
            self.reset_state()
            return "Commit Successful"
        return "Commit Failed"

def simulate_pbft(nodes, data):
    for node in nodes:
        node.pre_prepare(data)

    for node in nodes:
        node.prepare(data)

    for node in nodes:
        node.commit(data)

    for node in nodes:
        print(node.reply())

# Create DHT nodes
dht_nodes = []
for _ in range(10):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    dht_nodes.append(DHT(private_key, public_key))

# Create PBFT nodes with associated DHT nodes
total_nodes = 4
pbft_nodes = [PBFTNode(i, total_nodes, dht_nodes[i]) for i in range(total_nodes)]

# Fetch data and add to DHT nodes
data_url = 'https://www.gutenberg.org/files/1342/1342-0.txt'
source_data = fetch_data_from_url(data_url)
if source_data:
    for dht_node in dht_nodes:
        dht_node.add_data(source_data)

# Simulate PBFT with the source data
simulate_pbft(pbft_nodes, source_data)
