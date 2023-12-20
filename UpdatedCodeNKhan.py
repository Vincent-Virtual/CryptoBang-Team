import websocket
import json
import threading
import time
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
CHUNK_SIZE = 100 * 1  # Adjusted chunk size
BUFFER_CHECK_FREQUENCY = 20  # Seconds
DATA_BUFFER = ""  # Initialize data buffer
exit_flag = False  # Flag for graceful exit

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

# Function to process and clear the buffer
def process_buffer(dht):
    global DATA_BUFFER
    if len(DATA_BUFFER) >= CHUNK_SIZE:
        segments_info = segment_data(DATA_BUFFER[:CHUNK_SIZE], private_key)
        DATA_BUFFER = DATA_BUFFER[CHUNK_SIZE:]  # Remove processed data from buffer

        node_votes = {node_id: [] for node_id in range(NUMBER_OF_NODES)}
        chunk_consensus = True

        for segment, segment_hash, signature, timestamp in segments_info:
            segment_votes = dht.process_segment(segment, segment_hash, signature, timestamp)
            for node_id in range(NUMBER_OF_NODES):
                node_votes[node_id].append(segment_votes[node_id])
            chunk_consensus &= (sum(segment_votes.values()) >= math.ceil(0.7 * NUMBER_OF_NODES))

        print(f"Data Chunk {'Verified Successfully' if chunk_consensus else 'Verified Unsuccessfully'}\n")

# WebSocket message processing function
def process_websocket_message(ws_message):
    global DATA_BUFFER
    message_data = json.loads(ws_message)

    print("Received WebSocket message:", ws_message[:200])  # Debugging
    if 'text' in message_data:
        DATA_BUFFER += message_data['text']
        print("Current buffer length:", len(DATA_BUFFER))  # Debugging
    else:
        print("No 'text' field in the received message.")

# Function to check buffer size periodically
def check_buffer_size(dht):
    global exit_flag
    while not exit_flag:
        process_buffer(dht)
        time.sleep(BUFFER_CHECK_FREQUENCY)
        if len(DATA_BUFFER) < CHUNK_SIZE:
            print("Waiting for data to pile up...")
    print("Exiting buffer check thread.")

# WebSocket event handlers
def on_message(ws, message):
    process_websocket_message(message)

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def on_open(ws):
    print("WebSocket connection opened")
    def run(*args):
        ws.send(json.dumps({
            "type": "hello",
            "apikey": "ABD8F0C0-2F16-40F2-A33C-2B1A294873F9",
            "subscribe_data_type": ["trade"],
            "subscribe_filter_symbol_id": ["BITSTAMP_SPOT_BTC_USD", "BITFINEX_SPOT_BTC_USD"]
        }))
    threading.Thread(target=run).start()

# Set up WebSocket connection
ws = websocket.WebSocketApp("wss://ws.coinapi.io/v1",
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)
ws.on_open = on_open

# Run the WebSocket client and buffer checker in separate threads
dht = DHT(public_key)
ws_thread = threading.Thread(target=ws.run_forever)
ws_thread.start()

buffer_thread = threading.Thread(target=lambda: check_buffer_size(dht))
buffer_thread.start()

try:
    while True:  # Keep the main thread alive
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting program...")
    exit_flag = True
    ws.close()
    buffer_thread.join()
    ws_thread.join()

print("Program exited gracefully.")
