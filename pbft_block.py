import hashlib
import json
from pbft_chain_util import ChainUtil
import random
import time
import logging
from collections import defaultdict


class Block:
    def __init__(self, timestamp, lastHash, hash,
                 data,proposer,signature, sequenceNo):

        self.timestamp = timestamp
        self.lastHash = lastHash
        self.hash = hash
        self.data = data
        self.proposer = proposer
        self.signature = signature
        self.sequenceNo = sequenceNo

    # def toString(self):
    #     print(f" {self.timestamp, self.lastHash, self.hash} " )
    def __str__(self):
        return f"Block - \n" \
               f"    Timestamp   : {self.timestamp}\n" \
               f"    Last Hash   : {self.lastHash}\n" \
               f"    Hash        : {self.hash}\n" \
               f"    Data        : {self.data}\n" \
               f"    Proposer    : {self.proposer}\n" \
               f"    Signature   : {self.signature}\n" \
               f"    Sequence No : {self.sequenceNo}"


    @staticmethod
    def genesis():
        return Block(
            "genesis time",
            "----",
            "genesis-hash",
            [],
            "P4@P@53R",
            "SIGN",
            0
        )


    @staticmethod
    def hash(timestamp, last_hash, data):
        return hashlib.sha256(json.dumps(f"{timestamp}{last_hash}{data}").encode()).hexdigest()


    @staticmethod
    def block_hash(block):
        return Block.hash(block.timestamp, block.last_hash, block.data)


    @staticmethod
    def sign_block_hash(hash_, wallet):
        return wallet.sign(hash_)


    @staticmethod
    def verify_block(block):
        return ChainUtil.verify_signature(
            block.proposer,
            block.signature,
            Block.hash(block.timestamp, block.last_hash, block.data)
        )


    @staticmethod
    def verify_proposer(block, proposer):
        return block.proposer == proposer
# zero = Block(1,1,1,1,1,1,1)
# print(zero)
        # data, proposer , signature, sequenceNo}")



