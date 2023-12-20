import websocket
import json
import csv
import threading
import time
import os
import random
import prettytable

import math
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from datetime import datetime


# Constants
NUMBER_OF_NODES = 10
FAULTY_PROPORTION = 1/3
NUMBER_OF_FAULTY_NODES = math.floor(NUMBER_OF_NODES * FAULTY_PROPORTION)
CHUNK_SIZE = 500 * 1  # Adjusted chunk size
BUFFER_CHECK_FREQUENCY = 20  # Seconds
DATA_BUFFER = ""  # Initialize data buffer
exit_flag = False  # Flag for graceful exit

# Define the number of segments and chunks
number_of_segments = 5  # Adjust this to your desired number
number_of_chunks = 3  # Adjust this to your desired number

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

    # def export_to_csv(chunk_number,
    #                   chunk_consensus,
    #                   true_vote_percentage,
    #                   CSV_FILENAME):
    #
        #
        # # Write header if the file doesn't exist
        # write_header = not os.path.exists(CSV_FILENAME)
        # with open(CSV_FILENAME, mode='a', newline='') as csvfile:
        #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        #
        #     if write_header:
        #         writer.writeheader()
        #
        #     # Write row data
        #     writer.writerow(row_data)
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

    segments = [data[:100], data[-100:]]  # First and last 100 characters
    for _ in range(5):
        start_index = random.randint(100, len(data) - 150)
        segments.append(data[start_index:start_index + 50])

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
# def export_to_csv(chunk_number,
#                       chunk_consensus,
#                       true_vote_percentage,
#                       CSV_FILENAME):
#     fieldnames = ['Chunk', 'Consensus', 'True Vote Percentage']
#     row_data = {
#             'Chunk': chunk_number,
#             'Consensus': 'Verified Successfully' if chunk_consensus else 'Verified Unsuccessfully',
#             'True Vote Percentage': true_vote_percentage
#         }

def generate_table(chunk_number, segments_info, node_votes):
    table = prettytable.PrettyTable()

    # Set column names
    column_names = [f"Segment_{i}" for i in range(len(segments_info))]
    table.field_names = ['Nodes'] + column_names

    # Add data to the table
    for node_id, votes in node_votes.items():
        table.add_row([f"Node_{node_id}"] + votes)

    # Print the table
    print(f"Table for Chunk {chunk_number}:\n")
    print(table)
    print("\n")


def process_buffer(dht, chunk_number):
    global DATA_BUFFER
    if len(DATA_BUFFER) >= CHUNK_SIZE:
        segments_info = segment_data(DATA_BUFFER[:CHUNK_SIZE], private_key)
        DATA_BUFFER = DATA_BUFFER[CHUNK_SIZE:]

        print(f"Chunk {chunk_number}")
        node_votes = {node_id: [] for node_id in range(NUMBER_OF_NODES)}
        chunk_consensus = True
        total_true_votes = 0
        # CSV_FILENAME = "consensus_results.csv"
        # with open(CSV_FILENAME, mode='w', newline='') as csvfile:
        #    # fieldnames = ['Segment', 'Consensus']
        #    # writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        #    # writer.writeheader()
        for segment, segment_hash, signature, timestamp in segments_info:
            segment_votes = dht.process_segment(segment, segment_hash, signature, timestamp)
            for node_id in range(NUMBER_OF_NODES):
                node_votes[node_id].append(segment_votes[node_id])
                if segment_votes[node_id]:
                    total_true_votes += 1
            chunk_consensus &= (sum(segment_votes.values()) >= math.ceil(0.7 * NUMBER_OF_NODES))

        for node_id, votes in node_votes.items():
            print(f"Node {node_id} Votes: {votes}")
           # writer.writerow({'Node': node_id, 'Votes': votes})


        total_votes = len(segments_info) * NUMBER_OF_NODES
        true_vote_percentage = (total_true_votes / total_votes) * 100
        print(f"Chunk {chunk_number} {'Verified Successfully' if chunk_consensus else 'Verified Unsuccessfully'} ({true_vote_percentage:.2f}% true)\n")

        #generate_table(chunk_number, segments_info, node_votes)
        write_csv(chunk_number, segments_info, node_votes)
        #writer.writerow({'Segment': chunk_number + 1, 'Consensus': 'Valid' if chunk_consensus else 'Invalid'})
       # export_to_csv(chunk_number, chunk_consensus, true_vote_percentage, node_votes)

    #export_to_csv(chunk_number,chunk_consensus,true_vote_percentage,CSV_FILENAME)
        print("finished exporting")
import csv
import os

# ... (existing code)

# Constants
CSV_FILENAME = 'votes_table.csv'

# Function to process and clear the buffer
def process_buffer(dht, chunk_number):
    global DATA_BUFFER
    if len(DATA_BUFFER) >= CHUNK_SIZE:
        segments_info = segment_data(DATA_BUFFER[:CHUNK_SIZE], private_key)
        DATA_BUFFER = DATA_BUFFER[CHUNK_SIZE:]

        print(f"Chunk {chunk_number}")
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

        for node_id, votes in node_votes.items():
            print(f"Node {node_id} Votes: {votes}")

        total_votes = len(segments_info) * NUMBER_OF_NODES
        true_vote_percentage = (total_true_votes / total_votes) * 100
        print(f"Chunk {chunk_number} {'Verified Successfully' if chunk_consensus else 'Verified Unsuccessfully'} ({true_vote_percentage:.2f}% true)\n")

        # Generate and write the CSV file
        write_csv(chunk_number, segments_info, node_votes)

# Function to generate and write the CSV file
def write_csv(chunk_number, segments_info, node_votes):
    csv_filename = f'votes_table_chunk_{chunk_number}.csv'
    with open(csv_filename, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        header = ['Nodes'] + [f"Segment_{i}" for i in range(len(segments_info))]
        writer.writerow(header)

        # Write data
        for node_id, votes in node_votes.items():
            row_data = [f"Node_{node_id}"] + votes
            writer.writerow(row_data)

    print(f"CSV file '{csv_filename}' created successfully.\n")

# ... (existing code)



# Function to check buffer size periodically
def check_buffer_size(dht):
    global exit_flag
    chunk_number = 1
    while not exit_flag and chunk_number <= number_of_chunks:
        if len(DATA_BUFFER) >= CHUNK_SIZE:
            process_buffer(dht, chunk_number)
            if chunk_number == number_of_chunks:
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

# Set up Binance WebSocket connection
binance_ws_url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
ws = websocket.WebSocketApp(binance_ws_url, on_message=on_message, on_error=on_error, on_close=on_close)

# Run the WebSocket client and buffer checker in separate threads
dht = DHT(public_key)
ws_thread = threading.Thread(target=ws.run_forever)
ws_thread.start()

buffer_thread = threading.Thread(target=lambda: check_buffer_size(dht))
buffer_thread.start()

# Main loop for keeping the script running
try:
    while True:
        if exit_flag:
            break  # Break the loop if exit_flag is True
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting program...")
    exit_flag = True

# Close WebSocket and wait for threads to finish
ws.close()
buffer_thread.join()
ws_thread.join()

print("Program exited gracefully.")
