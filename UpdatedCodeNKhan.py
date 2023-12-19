import requests
import random
import math

# Constants
NUMBER_OF_NODES = 10
FAULTY_PROPORTION = 1/3
NUMBER_OF_FAULTY_NODES = math.floor(NUMBER_OF_NODES * FAULTY_PROPORTION)
CHUNK_SIZE = 1024 * 1024  # 1MB
NUMBER_OF_SEGMENTS = 7  # First 100, last 100, and 5 random 50-char segments
NUMBER_OF_CHUNKS_TO_PROCESS = 3  # Number of chunks to process

# Node Class
class Node:
    def __init__(self, node_id, is_faulty):
        self.node_id = node_id
        self.is_faulty = is_faulty

    def vote(self, segment):
        return not self.is_faulty or random.choice([True, False])

# DHT Class
class DHT:
    def __init__(self):
        self.nodes = [Node(i, i < NUMBER_OF_FAULTY_NODES) for i in range(NUMBER_OF_NODES)]

    def process_segment(self, segment):
        return {node.node_id: node.vote(segment) for node in self.nodes}

# Function to segment the data
def segment_data(data):
    segments = [data[:100], data[-100:]]  # First and last 100 characters
    remaining_data = data[100:-100]
    
    # Choose 5 random 50-character segments
    for _ in range(5):
        start_index = random.randint(0, len(remaining_data) - 50)
        segments.append(remaining_data[start_index:start_index + 50])
    
    return segments

# Stream Processing Function
def process_stream(url):
    response = requests.get(url, stream=True)
    dht = DHT()
    chunks_processed = 0

    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
        if chunks_processed >= NUMBER_OF_CHUNKS_TO_PROCESS:
            break

        # Check if the chunk is less than 1MB and break if so
        if len(chunk) < CHUNK_SIZE:
            print(f"Chunk {chunks_processed + 1} is smaller than 1MB, stopping processing.")
            break

        data_chunk = chunk.decode("utf-8", errors='ignore')
        segments = segment_data(data_chunk)
        print(f"Chunk {chunks_processed + 1}")

        node_votes = {node.node_id: [] for node in dht.nodes}
        chunk_consensus = True

        for segment in segments:
            segment_votes = dht.process_segment(segment)
            for node_id, vote in segment_votes.items():
                node_votes[node_id].append(vote)
            chunk_consensus &= (sum(segment_votes.values()) >= math.ceil(0.7 * NUMBER_OF_NODES))

        for node_id, votes in node_votes.items():
            print(f"Node {node_id} Votes: {votes}")
        print(f"Chunk {chunks_processed + 1} {'Verified Successfully' if chunk_consensus else 'Verified Unsuccessfully'}\n")
        chunks_processed += 1

# URL of the data stream
data_url = 'https://www.gutenberg.org/files/1342/1342-0.txt'

# Process the data stream
process_stream(data_url)
