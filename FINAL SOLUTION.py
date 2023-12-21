# All Imports
import websocket
import json
import threading
import time
import random
import math
import hashlib
import csv
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from datetime import datetime
import xlsxwriter

# Defining Constants
NUMBER_OF_NODES = 10 # Number of Nodes to Run
FAULTY_PROPORTION = 1/3 # Proportion of nodes that will be Faulty
NUMBER_OF_FAULTY_NODES = math.floor(NUMBER_OF_NODES * FAULTY_PROPORTION)
CHUNK_SIZE = 500  # Chunk Size
BUFFER_CHECK_FREQUENCY = 5  # Seconds
NUMBER_OF_SEGMENTS = 5  # Define the number of segments per chunk
TOTAL_VOTES = NUMBER_OF_NODES * (NUMBER_OF_SEGMENTS + 2) # Helps Approval Algorithm
MIN_APPROVALS = 2 * (TOTAL_VOTES // 3) + 1 # Determines Threshhold to Pass
SEGMENT_LENGTH = 20 
NUMBER_OF_CHUNKS = 3    # Define the number of chunks to process
DATA_BUFFER = ""  # Initializing Data Buffer
exit_flag = False  # Flag for Graceful Exit

# Defining global workbook and worksheet for matrix data
workbook = xlsxwriter.Workbook('matrix_tables.xlsx')
worksheet = workbook.add_worksheet()

# Add headers to the matrix data file
headers = ['CHUNK #', 'NODE #','HEAD', 'SEG 1', 'SEG 2', 'SEG 3', 'SEG 4', 'SEG 5', 'TAIL',
           'PERCENTAGE', 'OUTCOME','SIZE', 'HASHES',
           'SIGNATURE', 'TIMESTAMP', 'STATUS']

# Write headers to the worksheet
for col_num, header in enumerate(headers):
    worksheet.write(0, col_num, header)

# Start row for the first chunk
start_row = 1 

# Write headers to the worksheet, across the first row
for col_num, header in enumerate(headers):
    worksheet.write(0, col_num, header)

# Generate RSA keys (private and public)
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()



# File Initializations
csv_filename = 'chunk_data_records.csv'
with open(csv_filename, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["CHUNK #", "TIMESTAMP", "DATA", "SIZE", "SIGNATURE", "OUTCOME", "PERCENTAGE"])


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

    # Define head and tail segments
    head = data[:50]  # First 50 characters for head segment
    tail = data[-50:]  # Last 50 characters for tail segment

    # Calculate the length of the entire middle section
    middle_section_length = CHUNK_SIZE - (len(head) + len(tail))
    segment_length = middle_section_length // NUMBER_OF_SEGMENTS

    # Define middle segments
    middle_start = len(head)
    segments = [head]
    for _ in range(NUMBER_OF_SEGMENTS):
        segments.append(data[middle_start:middle_start + segment_length])
        middle_start += segment_length

    # Add the tail segment
    segments.append(tail)

    # Generate hash, signature, and timestamp for each segment
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
def save_chunk_to_csv(filename, chunk_number, chunk_data, node_votes, segments_info, chunk_verification_outcome, true_vote_percentage):
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)

        # Write the headers if the file is empty
        if file.tell() == 0:
            writer.writerow(["Chunk Number", "Timestamp", "Chunk Data", "Chunk Size", "Digital Signature", "Verification Outcome", "True Vote Percentage"])
        
        # Write the chunk data
        timestamp = datetime.now().timestamp()
        digital_signature = ','.join(info[2].hex() for info in segments_info)  # Assuming this is how you get the digital signature
        writer.writerow([chunk_number, timestamp, chunk_data, CHUNK_SIZE, digital_signature, chunk_verification_outcome, f"{true_vote_percentage:.2f}%"])

# Name for the Data Chunk Excel file
csv_filename = 'chunk_data_records.csv'

# Function to generate matrix table
def generate_matrix_table(chunk_number, node_votes, segments_info, chunk_verification_outcome, true_vote_percentage):
    global worksheet, start_row  # Declare start_row as global

    # Write Chunk number for all nodes
    for i in range(NUMBER_OF_NODES):
        worksheet.write(start_row + i, 0, f'Chunk {chunk_number}')

    # Write the data for each node
    for node_id in range(NUMBER_OF_NODES):
        worksheet.write(start_row + node_id, 1, f'NODE {node_id}')  # Node ID

        # Write True/False for the head segment, middle segments, and tail segment
        worksheet.write(start_row + node_id, 2, 'True' if node_votes[node_id][0] else 'False')  # Head segment
        for segment_index, vote in enumerate(node_votes[node_id][1:-1], start=3):  # Middle segments
            worksheet.write(start_row + node_id, segment_index, 'True' if vote else 'False')
        worksheet.write(start_row + node_id, 3 + NUMBER_OF_SEGMENTS, 'True' if node_votes[node_id][-1] else 'False')  # Tail segment

        # Write the verification percentage per node
        positive_votes = node_votes[node_id].count(True)
        verification_percentage_per_node = (positive_votes / (NUMBER_OF_SEGMENTS + 2)) * 100  # Including head and tail
        worksheet.write(start_row + node_id, 4 + NUMBER_OF_SEGMENTS, f"{verification_percentage_per_node:.2f}%")

        # Write the verification outcome, size of data received, hashes, signatures, timestamps, and node status
        worksheet.write(start_row + node_id, 5 + NUMBER_OF_SEGMENTS, chunk_verification_outcome)
        worksheet.write(start_row + node_id, 6 + NUMBER_OF_SEGMENTS, CHUNK_SIZE)
        
        # Combine hashes, signatures, and timestamps from segments_info
        hashes = ', '.join(info[1] for info in segments_info)
        signatures = ', '.join(info[2].hex() for info in segments_info)
        timestamps = ', '.join(str(info[3]) for info in segments_info)
        worksheet.write(start_row + node_id, 7 + NUMBER_OF_SEGMENTS, hashes)
        worksheet.write(start_row + node_id, 8 + NUMBER_OF_SEGMENTS, signatures)
        worksheet.write(start_row + node_id, 9 + NUMBER_OF_SEGMENTS, timestamps)
        
        # Determine node status based on the majority vote
        status = 'GOOD' if positive_votes >= math.ceil((NUMBER_OF_SEGMENTS + 2) * 0.85) else 'FAULTY'
        worksheet.write(start_row + node_id, 10 + NUMBER_OF_SEGMENTS, status)

    # After writing all nodes, increment start_row to skip to the next chunk's start
    start_row += NUMBER_OF_NODES


# Function to process and clear the buffer
def process_buffer(dht, chunk_number):
    global DATA_BUFFER, start_row
    if len(DATA_BUFFER) >= CHUNK_SIZE:
        chunk_data = DATA_BUFFER[:CHUNK_SIZE]
        DATA_BUFFER = DATA_BUFFER[CHUNK_SIZE:]

        segments_info = segment_data(chunk_data, private_key)
        node_votes = {node_id: [] for node_id in range(NUMBER_OF_NODES)}

        for node_id in range(NUMBER_OF_NODES):
            for segment_info in segments_info:
                segment, segment_hash, signature, timestamp = segment_info
                vote = dht.nodes[node_id].vote(segment, segment_hash, public_key, signature, timestamp)
                node_votes[node_id].append(vote)

        total_true_votes = sum(vote for votes in node_votes.values() for vote in votes)
        true_vote_percentage = (total_true_votes / TOTAL_VOTES) * 100
        chunk_verification_outcome = 'Verified Successfully' if total_true_votes >= MIN_APPROVALS else 'Verified Unsuccessfully'

        # Output to the terminal
        print(f"Chunk {chunk_number} Processing Results:")
        for node_id, votes in node_votes.items():
            print(f"Node {node_id} Votes: {votes}")
        print(f"Chunk {chunk_number} {chunk_verification_outcome} ({true_vote_percentage:.2f}% true votes)")

        # Generate Data Chunk Table and Matrix Table
        save_chunk_to_csv(csv_filename, chunk_number, chunk_data, node_votes, segments_info, chunk_verification_outcome, true_vote_percentage)
        generate_matrix_table(chunk_number, node_votes, segments_info, chunk_verification_outcome, true_vote_percentage)
        
        # Clear the DATA_BUFFER for the next chunk
        DATA_BUFFER = DATA_BUFFER[CHUNK_SIZE:]

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
# Implementing Threading
ws_thread = threading.Thread(target=ws.run_forever)
ws_thread.start()

# Implementing Buffer Threads
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

# Do not forget to close the workbook after processing all chunks
workbook.close()
