from parsimonious import NodeVisitor
from fryweb.config import fryconfig

class BaseGenerator(NodeVisitor):
    def __init__(self):
        self.client_embed_count = 0

    def inc_client_embed(self):
        count = self.client_embed_count
        self.client_embed_count = count + 1
        return count 

    def reset_client_embed(self):
        self.client_embed_count = 0



