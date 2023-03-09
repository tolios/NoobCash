from block import block
class blockchain:
    def __init__(self, blocks = []):
        self.blocks = [block(**block_dict) for block_dict in blocks]
    def append(self, block):
        self.blocks.append(block)
    def get_dict(self)->dict:
        return {'blocks': [block.get_dict() for block in self.blocks]}
    def last_block_hash(self):
        return self.block.hash()
    