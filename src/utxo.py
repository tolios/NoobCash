from collections import OrderedDict
from uuid import uuid4

'''
utxo: The basic building block of the cryptocurrency
'''

class utxo:
    def __init__(self, id = str(uuid4().hex), tx_id:str = '', address:str = '', amount:int = 0, spent = False):
        self.id = id # uuid of utxo, the moment it is created!
        self.tx_id = tx_id #transaction id that made the utxo
        self.address = address #public key of owner
        self.amount = amount #amount that utxo represents
        self.spent = spent #False, if not spent!
    
    def get_dict(self):
        return OrderedDict({
            'tx_id': self.tx_id,
            'address': self.address,
            'amount': self.amount,
            'spent': self.spent
        })
    
    def marked_spent(self):
        self.spent = True
