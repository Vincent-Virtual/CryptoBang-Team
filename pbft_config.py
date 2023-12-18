# from typing import Any
#
#
# class config:
#     def __int__(self, TRANSACTION_THRESHOLD,
#                 NUMBER_OF_NODES, MIN_APPROVALS):
#         self._TRANSACTION_THRESHOLD = TRANSACTION_THRESHOLD
#         self._NUMBER_OF_NODES = NUMBER_OF_NODES
#         self._MIN_APPROVALS = 2 * (NUMBER_OF_NODES // 3) + 1
#         #NUMBER_OF_NODES = 3
#         # Maximum number of transactions that can be present in a block and transaction pool
#
#         #
#         # Total number of nodes in the network
#
#
#         # Minimum number of positive votes required for the message/block to be valid
#         #MIN_APPROVALS =
#
#     def get_MIN_APPROVALS(self):
#         return self.MIN_APPROVALS
#
#     def set_MIN_APPROVALS(self, new_MIN_APPROVALS):
#         if isinstance(new_MIN_APPROVALS, int) & new_MIN_APPROVALS > 0 & new_MIN_APPROVALS < 120:
#
#             self._MIN_APPROVALS = new_MIN_APPROVALS
#
#     def get_TRANSACTION_THRESHOLD(self):
#         return self._TRANSACTION_THRESHOLD
#
#     def set_TRANSACTION_THRESHOLD(self, new_TRANSACTION_THRESHOLD):
#         self._TRANSACTION_THRESHOLD = new_TRANSACTION_THRESHOLD
#
#
#     def get_NUMBER_OF_NODES(self):
#         return self._NUMBER_OF_NODES
#
#     def set_NUMBER_OF_NODES(self, new_NUMBER_OF_NODES):
#         if isinstance(new_NUMBER_OF_NODES, int) & new_NUMBER_OF_NODES > 0 & new_NUMBER_OF_NODES < 120:
#             set._NUMBER_OF_NODES = new_NUMBER_OF_NODES
#
#     def __str__(self):
#         return f"Block - \n" \
#                f"    NUMBER_OF_NODES   : {self._NUMBER_OF_NODES}\n" \
#                f"    TRANSACTION_THRESHOLD   : {self._TRANSACTION_THRESHOLD}\n" \
#                f"    MIN_APPROVALS        : {self._MIN_APPROVALS}\n"
#
#
#
# zero = config()
# zero.set_NUMBER_OF_NODES(1)
#
# zero.__str__()
# # zero.NUMBER_OF_NODES
#         # Exporting variables
#         #__all__ = ["TRANSACTION_THRESHOLD","NUMBER_OF_NODES", "MIN_APPROVALS"]
class config:
    def __init__(self, TRANSACTION_THRESHOLD, NUMBER_OF_NODES, MIN_APPROVALS):
        self._transaction_threshold = TRANSACTION_THRESHOLD
        self._number_of_nodes = NUMBER_OF_NODES
        self._min_approvals = MIN_APPROVALS
        # TRANSACTION_THRESHOLD = 5
        # NUMBER_OF_NODES = 3
        # MIN_APPROVALS = 2 * (NUMBER_OF_NODES / 3) + 1

    def get_TRANSACTION_THRESHOLD(self):
        return self._transaction_threshold

    #@TRANSACTION_THRESHOLD.setter
    def set_TRANSACTION_THRESHOLD(self, value):
        self._transaction_threshold = value

    @property
    def get_NUMBER_OF_NODES(self):
        return self._number_of_nodes

   # @NUMBER_OF_NODES.setter
    def set_NUMBER_OF_NODES(self, value):
        self._number_of_nodes = value

    @property
    def get_MIN_APPROVALS(self):
        return self._min_approvals

    #@MIN_APPROVALS.setter
    def set_MIN_APPROVALS(self, value):
        self._min_approvals = value
#
# # Example usage:
# # Create an instance of the class with your desired values
# config = Config(5, 3, 2)
#
# # Access the parameters using getters
# print("TRANSACTION_THRESHOLD:", config.TRANSACTION_THRESHOLD)
# print("NUMBER_OF_NODES:", config.NUMBER_OF_NODES)
# print("MIN_APPROVALS:", config.MIN_APPROVALS)
#
# # Update the parameters using setters
# config.TRANSACTION_THRESHOLD = 10
# config.NUMBER_OF_NODES = 5
# config.MIN_APPROVALS = 3

# # Access the updated parameters
# print("Updated TRANSACTION_THRESHOLD:", config.TRANSACTION_THRESHOLD)
# print("Updated NUMBER_OF_NODES:", config.NUMBER_OF_NODES)
# print("Updated MIN_APPROVALS:", config.MIN_APPROVALS)
