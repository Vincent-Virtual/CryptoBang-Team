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
