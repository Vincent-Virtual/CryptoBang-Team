import asyncio
import json
import websockets
from pbft_config import config


config = config(5, 3, 2)

# Update the parameters using setters
config.TRANSACTION_THRESHOLD = 10
config.NUMBER_OF_NODES = 5
config.MIN_APPROVALS = 3

MESSAGE_TYPE = {
    "transaction": "TRANSACTION",
    "prepare": "PREPARE",
    "pre_prepare": "PRE-PREPARE",
    "commit": "COMMIT",
    "round_change": "ROUND_CHANGE"
}

import sys


# Declare the P2P_PORT, set to 5001 if not provided through the command line
P2P_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5001

# Declare the peers, split the PEERS string from the command line into a list
peers = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else []

#MIN_APPROVALS  # Assuming MIN_APPROVALS is defined in config module

class P2pServer:
    def __init__(self, blockchain, transaction_pool, wallet, block_pool, prepare_pool, commit_pool, message_pool, validators):
        self.blockchain = blockchain
        self.sockets = set()
        self.transaction_pool = transaction_pool
        self.wallet = wallet
        self.block_pool = block_pool
        self.prepare_pool = prepare_pool
        self.commit_pool = commit_pool
        self.message_pool = message_pool
        self.validators = validators

    async def listen(self):
        server = await websockets.serve(self.handler, "localhost", P2P_PORT)
        print(f"Listening for peer to peer connection on port: {P2P_PORT}")
        await server.wait_closed()

    async def handler(self, websocket, path):
        print("New connection")
        await self.connect_socket(websocket)
        try:
            async for message in websocket:
                await self.message_handler(websocket, message)
        finally:
            await self.disconnect_socket(websocket)

    async def connect_socket(self, socket):
        self.sockets.add(socket)
        print("Socket connected")

    async def disconnect_socket(self, socket):
        self.sockets.remove(socket)
        print("Socket disconnected")

    def connect_to_peers(self):
        loop = asyncio.get_event_loop()
        for peer in peers:
            asyncio.ensure_future(self.connect_peer(peer, loop))

    async def connect_peer(self, peer, loop):
        async with websockets.connect(peer) as websocket:
            await self.connect_socket(websocket)
            await websocket.wait_closed()

    def broadcast_transaction(self, transaction):
        message = json.dumps({"type": MESSAGE_TYPE["transaction"], "transaction": transaction})
        asyncio.ensure_future(self.broadcast(message))

    def send_transaction(self, socket, transaction):
        message = json.dumps({"type": MESSAGE_TYPE["transaction"], "transaction": transaction})
        asyncio.ensure_future(socket.send(message))

    def broadcast_pre_prepare(self, block):
        message = json.dumps({"type": MESSAGE_TYPE["pre_prepare"], "block": block})
        asyncio.ensure_future(self.broadcast(message))

    def send_pre_prepare(self, socket, block):
        message = json.dumps({"type": MESSAGE_TYPE["pre_prepare"], "block": block})
        asyncio.ensure_future(socket.send(message))

    def broadcast_prepare(self, prepare):
        message = json.dumps({"type": MESSAGE_TYPE["prepare"], "prepare": prepare})
        asyncio.ensure_future(self.broadcast(message))

    def send_prepare(self, socket, prepare):
        message = json.dumps({"type": MESSAGE_TYPE["prepare"], "prepare": prepare})
        asyncio.ensure_future(socket.send(message))

    def broadcast_commit(self, commit):
        message = json.dumps({"type": MESSAGE_TYPE["commit"], "commit": commit})
        asyncio.ensure_future(self.broadcast(message))

    def send_commit(self, socket, commit):
        message = json.dumps({"type": MESSAGE_TYPE["commit"], "commit": commit})
        asyncio.ensure_future(socket.send(message))

    def broadcast_round_change(self, message):
        message = json.dumps({"type": MESSAGE_TYPE["round_change"], "message": message})
        asyncio.ensure_future(self.broadcast(message))

    def send_round_change(self, socket, message):
        message = json.dumps({"type": MESSAGE_TYPE["round_change"], "message": message})
        asyncio.ensure_future(socket.send(message))

    async def broadcast(self, message):
        if self.sockets:
            await asyncio.wait([socket.send(message) for socket in self.sockets])

    async def message_handler(self, socket, message):
        data = json.loads(message)
        print(f"Received {data['type']}")
        message_type = data["type"]

        if message_type == MESSAGE_TYPE["transaction"]:
            await self.handle_transaction(data["transaction"], socket)
        elif message_type == MESSAGE_TYPE["pre_prepare"]:
            await self.handle_pre_prepare(data["block"], socket)
        elif message_type == MESSAGE_TYPE["prepare"]:
            await self.handle_prepare(data["prepare"], socket)
        elif message_type == MESSAGE_TYPE["commit"]:
            await self.handle_commit(data["commit"], socket)
        elif message_type == MESSAGE_TYPE["round_change"]:
            await self.handle_round_change(data["message"], socket)

    async def handle_transaction(self, transaction, socket):
        if (
            not self.transaction_pool.transaction_exists(transaction)
            and self.transaction_pool.verify_transaction(transaction)
            and self.validators.is_valid_validator(transaction["from"])
        ):
            threshold_reached = self.transaction_pool.add_transaction(transaction)
            await self.broadcast_transaction(transaction)

            if threshold_reached:
                print("THRESHOLD REACHED")
                if self.blockchain.get_proposer() == self.wallet.get_public_key():
                    print("PROPOSING BLOCK")
                    block = self.blockchain.create_block(self.transaction_pool.transactions, self.wallet)
                    print("CREATED BLOCK", block)
                    await self.broadcast_pre_prepare(block)
            else:
                print("Transaction Added")

    async def handle_pre_prepare(self, block, socket):
        if (
            not self.block_pool.existing_block(block)
            and self.blockchain.is_valid_block(block)
        ):
            self.block_pool.add_block(block)
            await self.broadcast_pre_prepare(block)

            prepare = self.prepare_pool.prepare(block, self.wallet)
            await self.broadcast_prepare(prepare)

    async def handle_prepare(self, prepare, socket):
        if (
            not self.prepare_pool.existing_prepare(prepare)
            and self.prepare_pool.is_valid_prepare(prepare, self.wallet)
            and self.validators.is_valid_validator(prepare["publicKey"])
        ):
            self.prepare_pool.add_prepare(prepare)
            await self.broadcast_prepare(prepare)

            # from pbft_txn_pool import TransactionPool
            # self.transaction_pool = TransactionPool
            # self.transaction_pool.clear()
            if len(self.prepare_pool.list[prepare["blockHash"]]) >= MIN_APPROVALS:
                self.transaction_pool.clear()
