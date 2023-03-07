from Crypto.PublicKey import RSA
from wallet import Wallet
import block

class node:
    #TODO Calculate throughtput and blocktime

    def __init__(self):
        #here we store information for every node, as its id, its address (ip:port) its public key and its balance
        #chain of node
        #id,port 
        #wallet
        #other nodes
        pass

    def create_transaction():
        raise NotImplemented
    
    def sign_transaction():
        raise NotImplemented
    
    def broadcast_transaction():
        raise NotImplemented
    
    def verify_signature():
        raise NotImplemented
    
    def validate_transaction():
        raise NotImplemented

    def create_new_block():
        raise NotImplemented
    
    def mine_block():
        raise NotImplemented
    
    def broadcast_block():
        raise NotImplemented
        
    def validate_chain():
        raise NotImplemented
        
    def resolve_conflict():
        raise NotImplemented

    @staticmethod
    def create_wallet():
        #create a wallet for this node, with a public key and a private key
        keypair = RSA.generate(2048)
        private_key = keypair.export_key().decode("ISO-8859-1")
        public_key = keypair.publickey().export_key().decode("ISO-8859-1")
        return Wallet(public_key, private_key)

