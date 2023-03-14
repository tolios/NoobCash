import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.contrib.cache import SimpleCache
from utils import create_logger
from node import Node
from transaction import Transaction
from block import Block
from blockchain import Blockchain

# ------------------------------ Bootstrapping --------------------------------
logger = create_logger('rest')
app = Flask(__name__)
CORS(app)
cache = SimpleCache(default_timeout=0)

# Create to_json method
def to_json(self):
    # create the json
    json = self.__dict__.copy()
    # return the json
    return json

# Create from_json method
def from_json(json):
    # create the object
    obj = self.__class__(**json)
    # return the object
    return obj

# Create get method
@app.route('/get', methods=['GET'])
def get():
    # get the blockchain from the cache
    blockchain = Blockchain.from_json(cache.get('blockchain'))
    # return the blockchain as a json
    return jsonify(blockchain.to_json())

# Create post method 
@app.route('/post', methods=['POST'])
def post():
    # post the blockchain to the cache
    data = request.get_json()
    cache.set('blockchain', data)
    # return the blockchain as a json
    return jsonify(data)

# Create mine method
@app.route('/mine', methods=['GET'])
def mine():
    # get the blockchain from the cache
    blockchain = Blockchain.from_json(cache.get('blockchain'))
    # mine the blockchain
    blockchain.mine()
    # update the cache
    cache.set('blockchain', blockchain.to_json())
    # return the blockchain as a json
    return jsonify(blockchain.to_json())

# Create add transaction method
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    # get the blockchain from the cache
    blockchain = Blockchain.from_json(cache.get('blockchain'))
    # get the transaction from the request
    data = request.get_json()
    transaction = Transaction.from_json(data)
    # add the transaction to the blockchain
    blockchain.add_transaction(transaction)
    # update the cache
    cache.set('blockchain', blockchain.to_json())
    # return the blockchain as a json
    return jsonify(blockchain.to_json())


# Create add node method
@app.route('/add_node', methods=['POST'])
def add_node():
    # get the node from the cache
    node = Node.from_json(cache.get('node'))
    # get the node from the request
    data = request.get_json()
    node = Node.from_json(data)
    # add the node to the blockchain
    blockchain = Blockchain.from_json(cache.get('blockchain'))
    blockchain.add_node(node)
    # update the cache
    cache.set('blockchain', blockchain.to_json())
    # return the blockchain as a json
    return jsonify(blockchain.to_json())

# Create replace chain method
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    # get the blockchain from the cache
    blockchain = Blockchain.from_json(cache.get('blockchain'))
    # replace the chain
    blockchain.replace_chain()
    # update the cache
    cache.set('blockchain', blockchain.to_json())
    # return the blockchain as a json
    return jsonify(blockchain.to_json())

# Create update method
def update():
    # get the blockchain from the cache
    blockchain = Blockchain.from_json(cache.get('blockchain'))
    # update the blockchain
    blockchain.update()
    # update the cache
    cache.set('blockchain', blockchain.to_json())
    # return the blockchain as a json
    return jsonify(blockchain.to_json())

# Create delete method
def delete():
    # delete the blockchain from the cache
    cache.delete('blockchain')
    # return notification
    return jsonify('Blockchain deleted')

# Create run method
def run(host, port, node):
    # add the node to the cache
    cache.set('node', node.to_json())
    # run the app
    app.run(host=host, port=port)

# Create bootstrap method
def bootstrap(host, port, node):
    # add the node to the cache
    cache.set('node', node.to_json())
    # run the app
    app.run(host=host, port=port)

# Create transfer method
def transfer(host, port, node, recipient, amount):
    # add the node to the cache
    cache.set('node', node.to_json())
    # create the transaction
    transaction = Transaction(node.identifier, recipient, amount)
    # create the request
    url = 'http://{}:{}/add_transaction'.format(host, port)
    headers = {'Content-Type': 'application/json'}
    data = transaction.to_json()
    # send the request
    response = requests.post(url, headers=headers, json=data)
    # return the response
    return response

# Create transactions method
def transactions(host, port, node):
    # add the node to the cache
    cache.set('node', node.to_json())
    # create the request
    url = 'http://{}:{}/get'.format(host, port)
    headers = {'Content-Type': 'application/json'}
    # send the request
    response = requests.get(url, headers=headers)
    # return the response
    return response

# Create main method
def main():
    # run the app
    app.run(host='
            
', port=5000)

# Run the main method
if __name__ == '__main__':
    main()



