from Crypto.PublicKey import RSA

class Wallet:
    def __init__(self, public_key: str, private_key: str, transactions: list = []):
        self.public_key = public_key
        self.private_key = private_key
        self.transactions = transactions

    def update_trsansactions(self, new_transactions: list):
        self.transactions = new_transactions
    
    def get_balance(self):
        # calculate balance based on UTXOs
        raise NotImplemented
