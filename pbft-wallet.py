from pbft_chain_util import ChainUtil  # Assuming you have a ChainUtil module with the required functions
from pbft_transaction import Transaction  # Assuming you have a Transaction class defined

class Wallet:
    def __init__(self, secret):
        self.key_pair = ChainUtil.gen_key_pair(secret)
        self.public_key = self.key_pair.get_public_key().to_string().hex()

    def __str__(self):
        return f"Wallet - \n" \
               f"    publicKey: {self.public_key}"

    def sign(self, data_hash):
        return self.key_pair.sign(data_hash.encode()).hex()

    def create_transaction(self, data):
        return Transaction(data, self)

    def get_public_key(self):
        return self.public_key

# Assuming you have a ChainUtil module with the required functions
# and a Transaction class defined
