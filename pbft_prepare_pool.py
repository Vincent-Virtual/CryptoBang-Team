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
