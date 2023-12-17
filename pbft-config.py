
class TRANSACTION_THRESHOLD():

    # Maximum number of transactions that can be present in a block and transaction pool

    TRANSACTION_THRESHOLD = 5

    # Total number of nodes in the network
    NUMBER_OF_NODES = 3

    # Minimum number of positive votes required for the message/block to be valid
    MIN_APPROVALS = 2 * (NUMBER_OF_NODES // 3) + 1

    # Exporting variables
    __all__ = ["TRANSACTION_THRESHOLD","NUMBER_OF_NODES", "MIN_APPROVALS"]
