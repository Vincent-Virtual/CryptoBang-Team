import hashlib
import time
import websocket
import threading
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

# Global variable to store the latest data received from WebSocket
latest_data = None

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
        # Ensure that the data_length is not zero to avoid "range() arg 3 must not be zero" error
        if len(data) == 0:
            return []

        segments = []
        data_length = len(data)
        segment_size = 50  # Assuming each segment is 50 characters long

        for start in range(0, data_length, segment_size):
            segment = data[start:min(start + segment_size, data_length)]
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

def fetch_data_from_websocket(url, dht_nodes):
    global latest_data

    def on_message(ws, message):
        global latest_data
        latest_data = message
        print(f"Received message: {message}")  # For debugging
        for dht_node in dht_nodes:
            dht_node.add_data(latest_data)

    def on_error(ws, error):
        print(f"WebSocket error: {error}")

    def on_close(ws, close_status_code, close_msg):
        print("WebSocket closed")

    def on_open(ws):
        print("WebSocket connection opened")
        ws.send("Test message")

    ws = websocket.WebSocketApp(url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever()

def verify_dht_nodes(dht_nodes):
    global latest_data
    total_true_count = 0
    total_checks = 0

    for i, dht_node in enumerate(dht_nodes):
        if latest_data:
            data_to_verify = latest_data
            data_segments = dht_node.segment_data(data_to_verify)
            verification_results = [dht_node.verify_data_segment(segment) for segment in data_segments]
            print(f"Node {i} VERIFICATION RESULTS:", verification_results)

            total_true_count += sum(result is True for result in verification_results)
            total_checks += len(verification_results)

    percentage_true = (total_true_count / total_checks) * 100 if total_checks > 0 else 0
    overall_verification = "PASS" if percentage_true >= 70 else "FAIL"
    return overall_verification, percentage_true

def periodic_verification(dht_nodes, interval_seconds=30):
    global latest_data
    while True:
        overall_verification, percentage_true = verify_dht_nodes(dht_nodes)
        print(f"\nOverall Verification: {overall_verification} ({percentage_true:.2f}% True)")
        time.sleep(interval_seconds)

# Set up the DHT nodes
dht_nodes = []
for _ in range(5):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    dht_nodes.append(DHT(private_key, public_key))

# Start the WebSocket client in a separate thread
websocket_url = "wss://echo.websocket.org"  # Replace with a working WebSocket server URL
websocket_thread = threading.Thread(target=fetch_data_from_websocket, args=(websocket_url, dht_nodes))
websocket_thread.start()

# Start the periodic verification in a separate thread
verification_thread = threading.Thread(target=periodic_verification, args=(dht_nodes,))
verification_thread.start()
