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

    def __iter__(self):
        return iter(self.transactions)

    def update_nonce(self):
        self.nonce += 1 #updates nonce for mining
    
    def __len__(self):
        return len(self.transactions)

    def append(self, tx: transaction, signature: str):
        self.transactions.append({'transaction': tx, 'signature': signature})

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
    from Crypto.PublicKey import RSA
    from json import dumps

    # Transaction!

    keypair = RSA.generate(2048)
    private_key = keypair.export_key().decode("ISO-8859-1")
    public_key = keypair.publickey().export_key().decode("ISO-8859-1")

    tx_id = 'diuewh3oijh'

    #tx: 10 -(9)-> 9, 1

    utxo_input = {
        'id': '221121',
        'tx_id': "ukdewhowi2",
        'address': public_key,
        'amount': 10
    }

    utxo_output1 = {
        'id': '029ue',
        'tx_id': tx_id,
        'address': "knedndl3w",
        'amount': 9
    }

    utxo_output2 = {
        'id': '2221',
        'tx_id': tx_id,
        'address': public_key,
        'amount': 1
    }

    tx_dict = {
        'transaction_id': tx_id,
        'sender_address': public_key,
        'receiver_address': 'knedndl3w',
        'amount': 9,
        'transaction_input': [utxo_input],
        'transaction_output': [utxo_output1, utxo_output2]
    }

    tx = transaction(**tx_dict)

    #sign tx
    signature = tx.sign_transaction(private_key)

    tx_dict_sent = tx.get_dict()

    #block

    block_dict = {
        'index': 22,
        'timestamp': int(time()),
        'transactions' : [{'transaction': tx_dict_sent, 'signature': signature}],
        'nonce' : 0,
        'previous_block_hash': "1"
    }

    block1 = block(**block_dict)

    hash_block = block1.hash()

    print(hash_block)

    block_dict_sent = block1.get_dict()
    ###################

    block2 = block(**block_dict_sent)

    print(block2.hash())

    print(dumps(block2.get_dict()))
