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

new_config = config(5, 3, 2)


# Update the parameters using setters
new_config.TRANSACTION_THRESHOLD = 10
new_config.NUMBER_OF_NODES = 5
new_config.MIN_APPROVALS = 2 * (new_config.NUMBER_OF_NODES / 3) + 1

# # Access the parameters using getters
# print("TRANSACTION_THRESHOLD:", new_config.TRANSACTION_THRESHOLD)
# print("NUMBER_OF_NODES:", new_config.NUMBER_OF_NODES)
# print("MIN_APPROVALS:", new_config.MIN_APPROVALS)
# #
app = Flask(__name__)
secret = "your_secret_here"
# secret_bytes = secret.encode('utf-8')
# print(secret_bytes)
# secret_bytes.decode()

new_wallet = Wallet(secret)  # Replace with your actual secret
transaction_pool = TransactionPool()
validators = Validators(new_config.NUMBER_OF_NODES)
blockchain = Blockchain(validators, new_config.NUMBER_OF_NODES)
block_pool = BlockPool()
prepare_pool = PreparePool()
commit_pool = CommitPool()
message_pool = MessagePool()
p2p_server = P2pServer(
    blockchain, transaction_pool, new_wallet, block_pool,
    prepare_pool, commit_pool, message_pool, validators
)

# @app.route("/transactions", methods=["GET"])
# def get_transactions():
#     return jsonify(transaction_pool.transactions), 200
#
# @app.route("/blocks", methods=["GET"])
# def get_blocks():
#     return jsonify(blockchain.chain), 200
#
# @app.route("/transact", methods=["POST"])
# def transact():
#     data = request.json.get("data")
#     transaction = wallet.create_transaction(data)
#     p2p_server.broadcast_transaction(transaction)
#     return redirect("/transactions"), 303
#
# if __name__ == "__main__":
#     app.run(port=3001)
#     p2p_server.listen()
