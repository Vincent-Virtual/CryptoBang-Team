from pbft_chain_util import ChainUtil  # Assuming you have a ChainUtil module with the required functions
from cryptography.hazmat.primitives import serialization

from pbft_transaction import Transaction  # Assuming you have a Transaction class defined
from cryptography.hazmat.primitives.asymmetric import ed25519


class Wallet:
    def __init__(self, secret):
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        secret_bytes = secret.encode('utf-8')
        signature = private_key.sign(secret_bytes)

        self.public_key_hex = public_key.public_bytes(
            # encoding=ed25519.Encoding.Raw,
            # format=ed25519.PublicFormat.Raw
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        ).hex()
        self.signature_hex = signature.hex()

        # Additional code related to ChainUtil, assuming it has a similar structure
        # Replace this with the actual implementation in your code
        # For example, self.key_pair = ChainUtil.gen_key_pair(secret)

        # Print statements for testing
        print(f"{secret} in the Wallet section")
        print(f"Public Key: {self.public_key_hex}")
        print(f"Signature: {self.signature_hex}")

    def __str__(self):
        return f"Wallet - \n" \
               f"    publicKey: {self.public_key}"

    def sign(self, data_hash):
        return self.key_pair.sign(data_hash.encode()).hex()

    def create_transaction(self, data):
        return Transaction(data, self)

    def get_public_key(self):
        #return self.public_key
        return self.public_key_hex

# Assuming you have a ChainUtil module with the required functions
# and a Transaction class defined

from pbft_wallet import Wallet  # Assuming you have a Wallet class defined

class Validators:
    def __init__(self, number_of_validators):
        self.list = self.generate_addresses(number_of_validators)

    def generate_addresses(self, number_of_validators):
        return [Wallet("NODE" + str(i)).get_public_key() for i in range(number_of_validators)]

    def is_valid_validator(self, validator):
        return validator in self.list

# Assuming you have a Wallet class defined


from pbft_transaction import Transaction  # Assuming you have a Transaction class defined
from pbft_config import config
from pbft_chain_util import ChainUtil

#TRANSACTION_THRESHOLD = config.get_TRANSACTION_THRESHOLD()

config = config(5, 3, 2)
#
# # Access the parameters using getters
# print("TRANSACTION_THRESHOLD:", config.TRANSACTION_THRESHOLD)
# print("NUMBER_OF_NODES:", config.NUMBER_OF_NODES)
# print("MIN_APPROVALS:", config.MIN_APPROVALS)
#
# # Update the parameters using setters
TRANSACTION_THRESHOLD = 10
NUMBER_OF_NODES = 5
MIN_APPROVALS = 3
#print(config.get_MIN_APPROVALS())
class TransactionPool:
    def __init__(self):
        self.transactions = []

    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        return len(self.transactions) >= TRANSACTION_THRESHOLD

    @staticmethod
    def verify_transaction(transaction):
        return Transaction.verify_transaction(transaction)

    def transaction_exists(self, transaction):
        return any(t.id == transaction.id for t in self.transactions)

    def clear(self):
        print("TRANSACTION POOL CLEARED")
        self.transactions = []

# Assuming you have a Transaction class and TRANSACTION_THRESHOLD defined in respective modules

from pbft_chain_util import ChainUtil  # Assuming you have a ChainUtil module with the required functions
import time

class Transaction:
    def __init__(self, data, wallet):
        self.id = ChainUtil.id()
        self.from_ = wallet.public_key
        self.input = {'data': data, 'timestamp': int(time.time() * 1000)}
        self.hash = ChainUtil.hash(self.input)
        self.signature = wallet.sign(self.hash)

    @staticmethod
    def verify_transaction(transaction):
        return ChainUtil.verify_signature(
            transaction.from_,
            transaction.signature,
            ChainUtil.hash(transaction.input)
        )

# Assuming you have a ChainUtil module with the required functions
# You might need to replace this with the actual import statement.
# Example: from chain_util import ChainUtil

from pbft_chain_util import ChainUtil  # Assuming you have a ChainUtil module with the required functions

class PreparePool:
    def __init__(self):
        self.list = {}

    def prepare(self, block, wallet):
        prepare_message = self.create_prepare(block, wallet)
        self.list[block.hash] = [prepare_message]
        return prepare_message

    def create_prepare(self, block, wallet):
        prepare_message = {
            'blockHash': block.hash,
            'publicKey': wallet.get_public_key(),
            'signature': wallet.sign(block.hash)
        }
        return prepare_message

    def add_prepare(self, prepare):
        self.list[prepare['blockHash']].append(prepare)

    def existing_prepare(self, prepare):
        exists = any(p['publicKey'] == prepare['publicKey'] for p in self.list.get(prepare['blockHash'], []))
        return exists

    def is_valid_prepare(self, prepare):
        return ChainUtil.verify_signature(prepare['publicKey'], prepare['signature'], prepare['blockHash'])

# Assuming you have a ChainUtil module with the required functions
# Make sure to adjust the import statements based on your actual module structure

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

from pbft_chain_util import ChainUtil  # Import the ChainUtil class

class MessagePool:
    def __init__(self):
        self.list = {}
        self.message = "INITIATE NEW ROUND"

    def create_message(self, block_hash, wallet):
        round_change = {
            "publicKey": wallet.get_public_key(),
            "message": self.message,
            "signature": wallet.sign(ChainUtil.hash(self.message + block_hash)),
            "blockHash": block_hash,
        }

        self.list[block_hash] = [round_change]
        return round_change

    def existing_message(self, message):
        if message["blockHash"] in self.list:
            exists = any(p["publicKey"] == message["publicKey"] for p in self.list[message["blockHash"]])
            return exists
        else:
            return False

    def is_valid_message(self, message):
        return ChainUtil.verify_signature(
            message["publicKey"],
            message["signature"],
            ChainUtil.hash(message["message"] + message["blockHash"])
        )

    def add_message(self, message):
        self.list.setdefault(message["blockHash"], []).append(message)

# Example usage:
# If you want to use this Python code, make sure to create a chain_util.py file
# with the ChainUtil class and import it appropriately.

# from typing import Any
#
#
# class config:
#     def __int__(self, TRANSACTION_THRESHOLD,
#                 NUMBER_OF_NODES, MIN_APPROVALS):
#         self._TRANSACTION_THRESHOLD = TRANSACTION_THRESHOLD
#         self._NUMBER_OF_NODES = NUMBER_OF_NODES
#         self._MIN_APPROVALS = 2 * (NUMBER_OF_NODES // 3) + 1
#         #NUMBER_OF_NODES = 3
#         # Maximum number of transactions that can be present in a block and transaction pool
#
#         #
#         # Total number of nodes in the network
#
#
#         # Minimum number of positive votes required for the message/block to be valid
#         #MIN_APPROVALS =
#
#     def get_MIN_APPROVALS(self):
#         return self.MIN_APPROVALS
#
#     def set_MIN_APPROVALS(self, new_MIN_APPROVALS):
#         if isinstance(new_MIN_APPROVALS, int) & new_MIN_APPROVALS > 0 & new_MIN_APPROVALS < 120:
#
#             self._MIN_APPROVALS = new_MIN_APPROVALS
#
#     def get_TRANSACTION_THRESHOLD(self):
#         return self._TRANSACTION_THRESHOLD
#
#     def set_TRANSACTION_THRESHOLD(self, new_TRANSACTION_THRESHOLD):
#         self._TRANSACTION_THRESHOLD = new_TRANSACTION_THRESHOLD
#
#
#     def get_NUMBER_OF_NODES(self):
#         return self._NUMBER_OF_NODES
#
#     def set_NUMBER_OF_NODES(self, new_NUMBER_OF_NODES):
#         if isinstance(new_NUMBER_OF_NODES, int) & new_NUMBER_OF_NODES > 0 & new_NUMBER_OF_NODES < 120:
#             set._NUMBER_OF_NODES = new_NUMBER_OF_NODES
#
#     def __str__(self):
#         return f"Block - \n" \
#                f"    NUMBER_OF_NODES   : {self._NUMBER_OF_NODES}\n" \
#                f"    TRANSACTION_THRESHOLD   : {self._TRANSACTION_THRESHOLD}\n" \
#                f"    MIN_APPROVALS        : {self._MIN_APPROVALS}\n"
#
#
#
# zero = config()
# zero.set_NUMBER_OF_NODES(1)
#
# zero.__str__()
# # zero.NUMBER_OF_NODES
#         # Exporting variables
#         #__all__ = ["TRANSACTION_THRESHOLD","NUMBER_OF_NODES", "MIN_APPROVALS"]
class config:
    def __init__(self, TRANSACTION_THRESHOLD, NUMBER_OF_NODES, MIN_APPROVALS):
        self._transaction_threshold = TRANSACTION_THRESHOLD
        self._number_of_nodes = NUMBER_OF_NODES
        self._min_approvals = MIN_APPROVALS
        # TRANSACTION_THRESHOLD = 5
        # NUMBER_OF_NODES = 3
        # MIN_APPROVALS = 2 * (NUMBER_OF_NODES / 3) + 1

    def get_TRANSACTION_THRESHOLD(self):
        return self._transaction_threshold

    #@TRANSACTION_THRESHOLD.setter
    def set_TRANSACTION_THRESHOLD(self, value):
        self._transaction_threshold = value

    @property
    def get_NUMBER_OF_NODES(self):
        return self._number_of_nodes

   # @NUMBER_OF_NODES.setter
    def set_NUMBER_OF_NODES(self, value):
        self._number_of_nodes = value

    @property
    def get_MIN_APPROVALS(self):
        return self._min_approvals

    #@MIN_APPROVALS.setter
    def set_MIN_APPROVALS(self, value):
        self._min_approvals = value
#
# # Example usage:
# # Create an instance of the class with your desired values
# config = Config(5, 3, 2)
#
# # Access the parameters using getters
# print("TRANSACTION_THRESHOLD:", config.TRANSACTION_THRESHOLD)
# print("NUMBER_OF_NODES:", config.NUMBER_OF_NODES)
# print("MIN_APPROVALS:", config.MIN_APPROVALS)
#
# # Update the parameters using setters
# config.TRANSACTION_THRESHOLD = 10
# config.NUMBER_OF_NODES = 5
# config.MIN_APPROVALS = 3

# # Access the updated parameters
# print("Updated TRANSACTION_THRESHOLD:", config.TRANSACTION_THRESHOLD)
# print("Updated NUMBER_OF_NODES:", config.NUMBER_OF_NODES)
# print("Updated MIN_APPROVALS:", config.MIN_APPROVALS)

from pbft_chain_util import ChainUtil  # Import the ChainUtil class

class CommitPool:
    def __init__(self):
        self.list = {}

    def commit(self, prepare, wallet):
        commit = self.create_commit(prepare, wallet)
        self.list[prepare["blockHash"]] = [commit]
        return commit

    def create_commit(self, prepare, wallet):
        commit = {
            "blockHash": prepare["blockHash"],
            "publicKey": wallet.get_public_key(),
            "signature": wallet.sign(prepare["blockHash"]),
        }
        return commit

    def existing_commit(self, commit):
        exists = any(p["publicKey"] == commit["publicKey"] for p in self.list.get(commit["blockHash"], []))
        return exists

    def is_valid_commit(self, commit):
        return ChainUtil.verify_signature(
            commit["publicKey"],
            commit["signature"],
            commit["blockHash"]
        )

    def add_commit(self, commit):
        self.list.setdefault(commit["blockHash"], []).append(commit)

# Example usage:
# If you want to use this Python code, make sure to create a chain_util.py file
# with the ChainUtil class and import it appropriately.

#from ellipticcurve.eddsa import Eddsa
import uuid
from Crypto.Hash import SHA256
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

class ChainUtil:
    # ed25519 allows us to create key pair from secret
   # eddsa = Eddsa("ed25519")
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # a static function to return keypair generated using a secret phrase
    @staticmethod
    def gen_key_pair(secret):

        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        secret_bytes = secret.encode('utf-8')
        signature = private_key.sign(secret_bytes)
        return signature

    # returns ids used in transactions
    @staticmethod
    def generate_id():
        return str(uuid.uuid4())

    # hashes any data using SHA256
    @staticmethod
    def hash_data(data):
        return SHA256.new(data.encode()).hexdigest()

    # verifies the signed hash by decrypting it with public key
    # and matching it with the hash
    @staticmethod
    def verify_signature(public_key, signature, data_hash):
        try:
            public_key.verify(public_key, data_hash, sig_alg=ed25519.Ed25519())
            return True
        except InvalidSignature:
            return False
#
# # Example usage:
# public_key_bytes = b'\x01\x23\x45\x67\x89\xab\xcd\xef'  # Replace with your actual public key bytes
# signature_bytes = b'\x01\x23\x45\x67\x89\xab\xcd\xef'  # Replace with your actual signature bytes
# data_bytes = b'Your data'  # Replace with your actual data bytes


# def verify_signature(public_key_bytes, signature_bytes, data_bytes):
#     pass
#
#
# if verify_signature(public_key_bytes, signature_bytes, data_bytes):
#     print("Signature is valid.")
# else:
#     print("Signature is invalid.")
# ff = str(uuid.uuid4())
# print(ff)

from pbft_block import Block  # Import the Block class
import random
from pbft_wallet import Wallet  # Import the Wallet class from your Python implementation

class Blockchain:
    def __init__(self, validators, NUMBER_OF_NODES):
        self.validator_list = validators.generate_addresses(NUMBER_OF_NODES)
        self.chain = [Block.genesis()]



    # def generate_addresses(number_of_validators):
    #     wallet_list = []
    #     for i in range(number_of_validators):
    #         wallet = Wallet("NODE" + str(i))
    #         wallet_list.append(wallet.get_public_key())
    #     return wallet_list

    def add_block(self, block):
        self.chain.append(block)
        print("NEW BLOCK ADDED TO CHAIN")
        return block

    def create_block(self, transactions, wallet):
        last_block = self.chain[-1]
        block = Block.create_block(last_block, transactions, wallet)
        return block

    def get_proposer(self):
        last_block_hash = self.chain[-1].hash
        index = ord(last_block_hash[0]) % len(self.validator_list)
        return self.validator_list[index]

    def is_valid_block(self, block):
        last_block = self.chain[-1]
        if (
            last_block.sequence_no + 1 == block.sequence_no
            and block.last_hash == last_block.hash
            and block.hash == Block.block_hash(block)
            and Block.verify_block(block)
            and Block.verify_proposer(block, self.get_proposer())
        ):
            print("BLOCK VALID")
            return True
        else:
            print("BLOCK INVALID")
            return False

    def add_updated_block(self, block_hash, block_pool, prepare_pool, commit_pool):
        block = block_pool.get_block(block_hash)
        block.prepare_messages = prepare_pool.list[block_hash]
        block.commit_messages = commit_pool.list[block_hash]
        self.add_block(block)

# Example usage:
# If you want to use this Python code, make sure to create a block.py file
# with the Block class and import it appropriately.

from pbft_block import Block  # Import the Block class

class BlockPool:
    def __init__(self):
        self.list = []

    def existing_block(self, block):
        exists = any(b.hash == block.hash for b in self.list)
        return exists

    def add_block(self, block):
        self.list.append(block)
        print("Added block to pool")

    def get_block(self, hash):
        exists = next((b for b in self.list if b.hash == hash), None)
        return exists

# Example usage:
# If you want to use this Python code, make sure to create a block.py file
# with the Block class and import it appropriately.

import hashlib
import json
from pbft_chain_util import ChainUtil
import random
import time
import logging
from collections import defaultdict


class Block:
    def __init__(self, timestamp, lastHash, hash,
                 data,proposer,signature, sequenceNo):

        self.timestamp = timestamp
        self.lastHash = lastHash
        self.hash = hash
        self.data = data
        self.proposer = proposer
        self.signature = signature
        self.sequenceNo = sequenceNo

    # def toString(self):
    #     print(f" {self.timestamp, self.lastHash, self.hash} " )
    def __str__(self):
        return f"Block - \n" \
               f"    Timestamp   : {self.timestamp}\n" \
               f"    Last Hash   : {self.lastHash}\n" \
               f"    Hash        : {self.hash}\n" \
               f"    Data        : {self.data}\n" \
               f"    Proposer    : {self.proposer}\n" \
               f"    Signature   : {self.signature}\n" \
               f"    Sequence No : {self.sequenceNo}"


    @staticmethod
    def genesis():
        return Block(
            "genesis time",
            "----",
            "genesis-hash",
            [],
            "P4@P@53R",
            "SIGN",
            0
        )


    @staticmethod
    def hash(timestamp, last_hash, data):
        return hashlib.sha256(json.dumps(f"{timestamp}{last_hash}{data}").encode()).hexdigest()


    @staticmethod
    def block_hash(block):
        return Block.hash(block.timestamp, block.last_hash, block.data)


    @staticmethod
    def sign_block_hash(hash_, wallet):
        return wallet.sign(hash_)


    @staticmethod
    def verify_block(block):
        return ChainUtil.verify_signature(
            block.proposer,
            block.signature,
            Block.hash(block.timestamp, block.last_hash, block.data)
        )


    @staticmethod
    def verify_proposer(block, proposer):
        return block.proposer == proposer
# zero = Block(1,1,1,1,1,1,1)
# print(zero)
        # data, proposer , signature, sequenceNo}")

from flask import Flask, jsonify, request, redirect
from pbft_wallet import Wallet  # Assuming you have a Wallet class defined
from pbft_txn_pool import TransactionPool  # Assuming you have a TransactionPool class defined
from pbft_validator import Validators  # Assuming you have a Validators class defined
from pbft_blockchain import Blockchain  # Assuming you have a Blockchain class defined
from pbft_block_pool import BlockPool  # Assuming you have a BlockPool class defined
from pbft_prepare_pool import PreparePool  # Assuming you have a PreparePool class defined
from pbft_cimmit_pool import CommitPool  # Assuming you have a CommitPool class defined
from pbft_message_pool import MessagePool  # Assuming you have a MessagePool class defined
from pbft_p2p_server import P2pServer  # Assuming you have a P2pServer class defined
  # Assuming you have NUMBER_OF_NODES defined in config module
from pbft_config import config

app = Flask(__name__)

@app.route("/transactions", methods=["GET"])
def get_transactions():
    return jsonify(transaction_pool.transactions), 200

@app.route("/blocks", methods=["GET"])
def get_blocks():
    return jsonify(blockchain.chain), 200

@app.route("/transact", methods=["POST"])
def transact():
    data = request.json.get("data")
    transaction = new_wallet.create_transaction(data)
    p2p_server.broadcast_transaction(transaction)
    return redirect("/transactions"), 303
#
if __name__ == "__main__":
    NUMBER_OF_NODES = int(input("enter number of nodes "))
    secret = input("Please enter your secret ")
    port_number = input("enter the port number ")
    TRANSACTION_THRESHOLD = 10
    new_config = config(NUMBER_OF_NODES, TRANSACTION_THRESHOLD, 2)

    # Update the parameters using setters
    #new_config.NUMBER_OF_NODES = 5
    new_config.MIN_APPROVALS = 2 * (NUMBER_OF_NODES / 3) + 1


    #secret = "your_secret_here"

    new_wallet = Wallet(secret)  # Replace with your actual secret
    transaction_pool = TransactionPool()
    validators = Validators(NUMBER_OF_NODES)
    blockchain = Blockchain(validators, NUMBER_OF_NODES)
    block_pool = BlockPool()
    prepare_pool = PreparePool()
    commit_pool = CommitPool()
    message_pool = MessagePool()
    p2p_server = P2pServer(
        blockchain, transaction_pool, new_wallet, block_pool,
        prepare_pool, commit_pool, message_pool, validators
    )

    app.run(port=port_number)
    p2p_server.listen()
    
    