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
