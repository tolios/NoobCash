from collections import OrderedDict
from uuid import uuid4

'''
utxo: The basic building block of the cryptocurrency
'''

class utxo:
    def __init__(self, id = str(uuid4().hex), tx_id:str = '', address:str = '', amount:int = 0):
        self.id = id # uuid of utxo, the moment it is created!
        self.tx_id = tx_id #transaction id that made the utxo
        self.address = address #public key of owner
        self.amount = amount #amount that utxo represents

    def __eq__(self, other) -> bool:
        if not (self.id == other.id):
            return False
        if not (self.tx_id == other.tx_id):
            return False
        if not (self.address == other.address):
            return False
        if not (self.amount == other.amount):
            return False
        #all information is the same...
        return True
    
    def get_dict(self):
        return OrderedDict({
            'id': self.id,
            'tx_id': self.tx_id,
            'address': self.address,
            'amount': self.amount,
        })
