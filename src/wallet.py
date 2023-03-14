from utxo import utxo

class Wallet:
    def __init__(self, public_key = None , private_key = None, utxos = dict(), spent = dict()):
        self.public_key = public_key
        self.private_key = private_key
        self.utxos = dict()
        self.spent = spent
        if utxos: #unpacking dictionary (utxo_dict -> utxo_obj)
            for address, a_utxos in utxos.items():
                self.utxos[address] = {} #a_utxos is a dict of {utxo_id, utxo_dict}
                for utxo_id, utxo_dict in a_utxos.items():
                    utxo_obj = utxo(**utxo_dict) #construct the utxo !
                    self.utxos[address][utxo_id] = utxo_obj

    def __getitem__(self, address: str):
        #get list of utxos that are of a user
        return self.utxos[address]
    
    def get_balance(self):
        # calculate balance based on personal UTXOs...
        ret = 0
        for personal_utxo in self.utxos[self.public_key].values():
            ret += personal_utxo.amount
        return ret

    def add_utxo(self, utxo_obj: utxo):
        #uses utxo id for lookup table
        if utxo_obj.address not in self.utxos:
            self.utxos[utxo_obj.address] = {}
        self.utxos[utxo_obj.address][utxo_obj.id] = utxo_obj

    def remove_utxo(self, utxo_obj: utxo):
        #deletes utxo from ledger using its id.
        del self.utxos[utxo_obj.address][utxo_obj.id]

    def track_spent(self, utxo_id, transaction_id):
        self.spent[utxo_id] = transaction_id

    def untrack_spent(self, utxo_id):
        del self.spent[utxo_id]

    def get_dict(self):
        #return dict representation of ledger!
        result_dict = dict()
        result_dict['utxos'] = dict()
        for address, a_utxos in self.utxos.items():
            result_dict['utxos'][address] = {utxo_id:utxo_obj.get_dict() for utxo_id, utxo_obj in a_utxos.items()}
        result_dict['public_key'] = self.public_key
        result_dict['private_key'] = self.private_key
        result_dict['spent'] = self.spent
        return result_dict
    
    def update(self, block):
        # Remove spent utxos and add new utxos from block transactions
        for transaction_dict in block.transactions:
            transaction = transaction_dict['transaction']
            for tx_input in transaction.transaction_input:
                #remove the utxo and remove it being spent
                self.untrack_spent(tx_input.id)
                self.remove_utxo(tx_input)
            for tx_output in transaction.transaction_output:
                self.add_utxo(tx_output)

    def rollback(self, block):
        #Goes back a block transformation.
        #the exact opposite of update!
        raise NotImplemented

