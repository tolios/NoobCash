import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from node import node
from transaction import transaction
from block import block
from blockchain import blockchain
from utils import create_logger
from argparse import ArgumentParser
from time import sleep

parser = ArgumentParser()
parser.add_argument('--ip', default='127.0.0.1', type=str,
                        help='ip of given node')
parser.add_argument('--port', default=5000, type=int,
                        help='port to listen on')
parser.add_argument('-b', '-bootstrap', action='store_true',
                        help='set if the current node is the bootstrap')
args = parser.parse_args()

#init node 
app_node = node(id = '0' if args.b else None, ip = args.ip, port = args.port, bootstrap=args.b)
app = Flask(__name__)
CORS(app)
logger = create_logger('rest api')

@app.route("/")
def index():
    return app_node.contents()

@app.route("/set_id/<id>", methods=['POST'])
def set_id(id = 0):
    if app_node.id:
        return 'Already set', 500
    app_node.set_id(id)
    sleep(1.)
    logger.info(f'set id to {id}')
    return 'Setted', 200

@app.route("/connect", methods=['POST'])
def register_peer():
    peer_details = request.get_json()
    #set id as #of peer nodes (since 0 is an id it works)
    app_node.register_peer(str(len(app_node.peers)+1), peer_details["ip"], peer_details["port"], peer_details["address"])
    logger.info(f'registering peer with id = {str(len(app_node.peers))}, ip = {peer_details["ip"]}, port = {peer_details["port"]}')
    return 'registered!', 200

@app.route("/broadcast_peers", methods=['POST'])
def broadcast_peers():
    app_node.broadcast_peers()
    logger.info('Broadcasting appropriate peers...')
    return 'Broadcasted peers to everyone', 200

@app.route("/post_peers", methods=['POST'])
def post_peers():
    #this is activated for all other nodes!
    peer_data = request.get_json()
    for peer_id, peer_details in peer_data.items():
        app_node.register_peer(peer_id, peer_details["ip"], peer_details["port"], peer_details["address"])
    logger.info('appropriate peers received!')
    return 'peers received', 200

@app.route("/peers")
def peers():
    return app_node.peers

@app.route("/genesis", methods=['POST'])
def genesis():
    #create genesis block...
    logger.info('Making genesis transactions...')
    g_block = app_node.genesis_block()
    g_block_dict = g_block.get_dict()
    logger.info('Broadcasting genesis block to peers...')
    for peer_details in app_node.peers.values():
        requests.post(f"http://{peer_details['ip']}:{peer_details['port']}/genesis_block", json=g_block_dict)
        sleep(1.)
    #update wallet...
    app_node.wallet.update(g_block)
    #add to blockchain!
    app_node.blockchain.append(g_block)
    logger.info('Updated wallet and blockchain!')
    return 'genesis init', 200

@app.route("/genesis_block", methods = ["POST"])
def genesis_block():
    logger.info('Receiving genesis block...')
    g_block = block(**request.get_json())
    #update wallet...
    app_node.wallet.update(g_block, genesis_ignore=True)
    #add to blockchain!
    app_node.blockchain.append(g_block)
    logger.info('Updated wallet and blockchain!')
    return 'genesis block added...', 200

@app.route("/new_transaction", methods = ["POST"])
def new_transaction():
    # a transaction is registered to the node!
    tx_details = request.get_json() #! will output error if not possible (should have try except)
    address = app_node.peers[tx_details["id"]]["address"]
    tx, signature = app_node.create_transaction(address, tx_details["amount"])
    logger.info(f'New transaction with receiver id {tx_details["id"]}, amount {tx_details["amount"]}')
    #broadcast!
    _, m = app_node.broadcast_transaction(tx, signature)
    if m == 500: 
        return 'failed to broadcast', 500
    logger.info("Appending to pending txns")
    app_node.pending_txns.append({"transaction": tx, "signature": signature}) #pending tx
    #decides if it should call the processing functionality
    # if not app_node.active_processing:
    #     logger.info('Calling processing endpoint!')
    #     #call the processing endpoint! 
    #     requests.post(f'http://{app_node.ip}:{app_node.port}/processing')
    return 'transaction added and broadcasted!!!', 200

@app.route("/receive_transaction", methods = ["POST"])
def receive_transaction():
    logger.info('Receiving transaction...')
    tx_dict = request.get_json()
    tx, signature = transaction(**tx_dict['transaction']), tx_dict['signature']
    # #validate transaction... Will happen later ...
    # if not app_node.validate_transaction(tx, signature):
    #     return 'transaction not valid', 200
    logger.info("Appending to pending txns")
    app_node.pending_txns.append({"transaction": tx, "signature": signature}) #pending tx
    #decides if it should call the processing functionality
    # if not app_node.active_processing:
    #     logger.info('Calling processing endpoint!')
    #     #call the processing endpoint! 
    #     requests.post(f'http://{app_node.ip}:{app_node.port}/processing')
    return 'received transaction!', 200

@app.route("/receive_block", methods = ["POST"])
def receive_block():
    #receive dict and make block
    block_dict = request.get_json()
    received_block = block(**block_dict)
    logger.info('block received ...')
    #add received block in memory
    app_node.received_blocks.append(received_block)
    # #if not processing, it should activate the processing endpoint...
    # if not app_node.active_processing:
    #     logger.info('Calling processing endpoint!')
    #     #call the processing endpoint! 
    #     requests.post(f'http://{app_node.ip}:{app_node.port}/processing')
    return 'received block!', 200

@app.route("/blockchain", methods = ["GET"])
def receive_chain():
    return app_node.blockchain.get_dict(), 200

@app.route("/processing", methods=["POST"])
def processing():
    '''
        If one calls this endpoint is like a switch, 
    if one calls it once, it activates the processing.
    Second time, it will stop...
    '''
    #processing something...
    if not app_node.active_processing:
        app_node.active_processing = True
        logger.info('Processing endpoint called...')
        logger.info('...will start processing')
        app_node.keep_processing()
    else:
        app_node.active_processing = False
        logger.info('Processing endpoint called...')
        logger.info('Stopped processing...')
    return 'done processing...', 200

@app.route("/view")
def view():
    return jsonify(app_node.view_transactions())

@app.route("/balance")
def balance():
    return {"balance": app_node.wallet.get_balance()}

@app.route("/wallet", methods = ["GET"])
def get_wallet():
    return app_node.wallet.get_dict()

if not args.b:
    #all other nodes post on bootstrap...
    details = {"ip": app_node.ip, "port": app_node.port, "address": app_node.wallet.public_key}
    requests.post('http://127.0.0.1:5000/connect', json=details)
else:
    pass

app.run(host = args.ip, port = args.port)