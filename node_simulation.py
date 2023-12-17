import socket
import threading
import time

class Node:
    def __init__(self, port):
        self.host = 'localhost'
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_nodes = {}  # Store connections
        self.received_numbers = []  # Store received numbers

    def start_node(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        print(f"Node started on {self.host}:{self.port}")
        threading.Thread(target=self.accept_connections).start()

    def accept_connections(self):
        while True:
            client_socket, addr = self.socket.accept()
            print(f"Connected to {addr}")
            threading.Thread(target=self.handle_node_connection, args=(client_socket,)).start()

    def handle_node_connection(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024)
                if data:
                    number = int(data.decode('utf-8'))
                    self.received_numbers.append(number)
                    print(f"Received number: {number}")
            except Exception as e:
                print(f"Connection error: {e}")
                break

    def connect_to_node(self, other_port):
        other_node = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        other_node.connect((self.host, other_port))
        self.connected_nodes[(self.host, other_port)] = other_node
        print(f"Connected to node {self.host}:{other_port}")

    def send_number_to_all(self, number):
        for node, conn in self.connected_nodes.items():
            try:
                conn.sendall(str(number).encode('utf-8'))
            except Exception as e:
                print(f"Error sending to {node}: {e}")

    def calculate_consensus(self):
        if self.received_numbers:
            return max(set(self.received_numbers), key=self.received_numbers.count)
        return None

# Example usage
if __name__ == "__main__":
    port = int(input("Enter port number: "))
    node = Node(port)
    node.start_node()
    
    
    # Allow some time for the server to start
    time.sleep(2)

    # Example: Connecting to other nodes
    while True:
        connect = input("Connect to another node? (yes/no): ")
        if connect.lower() == "yes":
            other_port = int(input("Enter port number of the node to connect: "))
            node.connect_to_node(other_port)
        elif connect.lower() == "no":
            break

    # Example: Sending a number to all connected nodes
    send_number = input("Send a number to all connected nodes? (yes/no): ")
    if send_number.lower() == "yes":
        number = int(input("Enter a number to send: "))
        node.send_number_to_all(number)

    # Wait for a while to receive numbers
    time.sleep(5)

    # Calculate and display the consensus                 ###!!! Make it perfect synchronous
    consensus_number = node.calculate_consensus()
    if consensus_number is not None:
        print(f"Consensus on number: {consensus_number}")
    else:
        print("No consensus reached.")