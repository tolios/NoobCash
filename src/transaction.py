from collections import OrderedDict
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pss

#TODO fix transaction_input, transaction_output

class transaction:
    '''
    Assumption: We do a transaction from only one node to only one node!
    '''
    def __init__(self, transaction_id: str = '', sender_address: str = '', receiver_address: str = '', 
                amount: int = 0, transaction_input: list = [], transaction_output: list = []):

        self.transaction_id = transaction_id
        self.sender_address = sender_address
        self.receiver_address = receiver_address
        self.amount = amount
        self.transaction_input = transaction_input
        self.transaction_output = transaction_output
    
    def __dict__(self)->dict:
        #create an OrderedDict without the signature!
        transaction_dict = OrderedDict({
            'transaction_id': self.transaction_id,
            'sender_address': self.sender_address,
            'receiver_address': self.receiver_address,
            'amount': self.amount,
            'transaction_input': self.transaction_input,
            'transaction_output': self.transaction_output
        })
        return transaction_dict
    
    def _hash(self):
        return SHA256.new(str(self.__dict__()).encode("ISO-8859-1")) #Hash object of transaction. Used only inside methods!   

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

    keypair = RSA.generate(2048)
    private_key = keypair.export_key().decode("ISO-8859-1")
    public_key = keypair.publickey().export_key().decode("ISO-8859-1")
    print(public_key)




    # Create a sample transaction
    tx = transaction('123', public_key, 'address2', 100, ['input1', 'input2'], ['output1', 'output2'])

    # Sign the transaction using a private key
    signature = tx.sign_transaction(private_key)

    # Verify the transaction using the signature and the sender's address
    is_valid = tx.verify_transaction(signature)

    print(f"Is transaction valid? {is_valid}")

    print(tx.hash())
    print(tx.hash())