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
        self.set_tx_id = set([tx_dict['transaction'].transaction_id for tx_dict in self.transactions])

    def __iter__(self):
        return iter(self.transactions)
    
    def __contains__(self, tx_id: str):
        #finds if it is contained in set of tx ids!
        return self.set_tx_id.__contains__(tx_id)

    def update_nonce(self):
        self.nonce += 1 #updates nonce for mining
    
    def __len__(self):
        return len(self.transactions)

    def append(self, tx: transaction, signature: str):
        self.transactions.append({'transaction': tx, 'signature': signature})
        self.set_tx_id.add(tx.transaction_id)

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
