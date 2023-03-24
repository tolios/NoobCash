from block import block
from time import time
class blockchain:
    def __init__(self, blocks = [], c_time = None, dts = []):
        self.blocks = [block(**block_dict) for block_dict in blocks]
        self.c_time = time() if c_time is None else c_time #get time of chain updated (at the start its creation...)
        self.dts = dts #record of all time differences! (used for throughput and block_time)
    def __len__(self):
        return len(self.blocks)
    def __iter__(self):
        return iter(self.blocks)
    def __reversed__(self):
        return reversed(self.blocks)
    def append(self, block):
        self.blocks.append(block)
        #calculate time elapsed from blockchain update!
        t_new = time()
        self.dts.append(t_new - self.c_time)
        self.c_time = t_new
    def get_dict(self)->dict:
        return {'blocks': [block.get_dict() for block in self.blocks], 
                'c_time' : self.c_time, 'dts': self.dts}
    def last_block(self):
        return self.blocks[-1]