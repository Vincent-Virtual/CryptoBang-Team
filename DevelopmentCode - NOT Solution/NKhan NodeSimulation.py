import requests
import threading
import random

class Node:
    def __init__(self, name, byzantine=False):
        self.name = name
        self.byzantine = byzantine
        self.data_chunks = []
        self.other_nodes = []

    def stream_and_process_data(self, url, chunk_size=10):
        with requests.get(url, stream=True) as r:
            for chunk in r.iter_content(chunk_size=chunk_size):
                chunk = chunk.decode('utf-8')
                consensus_chunk = self.reach_consensus(chunk)
                write_to_file(consensus_chunk)

    def reach_consensus(self, chunk):
        # Initial value is own chunk data or altered data if Byzantine
        my_data = chunk if not self.byzantine else self.alter_chunk(chunk)

        for _ in range(3):  # Number of rounds for consensus
            received_data = []
            # Send own data to other nodes and receive theirs
            for node in self.other_nodes:
                node.receive_data(my_data)
                received_data.append(node.send_data())

            # Determine the most common value received (majority)
            my_data = max(set(received_data), key=received_data.count)

        return my_data

    def receive_data(self, data):
        # Byzantine node might alter the received data
        return data if not self.byzantine else self.alter_chunk(data)

    def send_data(self):
        # Send the last received or processed data
        return self.data_chunks[-1] if self.data_chunks else "No data"

    def alter_chunk(self, chunk):
        # Logic for Byzantine node to alter the chunk
        return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=len(chunk)))

def write_to_file(data):
    with open('consensus_data.txt', 'a') as file:
        file.write(data + '\n')

def main():
    url = "https://www.gutenberg.org/files/1342/1342-0.txt"  # Replace with actual URL
    nodes = [Node(f"Node {i + 1}") for i in range(5)]
    byzantine_nodes = random.sample(nodes, 1)  # Choose 1 node to be Byzantine

    # Set Byzantine nodes
    for node in byzantine_nodes:
        node.byzantine = True

    # Let each node know about the other nodes
    for node in nodes:
        node.other_nodes = [n for n in nodes if n is not node] # Exclude self from the list

    # Start streaming and processing in separate threads
    threads = [threading.Thread(target=node.stream_and_process_data, args=(url,)) for node in nodes]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

