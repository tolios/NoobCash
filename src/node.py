from Crypto.PublicKey import RSA
from uuid import uuid4
from config import MINING_DIFFICULTY, CAPACITY
from blockchain import blockchain
from block import block
from transaction import transaction
from wallet import Wallet
from utxo import utxo

class node:
    #TODO Calculate throughtput and blocktime
    #TODO also add ip of node!
    def __init__(self, id = 0, ip = '127.0.0.1', port = "5000", peers = {}, wallet = None, blocks = []):
        # id is the same as port for simplicity
        self.id = id
        self.ip = ip
        self.port = port
        self.wallet = Wallet(**wallet) if wallet else self.create_wallet()
        self.blockchain = blockchain(blocks=blocks)
        self.peers = peers
        self.ip = f'http://localhost:{port}'

    def get_dict(self):
        return {
            "id": self.id,
            "ip": self.ip,
            "port": self.port,
            "wallet": self.wallet.get_dict(),
            "blockchain": self.blockchain.get_dict(),
            "peers": self.peers,
        }
    
    def register_peer(self, node_id, ip, address):
        self.peers[node_id] = {'ip': ip, 'address': address}

    def create_transaction(self, receiver_id, amount):
        #TODO dont really need the receiver id here, check outside!
        if receiver_id not in self.peers:
            raise ValueError("Receiver node not found in peers list")
        
        # Get the public key of the receiver node
        receiver_address = self.peers[receiver_id]["address"]

        #Check if amount is possible, get the utxos needed for transaction_input
        #but not remove them from the wallet!!! (we don't know if it is confimed yet!)
        # Find utxos to use as input transactions
        input_txns = []
        total_amount = 0
        for personal_utxo in self.wallet.utxos[self.wallet.public_key].values(): #access personal utxos 
            input_txns.append(personal_utxo)
            total_amount += personal_utxo.amount #calculate ammount of funds, while collecting utxos!
            if total_amount >= amount:
                break
        #check if it doesn't have enough
        if total_amount < amount:
            raise ValueError("Not enough funds in wallet to complete transaction")
        #start the transaction!
        transaction_id = str(uuid4().hex)
        output_txns = []
        #get the change for the transaction!
        change = total_amount - amount
        #one utxo for the sender, with the change, if zero, no need to make a utxo!
        if change != 0:
            output_txns.append(utxo(tx_id=transaction_id, address = self.wallet.public_key, amount = change))
        #now create utxo for the receiver!
        output_txns.append(utxo(tx_id=transaction_id, address = receiver_address, amount = amount))
        #TODO make it so you input utxo_dicts instead of objects
        # Create a new transaction using the transaction class
        tx = transaction(transaction_id = transaction_id, sender_address=self.wallet.public_key, receiver_address=receiver_address, 
                        amount=amount, transaction_input=input_txns, transaction_output=output_txns, expect_dict=False)
        
        # Sign the transaction using the sender node's private key
        signature = tx.sign_transaction(self.wallet.private_key)
        
        # Return the transaction and its signature as a tuple
        return tx.get_dict(), signature
    
    def broadcast_transaction():
        raise NotImplemented
    
    def verify_signature():
        raise NotImplemented
    
    def validate_transaction():
        raise NotImplemented

    def create_new_block(): #init block
        raise NotImplemented
    
    def broadcast_block():
        raise NotImplemented
    
    def valid_proof(difficulty=MINING_DIFFICULTY):
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
        return Wallet(public_key = public_key, private_key = private_key) #starts with no utxos
    
    @staticmethod
    def mine_block(bl: block, limit = 1e10):
        '''
            Receives a block, to mine it. Up to a limit...
        '''
        for _ in range(limit):
            b_hash = bl.hash()
            if b_hash[:MINING_DIFFICULTY] == "0"*MINING_DIFFICULTY:
                break #we mined successfuly!
            bl.update_nonce() #mine 


