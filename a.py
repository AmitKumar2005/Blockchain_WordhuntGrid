import re
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from solcx import compile_standard
from web3 import Web3

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5500"], supports_credentials=True)

Alchemy_URL = "https://eth-sepolia.g.alchemy.com/v2/pNASGYMf60h1z4fJpVgbgh_FMzO2iYoe"
w3 = Web3(Web3.HTTPProvider(Alchemy_URL))

with open("contract.sol", "r") as file:
    content = file.read()

compile_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"contract.sol": {"content": content}},
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]
                }
            }
        },
    },
    solc_version="0.8.0",
)

with open("package.json", "w") as file:
    json.dump(compile_sol, file)

bytecode = compile_sol["contracts"]["contract.sol"]["transfer"]["evm"]["bytecode"][
    "object"
]
abi = compile_sol["contracts"]["contract.sol"]["transfer"]["abi"]

my_address = w3.to_checksum_address(os.getenv("MY_ADDRESS"))
chain_id = 11155111
nonce = w3.eth.get_transaction_count(my_address)
private_key = os.getenv("PRIVATE_KEY")

contract = w3.eth.contract(bytecode=bytecode, abi=abi)
trans = contract.constructor().build_transaction(
    {"from": my_address, "nonce": nonce, "chainId": chain_id}
)
signTrans = w3.eth.account.sign_transaction(trans, private_key=private_key)
sendTrans = w3.eth.send_raw_transaction(signTrans.raw_transaction)
receiptTrans = w3.eth.wait_for_transaction_receipt(sendTrans)
contAdd = receiptTrans.contractAddress
newCont = w3.eth.contract(address=contAdd, abi=abi)


def is_valid_ethereum_address(address):
    if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
        return False
    try:
        w3.to_checksum_address(address)
        return True
    except ValueError:
        return False


@app.route("/verifyAddress", methods=["POST"])
def verifyAddress():
    data = request.get_json()
    address = data.get("address", "")

    if not is_valid_ethereum_address(address):
        return jsonify({"valid": False, "message": "Invalid Ethereum address"})
    return jsonify({"valid": True, "message": "Connected"})


@app.route("/transfer", methods=["POST"])
def transferMoney():
    try:
        data = request.get_json()
        points = data.get("points", 0)
        recipient_address = data.get("address", "")
        if not is_valid_ethereum_address(recipient_address):
            return jsonify(
                {"valid": False, "message": "Invalid recipient Ethereum address"}
            )

        nonce = w3.eth.get_transaction_count(my_address)
        totalAmount = newCont.functions.fund(points).call()
        tx = {
            "from": my_address,
            "to": w3.to_checksum_address(recipient_address),
            "value": totalAmount,
            "nonce": nonce,
            "chainId": chain_id,
            "gas": 2000000,
            "gasPrice": w3.to_wei("50", "gwei"),
        }
        sign_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        send_tx = w3.eth.send_raw_transaction(sign_tx.raw_transaction)
        receipt_tx = w3.eth.wait_for_transaction_receipt(send_tx)
        if receipt_tx.status == 0:
            return jsonify({"valid": False, "message": "Unsuccessful Transaction"})
        return jsonify({"valid": True, "message": "Successfully sent"})
    except Exception as e:
        print(f"Error in /transfer: {str(e)}")
        return jsonify({"valid": False, "message": f"Server error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
