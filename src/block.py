from time import time
from collections import OrderedDict
from Crypto.Hash import SHA256

class block:

    def __init__(self, index: int, previous_block_hash: str):
        self.index = index
        self.timestamp = int(time())
        self.transactions = []
        self.nonce = 0 #initial
        self.previous_block_hash = previous_block_hash

    def update_nonce(self):
        self.nonce += 1 #updates nonce for mining
    
    def __len__(self):
        return len(self.transactions)

    def append(self, transaction):
        self.transactions.append(transaction)

    def __dict__(self)->dict:
        #create an OrderedDict without the hash!
        return OrderedDict({
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [dict(transaction) for transaction in self.transactions],
            'nonce': self.nonce,
            'previous_block_hash': self.previous_block_hash
        })
    
    def _hash(self):
        return SHA256.new(str(self.__dict__()).encode("ISO-8859-1")) #Hash object of block. Used only inside methods!   

    def hash(self):
        return self._hash().hexdigest() #Hash in hex str form...

if __name__=="__main__":

    block1 = block(0, 'eidhoi3hqioje')

    print(block1.hash())
    n = 4
    for i in range(115330):
        b_hash = block1.hash()
        if b_hash[:n] == "0"*n:
            print(i)
            print(b_hash)
            break
        block1.update_nonce() #mine
