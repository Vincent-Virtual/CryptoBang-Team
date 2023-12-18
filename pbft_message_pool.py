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
