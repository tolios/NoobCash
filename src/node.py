from Crypto.PublicKey import RSA
from uuid import uuid4
from config import MINING_DIFFICULTY, CAPACITY, N
from blockchain import blockchain
from block import block
from transaction import transaction
from wallet import Wallet
from utxo import utxo
import requests
from time import sleep, time
from utils import create_logger

logger = create_logger("node backend")

class node:
    '''
        Node should be thought of as the backend...
    '''
    def __init__(self, id = None, ip = '127.0.0.1', port = "5000", 
                peers = {}, wallet = None, chain = dict(), bootstrap = False, 
                personal_txns = [], pending_txns = [], received_blocks = [], active_processing = False):
        logger.info("initializing ...")
        self.id = id
        self.ip = ip
        self.port = port
        self.wallet = Wallet(**wallet) if wallet else self.create_wallet() 
        self.blockchain = blockchain(**chain)
        self.peers = peers
        self.ip = ip
        self.bootstrap = bootstrap
        self.personal_txns = personal_txns #contains personal tx instructions, will happen after a block is added to the chain! (need utxos)
        self.pending_txns = [{"transaction":transaction(**tx_dict["transaction"]), "signature": tx_dict["signature"]} \
                        for tx_dict in pending_txns] #expects transaction dicts (with signatures!) changes to transaction obj
        self.received_blocks = [block(**block_dict) for block_dict in received_blocks]
        self.active_processing = active_processing

    def set_id(self, id: int):
        self.id = id
    
    def address2id(self, pk: str):
        #uses public key address to find the id
        if pk == self.wallet.public_key:
            return self.id #returns own id
        for peer_id, peer_details in self.peers.items():
            if peer_details["address"] == pk:
                return peer_id
        return -1 #if this happens, something really bad happened!

    def contents(self):
        #used for / endpoint...
        return {
            "id": self.id,
            "ip": self.ip,
            "port": self.port,
            "public_key": self.wallet.public_key,
            "bootstrap": self.bootstrap,
            "personal_txns": self.personal_txns,
            "pending_txns": [{"transaction": tx_dict["transaction"].get_dict(), "signature": tx_dict["signature"]} \
                            for tx_dict in self.pending_txns],
            "received_blocks": [bl.get_dict() for bl in self.received_blocks],
            "active_processing": self.active_processing
        }
    
    def broadcast_peers(self):
        logger.info("broadcasting peers ...")
        #once all the nodes have connected, simply run...
        for peer_id, peer_details in self.peers.items():
            relevant_peers = self.peers.copy() #get a copy of the dictionary
            relevant_peers[self.id] = {'ip': self.ip, 'port': self.port, 'address': self.wallet.public_key}          
            del relevant_peers[peer_id] #remove id of receiver (the receiver has it...)
            requests.post(f"http://{peer_details['ip']}:{peer_details['port']}/post_peers", json=relevant_peers)
            sleep(0.1)
            requests.post(f"http://{peer_details['ip']}:{peer_details['port']}/set_id/{peer_id}") #set id of node!

    def get_dict(self):
        return {
            "id": self.id,
            "ip": self.ip,
            "port": self.port,
            "wallet": self.wallet.get_dict(),
            "chain": self.blockchain.get_dict(),
            "peers": self.peers,
            "bootstrap": self.bootstrap,
            "personal_txns": self.personal_txns,
            "pending_txns": [{"transaction": tx_dict["transaction"].get_dict(), "signature": tx_dict["signature"]} \
                            for tx_dict in self.pending_txns],
            "received_blocks": [bl.get_dict() for bl in self.received_blocks],
            "active_processing": self.active_processing
        }
    
    def genesis_utxos(self, entry_coins: int = 100):
        #this method will only be used ONCE for the bootstrap node...
        #Simply put, it will make (N-1)*100 utxos, one for each peer...
        #and put them to the wallet of the bootstrap node
        logger.info("Creating genesis utxos ...")
        if not self.bootstrap:
            raise ValueError("Not the bootstrap")
        for i in range(len(self.peers)): 
            #create utxos for each node for the bootstrap wallet...
            if i != (len(self.peers)-1):
                for _ in range(entry_coins):
                    self.wallet.add_utxo(utxo(id = str(uuid4().hex), tx_id='init', address=self.wallet.public_key, amount=1.))
            else:
                # trick for the spare to register bootstraps utxos...
                for _ in range(entry_coins):
                    self.wallet.add_utxo(utxo(id = str(uuid4().hex), tx_id='init', address=self.wallet.public_key, amount=2.))
        return entry_coins

    def genesis_block(self):
        #create utxos... entry_coins per node
        logger.info('Making genesis block...')
        g_block = block(timestamp=int(time()))
        entry_coins = self.genesis_utxos()
        for peer_details in self.peers.values():
            #so as each begins with 100 utxos instead of one utxo of 100, would block if 5 nodes 10 capacity...
            for _ in range(entry_coins):
                g_block.append(*self.create_transaction(peer_details['address'], 1.)) #tuple so *
        return g_block
    
    def register_peer(self, node_id, ip, port, address):
        self.peers[node_id] = {'ip': ip, 'port': port, 'address': address}

    def create_transaction(self, receiver_address, amount):
        #Check if amount is possible, get the utxos needed for transaction_input
        #but not remove them from the wallet!!! (we don't know if it is confimed yet!)
        # Find utxos to use as input transactions
        logger.info("creating transaction ...")
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
            logger.info('not enough funds available...')
            raise ValueError("Not enough funds in wallet to complete transaction")
        #start the transaction!
        transaction_id = str(uuid4().hex)
        output_txns = []
        #get the change for the transaction!
        change = total_amount - amount
        #one utxo for the sender, with the change, if zero, no need to make a utxo!
        if change != 0:
            output_txns.append(utxo(id = str(uuid4().hex), tx_id=transaction_id, address = self.wallet.public_key, amount = change))
        #now create utxo for the receiver!
        output_txns.append(utxo(id = str(uuid4().hex), tx_id=transaction_id, address = receiver_address, amount = amount))
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
    
    def broadcast_transaction(self, tx: transaction, signature: str):
        #this method receives a transaction and its corresponding input,
        #then broadcast it to all peers, by posting to the appropriate endpoints!
        logger.info(f'broadcasting transaction with id {tx.transaction_id}')
        tx_dict = {'transaction': tx.get_dict(), 'signature': signature}
        try:
            for peer_details in self.peers.values():
                #make post
                requests.post(f"http://{peer_details['ip']}:{peer_details['port']}/receive_transaction", json=tx_dict)
            return 'Broadcast succeeded!', 200
        except:
            return 'Broadcast failed...', 500
    
    def personal_transaction(self):
        '''
            This method takes care of personal transactions...
        Will create them if possible, and will broadcast them...

        Return True if done, else ... False
        '''
        #if it has pending personal ...
        if self.personal_txns:
            tx_details = self.personal_txns.pop(0)
            address = self.peers[tx_details["id"]]["address"]
            #first checks if even possible...
            if self.wallet.get_balance() < tx_details["amount"]:
                logger.info('transaction impossible! Ignored...')
                return True #we output true so as to move along. The transaction was just erroneous...
            try:
                tx, signature = self.create_transaction(address, tx_details["amount"])
            except:
                logger.info('transaction not possible...yet (enough funds but utxos are spent)')
                self.personal_txns = [tx_details]+self.personal_txns #keeping it in memory...
                return False
            logger.info(f'Broadcasting tx with receiver id {tx_details["id"]}, amount {tx_details["amount"]}')
            #broadcast!
            self.broadcast_transaction(tx, signature)
            logger.info("Appending to pending txns")
            self.pending_txns.append({"transaction": tx, "signature": signature}) #pending tx
            return True
        return False #no personal txns...
        
    def validate_transaction(self, tx: transaction, signature: str)->bool:
        '''
            True, if transaction valid, else False.
        '''
        logger.info(f'Validating transaction with id {tx.transaction_id}')
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
        #since all checks passed we track the transaction utxos so that it will be satisfied....
        for sender_utxo in tx.transaction_input:
            self.wallet.track_spent(sender_utxo.id, transaction_id=tx.transaction_id)
        return True 
    
    def view_transactions(self):
        #returns all transactions of the last verified block!
        txns = []
        for tx_dict in self.blockchain.last_block():
            tx = tx_dict['transaction'] #we only need the transaction, not the signature
            txns.append(f"{self.address2id(tx.sender_address)} -- {tx.amount} -> {self.address2id(tx.receiver_address)}")
        return txns

    def create_new_block(self): #init block
        #a new block is created with the appropriate index, and previous block hash...
        #starts as empty!
        logger.info('creating new block...')
        if len(self.blockchain) > 0:
            last = self.blockchain.last_block() #access last block in the chain...
            return block(timestamp = int(time()), index = last.index + 1, previous_block_hash = last.hash()) #empty block, nonce = 0
        else:
            raise ValueError('Genesis elsewhere!')
    
    def validate_block(self, bl: block):
        '''
            Checks if a given block is valid to add to the chain!
        '''
        logger.info('validating block ...')
        if len(bl) != CAPACITY:
            return False, 'wrong capacity' #doesn't have the appropriate capacity
        if self.blockchain.last_block().hash() != bl.previous_block_hash:
            return False, 'wrong hash' #not the next in line for the chain!
        if self.blockchain.last_block().index + 1 != bl.index:
            return False, 'wrong index' #not the next in line for the chain!
        #check if valid proof
        if bl.hash()[:MINING_DIFFICULTY] != "0"*MINING_DIFFICULTY:
            return False, 'not mined' #not mined!
        #check if each transaction is valid...
        #also check if two transactions have the same id. This should be wrong especially in the block!
        used_txns = set()
        for num, tx_dict in enumerate(bl):
            tx = tx_dict['transaction']
            if tx.transaction_id in used_txns:
                return False, ('2 same id', num) #wrong to have two transactions with the same id...
            used_txns.add(tx.transaction_id) #add transaction to the set...
            if not self.validate_transaction(tx, tx_dict['signature']):
                return False, ('transaction invalidated', num) #transaction was invalidated so block is cancelled!
        return True, 'passed' #all checks passed! (plus transaction utxos tracked...)
    
    def mine_block(self, bl: block, limit = 1e10):
        '''
            Receives a block, to mine it. Up to a limit... unless it receives a block...
        '''
        logger.info('mining ...')
        for _ in range(int(limit)):
            if len(self.received_blocks) >= 1:
                logger.info('received block, stopping mining...')
                break #break since we have a block received...
            b_hash = bl.hash()
            if b_hash[:MINING_DIFFICULTY] == "0"*MINING_DIFFICULTY:
                logger.info('mined!')
                return bl, True #we mined successfuly!
            bl.update_nonce() #mine 
        return bl, False #false denotes not mined!
    
    def broadcast_block(self, mined_block: block):
        #broadcasts block to all peers...
        block_dict = mined_block.get_dict()
        logger.info('broadcasting block...')
        try:
            for peer_details in self.peers.values():
                #make post
                requests.post(f"http://{peer_details['ip']}:{peer_details['port']}/receive_block", json=block_dict)
            return 'Broadcast succeeded!', 200
        except:
            return 'Broadcast failed...', 500

    def unzipnzip(self, new_chain: blockchain): 
        '''
            Given our new chain, we need to unzip our previous chain,
        then zip the new chain, while tracking all the pending transactions.
        '''
        #first we need to find where the chains splitted!
        split = -1
        logger.info('finding split...')
        for new_block, old_block in zip(new_chain, self.blockchain):
            #we check if the same...
            if new_block.hash() == old_block.hash():
                split += 1
            else:
                break
        logger.info(f'found split at {split}')
        if split == -1:
            logger.info(f'found split at {split}')
            raise ValueError("Erroneous new chain!!!")
        #start reversing, keeping reversed transactions
        logger.info('unzipping...')
        reversed_txns = [] 
        limit = len(self.blockchain) -split -1
        for i, old_block in enumerate(reversed(self.blockchain)):
            if i == limit:
                logger.info('stopped rolling back...')
                break
            else:  #! could have an error...
                #start rolling back transactions
                reversed_txns = self.wallet.rollback(old_block) + reversed_txns
                #pop out block from blockchain...
                self.blockchain.trim()
        #update pending with old... (correct order!)
        logger.info('zip to new...')
        self.pending_txns = reversed_txns + self.pending_txns
        #zip new chain...
        for i, new_block in enumerate(new_chain):
            if i <= split:
                continue #do nothing before we cross the split...
            #update wallet!!!
            try:
                print(self.validate_block(new_block))
                self.wallet.update(new_block)
                self.blockchain.append(new_block)
            except:
                logger.info('error of new block')
            # delete pending txns that are used in the block!!!
            self.update_pending_txns(new_block) #change the pending txns...
        
    def resolve_conflict(self):
        #iterates all peers, picks longest chain!
        max_len, max_chain, max_id = -1, None, -1
        for peer_id in self.peers:
            logger.info('searching chain...')
            chain_dict = requests.get(f'http://127.0.0.1:{5000+int(peer_id)}/blockchain').json()
            new_len = len(chain_dict['blocks'])
            if new_len > max_len:
                max_len, max_chain, max_id = new_len, chain_dict, peer_id
        if max_len <= len(self.blockchain):
            #we have the biggest blockchain...
            logger.info('already has the biggest chain...')
            return None
        logger.info(f'adopting chain of id {max_id}')
        #therefore we have acquired new chain...
        new_chain = blockchain(**max_chain)
        self.unzipnzip(new_chain) #unzip from old and zip to new chain...

    def update_pending_txns(self, successful_block: block):
        #remove the satisfied transactions form the pending tx list!
        logger.info('updating pending transactions...')
        new_pending = []
        for tx_dict in self.pending_txns:
            if not (tx_dict['transaction'].transaction_id in successful_block):
                #add since it is not contained in the successful 
                new_pending.append(tx_dict)
            #else don't do anything!
        logger.info('new pending '+str(len(new_pending)))
        self.pending_txns = new_pending #only the non included!
    
    def cleanup(self, cancelled_txns: list):
        '''
            If a block is cancelled by an invalid transaction inside, we should clean
        all tracked utxos of its contained transactions form the wallet!!!
        '''
        logger.info('cleaning cancelled transactions...')
        #iterate through the transactions of the cancelled block
        for tx_dict in cancelled_txns:
            # for each utxo
            for utxo in tx_dict['transaction'].transaction_input:
                # if we have tracked it to this transaction, untrack!
                if utxo.id in self.wallet.spent:
                    if self.wallet.spent == tx_dict['transaction'].transaction_id:
                        self.wallet.untrack_spent(utxo.id)
    
    def processing(self):
        '''
            This is the main method of a node. This method can be activated many times from api calls.
        It deals with pending transactions, incoming blocks, incoming chains etc. This method is tasked
        with dealing with serving most transactions with all the appropriate steps. 
            When active, it raises a flag, called active_processing = True. This helps so as to know whether
        we need to call or not the processing method while receiving api calls!
        '''
        if self.received_blocks: #block received ...
            logger.info('examining block received ...')
            #assumes clean state ...
            received_block = self.received_blocks.pop(0) #pops it (might have received more than one ?!)
            #validate block...
            valid, reason = self.validate_block(received_block)
            if valid:
                logger.info('block is valid, adding to blockchain and updating wallet...')
                self.blockchain.append(received_block)
                #update wallet!!!
                self.wallet.update(received_block)
                # delete pending txns that are used in the block!!!
                self.update_pending_txns(received_block) #change the pending txns...
                logger.info('removing rest of incoming blocks...(if they exist)')
                #emptying all the rest received blocks...
                self.received_blocks = []
                logger.info('restarting session to deal with other pending txns...')
                return self.processing() #call this again to deal with more of the pending if any left...
            else:
                logger.info('block invalidated!')
                #clean state!!! nothing or chain!
                if (reason[0] == 'transaction invalidated') or (reason[0] == '2 same id'):
                    logger.info('a transaction was invalidated!')
                    num = reason[1] #have been validated...
                    self.cleanup(received_block.transactions[:num])
                    #nothing to do, restart process having removed the received_block validated txns
                    return self.processing()
                elif reason == 'wrong hash':
                    #if we have wrong hash ... need to ask for chain
                    logger.info('wrong hash... asking for longest chain...')
                    self.resolve_conflict() #find longest valid chain... unzipnzip ...
                    return self.processing()
                else:
                    #simply start new processing session! Having removed simply invalid block...
                    logger.info(f'Reason of invalidation: {str(reason)}')
                    logger.info('restarting session to deal with other pending txns...')
                    return self.processing()
        
        #Try to create personal transaction & add to pending_txns ...
        personal = True
        while personal:
            personal = self.personal_transaction()
            if personal:
                logger.info('...')
                
        if len(self.pending_txns) >= CAPACITY: #make block ... if appropriate
            logger.info('start validating pending txns...')
            valid_txns = []
            while len(self.pending_txns)+len(valid_txns) >= CAPACITY:
                '''
                    This loop should run until enough of the pending_txns are dealt with...
                It must deal with incoming transactions, and incoming blocks, and update them all
                coherently. (If a block made or received has dealt with some pending, it should remove them form the list!)
                '''
                if len(self.received_blocks) < 1: #hears for incoming blocks
                    #if non, starts validating txns
                    tx_dict = self.pending_txns.pop(0)
                    if self.validate_transaction(tx_dict['transaction'], tx_dict['signature']):
                        #since validated, add to list!
                        valid_txns.append(tx_dict)
                    else:
                        logger.info('throw out invalid transaction from pending...')
                        del tx_dict #throw out invalid transaction!!!
                else:
                    logger.info('received block while validating txns ...')
                    #since we have tracked from validating, we should remove the tracking!
                    self.cleanup(valid_txns)
                    #get the same pending txns
                    self.pending_txns = valid_txns + self.pending_txns
                    #restart with the received block!
                    logger.info('restarting process to deal with the received block...')
                    return self.processing()
                #time to make new block 
                if len(valid_txns) == CAPACITY:
                    logger.info('making block to mine from validated txns...')
                    #make block!
                    mine_block = self.create_new_block()
                    #start adding one by one...
                    for tx_dict in valid_txns:
                        if len(self.received_blocks) < 1:
                            #add one by one to the block...
                            mine_block.append(tx_dict['transaction'], tx_dict['signature'])
                        else:
                            logger.info('received block, clean state...')
                            #received new block so we need to untrack, 
                            self.cleanup(valid_txns)
                            #get the same pending txns
                            self.pending_txns = valid_txns + self.pending_txns
                            logger.info('restarting process to deal with the received block...')
                            return self.processing()
                    #start mining away...
                    mine_block, mined = self.mine_block(mine_block)
                    #if mined broadcast and add...
                    if mined and (len(self.received_blocks) < 1):
                        #broadcast then add to the chain!!!
                        self.broadcast_block(mine_block)
                        logger.info('adding to blockchain, updating wallet...')
                        self.blockchain.append(mine_block)
                        #throw out all satisfied valid txns...
                        valid_txns = []
                        #update wallet!!!
                        self.wallet.update(mine_block)
                    else:
                        #deal with received block...
                        #since we have tracked from validating, we should remove the tracking!
                        self.cleanup(valid_txns)
                        #get the same pending txns
                        self.pending_txns = valid_txns + self.pending_txns
                        #restart with the received block!
                        logger.info('restarting process to deal with the received block...')
                        return self.processing()
            if valid_txns:
                #not enough valid left to make block...
                self.cleanup(valid_txns)
                #get the same pending txns
                self.pending_txns = valid_txns + self.pending_txns
                #restart with the received block!
                logger.info('restarting process, too few valid...')
                return self.processing()

        #if nothing is done, means we haven't received anything so there is nothing to be done...
        return 0
    
    def keep_processing(self):
        '''
            This method is called once, to activate processing.
        Essentially we loop around the processing method waiting for something
        to do. When we receive anything, processing will take care of it,
        then simply return to do nothing. 

        Loop stops if we set self.active_processing to False...
        '''
        while self.active_processing:
            sleep(0.1) #giving it a small rythm...
            _ = self.processing()
        logger.info('processing stops!')

    @staticmethod
    def create_wallet():
        #create a wallet for this node, with a public key and a private key
        keypair = RSA.generate(2048)
        private_key = keypair.export_key().decode("ISO-8859-1")
        public_key = keypair.publickey().export_key().decode("ISO-8859-1")
        return Wallet(public_key = public_key, private_key = private_key) #starts with no utxos
