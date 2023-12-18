from pbft_transaction import Transaction  # Assuming you have a Transaction class defined
from pbft_chain_util import ChainUtil

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
