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
