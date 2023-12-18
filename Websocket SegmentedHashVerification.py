import asyncio
import websockets
import threading
import time
import hashlib
import websocket
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

# Global variable for the latest data and stopping threads
latest_data = None
stop_threads = False
last_verification_result = None

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
        segments = []
        data_length = len(data)
        segment_size = 50
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
        print(f"Received message: {message}")
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
    verification_results = []
    for i, dht_node in enumerate(dht_nodes):
        if latest_data:
            result = dht_node.verify_data_segment(latest_data)
            verification_results.append(f"Node {i+1} {result}")
    return verification_results

def periodic_verification(dht_nodes, interval_seconds=60):
    global stop_threads, last_verification_result
    while not stop_threads:
        if latest_data:
            current_results = verify_dht_nodes(dht_nodes)
            if current_results != last_verification_result:  # Print only if the result changes
                print(f"Results for data input: {current_results}")
                last_verification_result = current_results
        else:
            print("\nWaiting for data...")
        time.sleep(interval_seconds)

async def run_websocket_server():
    async def echo(websocket, path):
        for message_count in range(10, 0, -1):
            try:
                await websocket.send(f"Message {message_count} from local server")
                await asyncio.sleep(1)
            except websockets.exceptions.ConnectionClosed:
                print("Client disconnected")
                break

    async with websockets.serve(echo, "localhost", 8765):
        await asyncio.Future()

def start_websocket_server():
    asyncio.run(run_websocket_server())

def main():
    global stop_threads

    dht_nodes = []
    for _ in range(5):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        dht_nodes.append(DHT(private_key, public_key))

    server_thread = threading.Thread(target=start_websocket_server)
    server_thread.start()

    websocket_thread = threading.Thread(target=fetch_data_from_websocket, args=("ws://localhost:8765", dht_nodes))
    websocket_thread.start()

    verification_thread = threading.Thread(target=periodic_verification, args=(dht_nodes,))
    verification_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping threads...")
        stop_threads = True
        websocket_thread.join()
        verification_thread.join()
        server_thread.join()
        print("Threads stopped. Exiting program.")

if __name__ == "__main__":
    main()
