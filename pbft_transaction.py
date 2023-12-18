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
