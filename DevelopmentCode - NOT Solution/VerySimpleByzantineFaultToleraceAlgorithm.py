class Node:
    def _init_(self, node_id):
        self.node_id = node_id
        self.sequence_number = 0
        self.state = {}
        self.requests = []

    def pre_prepare(self, request):
        # Pre-prepare phase
        message = f"Pre-prepare: {request}"
        self.broadcast(message)

    def prepare(self, request):
        # Prepare phase
        message = f"Prepare: {request}"
        self.broadcast(message)

    def commit(self, request):
        # Commit phase
        message = f"Commit: {request}"
        self.broadcast(message)

    def broadcast(self, message):
        # Simulated broadcast to all nodes
        print(f"Node {self.node_id} broadcasts: {mes