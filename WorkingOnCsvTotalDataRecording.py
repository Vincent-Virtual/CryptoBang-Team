import websocket
import json
import threading
import time
import random
import xlsxwriter
import math
import hashlib
import csv
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from datetime import datetime

# Constants
NUMBER_OF_NODES = 10
FAULTY_PROPORTION = 1/3
NUMBER_OF_FAULTY_NODES = math.floor(NUMBER_OF_NODES * FAULTY_PROPORTION)
CHUNK_SIZE = 500  # Adjusted chunk size
BUFFER_CHECK_FREQUENCY = 20  # Seconds
DATA_BUFFER = ""  # Initialize data buffer
exit_flag = False  # Flag for graceful exit

NUMBER_OF_SEGMENTS = 5  # Define the number of segments per chunk
NUMBER_OF_CHUNKS = 3    # Define the number of chunks to process

# Generate RSA keys (private and public)
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()


# CSV File Initialization
csv_filename = 'data.csv'
with open(csv_filename, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Chunk Data", "Chunk Size", "Digital Signature", "Verification Outcome", "True Vote Percentage"])

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
    if len(data) < 250:
        return []

    segments = [data[i:i + CHUNK_SIZE // NUMBER_OF_SEGMENTS] for i in range(0, len(data), CHUNK_SIZE // NUMBER_OF_SEGMENTS)]

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

# Function to save chunk data to CSV
def save_to_csv(timestamp, chunk_data, chunk_size, digital_signature, outcome, true_vote_percentage):
    with open(csv_filename, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, chunk_data, chunk_size, digital_signature, outcome, true_vote_percentage])

# Additional function to generate the matrix table Excel file
def generate_matrix_table(chunk_number, node_votes, dht):
    # Create a workbook and add a worksheet
    workbook = xlsxwriter.Workbook(f'matrix_table_chunk_{chunk_number}.xlsx')
    worksheet = workbook.add_worksheet()

    # Define headers for the columns and rows
    headers = ['Chunk #', 'HEAD SEGMENT', 'SEGMENT 1', 'SEGMENT 2', 'SEGMENT 3', 'SEGMENT 4', 'SEGMENT 5', 'TAIL SEGMENT',
               'VERIFICATION PERCENTAGE', 'VERIFICATION OUTCOME', 'SIZE OF DATA RECEIVED', 'HASHES OF DATA SEGMENTS',
               'DIGITAL SIGNATURES OF DATA SEGMENTS', 'TIMESTAMPS OF DATA SEGMENTS', 'NODE STATUS']
    
    # Write headers
    for i, header in enumerate(headers):
        worksheet.write(i, 0, header)
    
    # Write Node IDs
    for i in range(NUMBER_OF_NODES):
        worksheet.write(0, i+1, f'NODE {i}')
    
    # Write votes and statuses for each segment
    for segment_index, votes in enumerate(zip(*node_votes.values()), start=1):
        for node_index, vote in enumerate(votes, start=1):
            worksheet.write(segment_index, node_index, str(vote))
            # Fill in other details like verification percentage, outcome, etc.
            # This part is omitted for brevity, and should be filled with actual values
    
    # Close the workbook
    workbook.close()

# Function to process and clear the buffer
def process_buffer(dht, chunk_number):
    global DATA_BUFFER
    if len(DATA_BUFFER) >= CHUNK_SIZE:
        chunk_data = DATA_BUFFER[:CHUNK_SIZE]
        DATA_BUFFER = DATA_BUFFER[CHUNK_SIZE:]

        print(f"Chunk {chunk_number}")
        segments_info = segment_data(chunk_data, private_key)
        node_votes = {node_id: [] for node_id in range(NUMBER_OF_NODES)}
        chunk_consensus = True
        total_true_votes = 0

        for segment, segment_hash, signature, timestamp in segments_info:
            segment_votes = dht.process_segment(segment, segment_hash, signature, timestamp)
            for node_id in range(NUMBER_OF_NODES):
                node_votes[node_id].append(segment_votes[node_id])
                if segment_votes[node_id]:
                    total_true_votes += 1
            chunk_consensus &= (sum(segment_votes.values()) >= math.ceil(0.7 * NUMBER_OF_NODES))

        total_votes = len(segments_info) * NUMBER_OF_NODES
        true_vote_percentage = (total_true_votes / total_votes) * 100
        chunk_verification_outcome = 'Verified Successfully' if chunk_consensus else 'Verified Unsuccessfully'
        print(f"Chunk {chunk_number} {chunk_verification_outcome} ({true_vote_percentage:.2f}% true)")

        # Compute digital signature for the entire chunk
        chunk_signature = private_key.sign(
            chunk_data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        chunk_signature_readable = chunk_signature.hex()

        # Save chunk data to CSV
        save_to_csv(datetime.now().timestamp(), chunk_data, len(chunk_data), chunk_signature_readable, chunk_verification_outcome, true_vote_percentage)
        
        # After processing each chunk, call the function to create the matrix table
        generate_matrix_table(chunk_number, node_votes, dht)

# Function to check buffer size periodically
def check_buffer_size(dht):
    global exit_flag
    chunk_number = 1
    while not exit_flag and chunk_number <= NUMBER_OF_CHUNKS:
        if len(DATA_BUFFER) >= CHUNK_SIZE:
            process_buffer(dht, chunk_number)
            if chunk_number == NUMBER_OF_CHUNKS:
                exit_flag = True  # Set exit flag to ensure main program exits
                break
            chunk_number += 1
        else:
            print(f"Waiting for enough data for Chunk {chunk_number}...")
        time.sleep(BUFFER_CHECK_FREQUENCY)
    print("Exiting buffer check thread.")

# Binance WebSocket message processing function
def process_binance_message(ws_message):
    global DATA_BUFFER
    message_data = json.loads(ws_message)
    if 'p' in message_data:
        DATA_BUFFER += message_data['p']
    else:
        print("No price field in the received message.")

# Binance WebSocket event handlers
def on_message(ws, message):
    process_binance_message(message)

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def on_open(ws):
    print("WebSocket connection opened to Binance")

# Set up Binance WebSocket connection and run client
binance_ws_url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
ws = websocket.WebSocketApp(binance_ws_url, on_message=on_message, on_error=on_error, on_close=on_close)

dht = DHT(public_key)
ws_thread = threading.Thread(target=ws.run_forever)
ws_thread.start()

buffer_thread = threading.Thread(target=lambda: check_buffer_size(dht))
buffer_thread.start()

# Main loop for keeping the script running
try:
    while True:
        if exit_flag:
            break
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting program...")
    exit_flag = True

# Close WebSocket and wait for threads to finish
ws.close()
buffer_thread.join()
ws_thread.join()

print("Program exited gracefully.")
