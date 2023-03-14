from collections import OrderedDict
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from uuid import uuid4
from utxo import utxo

class transaction:
    '''
    Assumption: We do a transaction from only one node to only one node!
    '''
    def __init__(self, transaction_id: str = str(uuid4().hex), 
                sender_address: str = '', receiver_address: str = '', 
                amount: float = 0, transaction_input: list = [], transaction_output: list = [], expect_dict=True):
        #expects dictionary form!!!
        self.transaction_id = transaction_id #has a uuid, if not mentioned!
        self.sender_address = sender_address
        self.receiver_address = receiver_address
        self.amount = amount
        self.transaction_input = [utxo(**utxo_dict) for utxo_dict in transaction_input] if expect_dict else transaction_input
        self.transaction_output = [utxo(**utxo_dict) for utxo_dict in transaction_output] if expect_dict else transaction_output
    
    def get_dict(self)->dict:
        #create an OrderedDict without the signature!
        transaction_dict = OrderedDict({
            'transaction_id': self.transaction_id,
            'sender_address': self.sender_address,
            'receiver_address': self.receiver_address,
            'amount': self.amount,
            'transaction_input': [utxo_obj.get_dict() for utxo_obj in self.transaction_input],
            'transaction_output': [utxo_obj.get_dict() for utxo_obj in self.transaction_output]
        })
        return transaction_dict
    
    def _hash(self):
        return SHA256.new(str(self.get_dict()).encode("ISO-8859-1")) #Hash object of transaction. Used only inside methods!   

    def hash(self):
        return self._hash().hexdigest() #Hash in hex str form...

    def sign_transaction(self, private_key: str) -> str:
        # create a SHA-256 hash of the transaction's ordered dictionary representation
        # create a signer object using the private key encoded as bytes
        # sign the hash of the transaction with the private key
        # encode the signature as a string and return it
        return pss.new(RSA.importKey(private_key.encode("ISO-8859-1"))).sign(self._hash()).decode("ISO-8859-1")

    def verify_transaction(self, signature: str) -> bool:
        # get the public key from the sender's address
        #verify the signature, using the public key and the hash
        try:
            pss.new(RSA.importKey(self.sender_address.encode("ISO-8859-1"))).verify(self._hash(), signature.encode("ISO-8859-1"))
            return True
        except (ValueError, TypeError):
            return False
         
if __name__=="__main__":
    from json import dumps

    keypair = RSA.generate(2048)
    private_key = keypair.export_key().decode("ISO-8859-1")
    public_key = keypair.publickey().export_key().decode("ISO-8859-1")
    print(public_key)

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

    #verify signature
    print(tx.verify_transaction(signature))

    tx_dict_sent = tx.get_dict()

    ########################## simulate sending transaction!

    tx_received = transaction(**tx_dict_sent)

    #verify signature
    print(tx_received.verify_transaction(signature))

    print(dumps(tx_received.get_dict()))





