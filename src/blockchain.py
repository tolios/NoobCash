class blockchain:
    def __init__(self, blocks = []):
        self.blocks = blocks
    def append(self, block):
        self.blocks.append(block)
    def __dict__(self):
        return {'blocks': [dict(block) for block in self.blocks]}
    def last_block_hash(self):
        return self.block.hash()
    