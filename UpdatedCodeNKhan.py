import hashlib
import time
import requests
import random
import math
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

# Constants
NUMBER_OF_NODES = 10
FAULTY_PROPORTION = 1/3
NUMBER_OF_FAULTY_NODES = math.floor(NUMBER_OF_NODES * FAULTY_PROPORTION)
NUMBER_OF_HEALTHY_NODES = NUMBER_OF_NODES - NUMBER_OF_FAULTY_NODES
MIN_APPROVALS = math.ceil(0.7 * NUMBER_OF_NODES)
NUMBER_OF_SEGMENTS_TO_PROCESS = 3  # Number of segments to process

# Node Class
class Node:
    def __init__(self, is_faulty):
        self.is_faulty = is_faulty
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()

    def vote(self, data_segment):
        if self.is_faulty:
            return random.choice([True, False])
        else:
            return self.verify_signature(data_segment)

    def verify_signature(self, data_segment):
        # In a real scenario, this should verify the signature
        return True

# DHT Class
class DHT:
    def __init__(self):
        self.nodes = [Node(i < NUMBER_OF_FAULTY_NODES) for i in range(NUMBER_OF_NODES)]

    def process_stream_segment(self, data_segment):
        votes = [node.vote(data_segment) for node in self.nodes]
        print(f"Node Votes: {votes}")
        return votes.count(True) >= MIN_APPROVALS

# Stream Processing Function
def process_stream(url):
    response = requests.get(url, stream=True)
    dht = DHT()
    segment_size = 1024  # 1 KB for demonstration
    segments_processed = 0

    for chunk in response.iter_content(chunk_size=segment_size):
        if segments_processed >= NUMBER_OF_SEGMENTS_TO_PROCESS:
            break
        data_segment = chunk.decode("utf-8", errors='ignore')
        consensus = dht.process_stream_segment(data_segment)
        print(f"Segment {segments_processed + 1} Consensus: {'Valid' if consensus else 'Invalid'}")
        segments_processed += 1

# URL of the data stream
data_url = 'https://www.gutenberg.org/files/1342/1342-0.txt'

# Process the data stream
process_stream(data_url)
