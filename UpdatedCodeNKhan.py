import requests
import random
import math
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from datetime import datetime

# Constants
NUMBER_OF_NODES = 10
FAULTY_PROPORTION = 1/3
NUMBER_OF_FAULTY_NODES = math.floor(NUMBER_OF_NODES * FAULTY_PROPORTION)
CHUNK_SIZE = 100000 * 1  # 100KB
NUMBER_OF_SEGMENTS = 7  # First 100, last 100, and 5 random 50-char segments
NUMBER_OF_CHUNKS_TO_PROCESS = 3  # Number of chunks to process

# Generate RSA keys (private and public)
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# Node Class
class Node:
    def __init__(self, node_id, is_faulty):
        self.node_id = node_id
        self.is_faulty = is_faulty

    def vote(self, segment, segment_hash, public_key, signature, timestamp):
        if self.is_faulty:
            return random.choice([True, False])

        calculated_hash = hashlib.sha256(segment.encode()).hexdigest()
        if calculated_hash != segment_hash:
            return False

        try:
            public_key.verify(
                signature,
                calculated_hash.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        except Exception:
            return False

        if datetime.now().timestamp() - timestamp > 300:
            return False

        return True

# DHT Class
class DHT:
    def __init__(self, public_key):
        self.nodes = [Node(i, i < NUMBER_OF_FAULTY_NODES) for i in range(NUMBER_OF_NODES)]
        self.public_key = public_key

    def process_segment(self, segment, segment_hash, signature, timestamp):
        return {node.node_id: node.vote(segment, segment_hash, self.public_key, signature, timestamp) for node in self.nodes}

# Function to segment the data
def segment_data(data, private_key):
    segments = [data[:100], data[-100:]] + [data[random.randint(100, len(data)-150):random.randint(100, len(data)-150) + 50] for _ in range(5)]
    segment_info = []

    for segment in segments:
        segment_hash = hashlib.sha256(segment.encode()).hexdigest()
        signature = private_key.sign(
            segment_hash.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        timestamp = datetime.now().timestamp()

        segment_info.append((segment, segment_hash, signature, timestamp))

    return segment_info

# Stream Processing Function
def process_stream(url, private_key):
    response = requests.get(url, stream=True)
    dht = DHT(public_key)
    chunks_processed = 0

    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
        if chunks_processed >= NUMBER_OF_CHUNKS_TO_PROCESS:
            break

        if len(chunk) < CHUNK_SIZE:
            print(f"Chunk {chunks_processed + 1} is smaller than 100KB, stopping processing.\n")
            break

        data_chunk = chunk.decode("utf-8", errors='ignore')
        segments_info = segment_data(data_chunk, private_key)
        print(f"\nChunk {chunks_processed + 1}")

        node_votes = {node_id: [] for node_id in range(NUMBER_OF_NODES)}
        chunk_consensus = True

        for segment, segment_hash, signature, timestamp in segments_info:
            segment_votes = dht.process_segment(segment, segment_hash, signature, timestamp)
            for node_id in range(NUMBER_OF_NODES):
                node_votes[node_id].append(segment_votes[node_id])
            chunk_consensus &= (sum(segment_votes.values()) >= math.ceil(0.7 * NUMBER_OF_NODES))

        for node_id, votes in node_votes.items():
            print(f"Node {node_id} Votes: {votes}")
        print(f"Chunk {chunks_processed + 1} {'Verified Successfully' if chunk_consensus else 'Verified Unsuccessfully'}\n")
        chunks_processed += 1

# URL of the data stream
data_url = 'https://www.gutenberg.org/files/1342/1342-0.txt'

# Process the data stream
process_stream(data_url, private_key)

