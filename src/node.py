from Crypto.PublicKey import RSA
from uuid import uuid4
from config import MINING_DIFFICULTY, CAPACITY, N
from blockchain import blockchain
from block import block
from transaction import transaction
from wallet import Wallet
from utxo import utxo

class node:
    #TODO Calculate throughtput and blocktime
    #TODO also add ip of node!
    #TODO what happens if same utxo same transaction id. Is it exploitable. If in the same block two transactions same id same utxo!
    def __init__(self, id = 0, ip = '127.0.0.1', port = "5000", peers = {}, wallet = None, chain = dict()):
        # id is the same as port for simplicity
        self.id = id
        self.ip = ip
        self.port = port
        self.wallet = Wallet(**wallet) if wallet else self.create_wallet()
        self.blockchain = blockchain(**chain)
        self.peers = peers
        self.ip = f'http://localhost:{port}'

    def get_dict(self):
        return {
            "id": self.id,
            "ip": self.ip,
            "port": self.port,
            "wallet": self.wallet.get_dict(),
            "chain": self.blockchain.get_dict(),
            "peers": self.peers,
        }
    
    def genesis_utxos(self, entry_coins = 100):
        #this method will only be used ONCE for the bootstrap node...
        #Simply put, it will make N utxos, one for each node...
        #and put them to the wallet of the bootstrap node
        for _ in range(N):
            #create utxos for each node for the bootstrap wallet...
            self.wallet.add_utxo(utxo(id = str(uuid4().hex), tx_id='init', address=self.wallet.public_key, amount=100))

    def genesis_block(self):
        raise NotImplemented
    
    def register_peer(self, node_id, ip, port, address):
        self.peers[node_id] = {'ip': ip, 'port': port, 'address': address}

    def create_transaction(self, receiver_address, amount):
        #Check if amount is possible, get the utxos needed for transaction_input
        #but not remove them from the wallet!!! (we don't know if it is confimed yet!)
        # Find utxos to use as input transactions
        input_txns = []
        total_amount = 0
        for personal_utxo in self.wallet.utxos[self.wallet.public_key].values(): #access personal utxos 
            #first check if given transaction is spent already ...
            if personal_utxo.id in self.wallet.spent:
                continue #if it is simply continue with the others...
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
        # Create a new transaction using the transaction class
        tx = transaction(transaction_id = transaction_id, sender_address=self.wallet.public_key, receiver_address=receiver_address, 
                        amount=amount, transaction_input=input_txns, transaction_output=output_txns, expect_dict=False)
        #add all the transaction_input ids to the spent dictionary (could be removed if something happens ?!)
        for to_be_spent in input_txns:
            self.wallet.track_spent(to_be_spent.id, transaction_id=transaction_id) #add to spent... doesn't mean it will be though...
        # Sign the transaction using the sender node's private key
        signature = tx.sign_transaction(self.wallet.private_key)
        # Return the transaction and its signature as a tuple
        return tx, signature
    
    def broadcast_transaction():
        raise NotImplemented
    
    def validate_transaction(self, tx: transaction, signature: str)->bool:
        '''
            True, if transaction valid, else False.
        '''
        #verify signature, then check if funds are available!
        #verify signature
        if not tx.verify_transaction(signature):
            #not valid signature
            return False
        #verify utxos
        #check if sender address exists!
        sender_address = tx.sender_address
        receiver_address = tx.receiver_address
        if sender_address not in self.wallet.utxos:
            return False
        #check if receiver address exists
        if receiver_address not in self.wallet.utxos:
            return False
        actual_amount = 0
        for sender_utxo in tx.transaction_input:
            #for every alleged sender_utxo, check if it exists...
            actual_utxo = self.wallet[sender_address].get(sender_utxo.id, False)
            if not actual_utxo: #utxo doesn't exist
                return False
            #check if the same utxo
            if not (sender_utxo == actual_utxo):
                return False
            #check if spent in another transaction!
            if sender_utxo.id in self.wallet.spent:
                if self.wallet.spent[sender_utxo.id] != tx.transaction_id:
                    return False #if it is spent in a different transaction than this...
            #to check if valid in economy
            actual_amount += sender_utxo.amount
        #check transaction_output if valid...
        change = actual_amount - tx.amount
        if change < 0:
            return False #not enough funds
        elif change == 0:
            #must have only one utxo to the receiver with the amount!
            if (len(tx.transaction_output) != 1) or \
                    (tx.transaction_output[0].address != receiver_address) or (tx.transaction_output[0].amount != actual_amount):
                return False
        else:
            #most typical case, 2 utxos... one for receiver, other for sender with change
            if len(tx.transaction_output) > 2: #more than 2 utxos return False
                return False
            if tx.transaction_output[0].address == sender_address:
                #in this case first is the sender utxo, with change and the other the receiver with amount.
                if (tx.transaction_output[1].address != receiver_address) or \
                    (tx.transaction_output[1].amount != tx.amount) or (tx.transaction_output[0].amount != change):
                    return False
            elif tx.transaction_output[0].address == receiver_address:
                #in this case first is the receiver utxo, with amount and the other the receiver with spare.
                if (tx.transaction_output[1].address != sender_address) or \
                    (tx.transaction_output[1].amount != change) or (tx.transaction_output[0].amount != tx.amount):
                    return False
            else:
                return False
        return True #all checks passed!

    def create_new_block(self): #init block
        #a new block is created with the appropriate index, and previous block hash...
        #starts as empty!
        if len(self.blockchain) > 0:
            last = self.blockchain.last_block() #access last block in the chain...
            return block(self, index = last.index + 1, previous_block_hash = last.hash()) #empty block, nonce = 0
        else:
            #only when block is genesis!!!
            return block()
    
    def validate_block(self, bl: block):
        '''
            Checks if a given block is valid to add to the chain!
        '''
        if len(bl) != CAPACITY:
            return False #doesn't have the appropriate capacity
        if self.blockchain[-1].index + 1 != bl.index:
            return False #not the next in line for the chain!
        if self.blockchain[-1].hash != bl.previous_block_hash:
            return False #not the next in line for the chain!
        #check if valid proof
        if bl.hash()[:MINING_DIFFICULTY] != "0"*MINING_DIFFICULTY:
            return False #not mined!
        #check if each transaction is valid...
        #also check if two transactions have the same id. This should be wrong especially in the block!
        used_txns = set()
        for tx_dict in bl:
            tx = tx_dict['transaction']
            if tx.id in used_txns:
                return False #wrong to have two transactions with the same id...
            used_txns.add(tx.id) #add transaction to the set...
            if not self.validate_transaction(tx, tx_dict['signature']):
                return False #transaction was invalidated so block is cancelled!
        return True #all checks passed!
    
    def broadcast_block():
        raise NotImplemented

    def validate_chain(self, chain: blockchain): #newcomers only...
        #check if wallet is empty (it should be because newcomer!)
        if self.wallet:
            #since nonempty, raise
            raise ValueError("Not a newcomer!")
        #now the way to validate the chain is to validate each block and update the history!
        #therefore it must gain the knowledge of the other wallets! (utxo possesions etc...)
        genesis = True
        for bl in chain:
            if not genesis:
                #validate all other blocks!
                if not self.validate_block(bl):
                    return False
            else:
                genesis = False #only one genesis block
            self.wallet.update(bl) #will update wallet
        return True #if returns True, then chain is validated, wallet up to date...
    
    def broadcast_chain():
        raise NotImplemented

    def resolve_conflict():
        raise NotImplemented #will use something else than validate chain! (probably)

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
                return bl, True #we mined successfuly!
            bl.update_nonce() #mine 
        return bl, False #false denotes not mined!

if __name__=="__main__":
    from json import dumps

    bootstrap = node()

    bootstrap.genesis_utxos()

    print(bootstrap.wallet.spent)

    tx, signature = bootstrap.create_transaction('22122e2', 11)

    bl1 = bootstrap.create_new_block()

    bl1.append(tx, signature)

    #print(bootstrap.wallet.spent)

    print(bl1.get_dict())