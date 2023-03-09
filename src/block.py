from time import time
from collections import OrderedDict
from Crypto.Hash import SHA256
from transaction import transaction

class block:

    def __init__(self, index: int = 0, timestamp = int(time()), 
                transactions: list = [], nonce: int = 0, previous_block_hash: str = "1"):
        self.index = index
        self.timestamp = timestamp #creates transaction objects from dict and gets the signature!
        self.transactions = [{'transaction': transaction(**tx_dict['transaction']), 'signature': tx_dict['signature']} \
                            for tx_dict in transactions]
        self.nonce = nonce
        self.previous_block_hash = previous_block_hash

    def update_nonce(self):
        self.nonce += 1 #updates nonce for mining
    
    def __len__(self):
        return len(self.transactions)

    def append(self, transaction: transaction):
        self.transactions.append(transaction)

    def get_dict(self)->dict:
        #create an OrderedDict without the hash! (OrderedDict needed to get same hash each time!)
        return OrderedDict({
            'index': self.index,
            'timestamp': self.timestamp, #gets transaction dict and signature for all transactions!
            'transactions': [OrderedDict({'transaction': tx_dict['transaction'].get_dict(), 'signature': tx_dict['signature']})
                            for tx_dict in self.transactions],
            'nonce': self.nonce,
            'previous_block_hash': self.previous_block_hash
        })
    
    def _hash(self):
        return SHA256.new(str(self.get_dict()).encode("ISO-8859-1")) #Hash object of block. Used only inside methods!   

    def hash(self):
        return self._hash().hexdigest() #Hash in hex str form...

if __name__=="__main__":

    block1 = block(index = 0, previous_block_hash='eidhoi3hqioje')

    print(block1.hash())
    n = 4
    for i in range(115330):
        b_hash = block1.hash()
        if b_hash[:n] == "0"*n:
            print(i)
            print(b_hash)
            break
        block1.update_nonce() #mine
