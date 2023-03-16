import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from node import node
from transaction import transaction
from block import block
from blockchain import blockchain
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
app_node = node(id = 0 if args.b else None, ip = args.ip, port = args.port, bootstrap=args.b)
app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return app_node.contents()

@app.route("/set_id/<id>", methods=['POST'])
def set_id(id = 0):
    if app_node.id:
        return 'Already set', 500
    app_node.set_id(id)
    return 'Setted', 200

@app.route("/connect", methods=['POST'])
def register_peer():
    peer_details = request.get_json()
    #set id as #of peer nodes (since 0 is an id it works)
    app_node.register_peer(len(app_node.peers)+1, peer_details["ip"], peer_details["port"], peer_details["address"])
    return 'registered!', 200

@app.route("/broadcast_peers", methods=['POST'])
def broadcast_peers():
    app_node.broadcast_peers()
    return 'Broadcasted peers to everyone', 200

@app.route("/post_peers", methods=['POST'])
def post_peers():
    #this is activated for all other nodes!
    peer_data = request.get_json()
    for peer_id, peer_details in peer_data.items():
        app_node.register_peer(peer_id, peer_details["ip"], peer_details["port"], peer_details["address"])
    return 'peers received', 200

@app.route("/peers")
def peers():
    return app_node.peers

#data = request.get_json()

# # Create main method
# def main(host = '', port = 5000):
#     # run the app
#     app.run(host=host, port=port)

#initializations

if not args.b:
    #all other nodes post on bootstrap...
    details = {"ip": app_node.ip, "port": app_node.port, "address": app_node.wallet.public_key}
    requests.post('http://127.0.0.1:5000/connect', json=details)
else:
    pass

app.run(host = args.ip, port = args.port)