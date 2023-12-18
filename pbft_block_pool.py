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
