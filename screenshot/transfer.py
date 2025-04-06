import re
import os
import json
import mysql.connector
from mysql.connector import Error
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

host = os.getenv("HOST")
user = os.getenv("USER")
password = os.getenv("PASSWORD")
database = os.getenv("DATABASE")

DB_CONFIG = {"host": host, "user": user, "password": password, "database": database}


def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        return None
    return None


@app.route("/balance", methods=["POST"])
def get_balance():
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"valid": False, "error": "Invalid JSON data"}), 400
        address = data.get("address", "")
    except Exception as e:
        return jsonify({"valid": False, "error": "Failed to parse request data"}), 400

    if not address:
        return jsonify({"valid": False, "error": "Address is required"}), 400

    connection = get_db_connection()
    if not connection:
        return jsonify({"valid": False, "error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        query = "SELECT balance FROM token WHERE accNo = %s"
        cursor.execute(query, (address,))
        result = cursor.fetchone()

        if result:
            balance = result[0]
            return jsonify({"valid": True, "balance": balance})
        else:
            query = "INSERT INTO token (accNo, balance) VALUES (%s, %s)"
            cursor.execute(query, (address, 0))
            connection.commit()
            return jsonify({"valid": True, "balance": 0})

    except Error as e:
        if e.errno == 1062:
            return jsonify({"valid": False, "error": "Account already exists"}), 409
        return jsonify({"valid": False, "error": str(e)}), 500
    except Exception as e:
        return jsonify({"valid": False, "error": f"Unexpected error: {str(e)}"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route("/addToBalance", methods=["POST"])
def add_balance():
    data = request.get_json()
    address = data.get("address", "")
    points = data.get("points", 0)

    if not address:
        return jsonify({"valid": False, "error": "Address is required"}), 400
    if not isinstance(points, (int, float)):
        return jsonify({"valid": False, "error": "Points must be a number"}), 400

    connection = get_db_connection()
    if not connection:
        return jsonify({"valid": False, "error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT balance FROM token WHERE accNo = %s", (address,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"valid": False, "error": "Account not found"}), 404

        current_balance = result[0]
        new_balance = current_balance + points

        cursor.execute(
            "UPDATE token SET balance = %s WHERE accNo = %s", (new_balance, address)
        )
        connection.commit()

        return jsonify({"valid": True, "balance": new_balance})
    except Error as e:
        return jsonify({"valid": False, "error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


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


@app.route("/walletTransfer", methods=["POST"])
def walletTransfer():
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
            print(f"Transaction failed. Receipt: {receipt_tx}")
            return jsonify({"valid": False, "message": "Unsuccessful Transaction"})
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE token SET balance = %s WHERE accNo = %s", (0, recipient_address)
        )
        connection.commit()
        return jsonify({"valid": True, "message": "Successfully sent"})
    except Exception as e:
        print(f"Error in /transfer: {str(e)}")
        return jsonify({"valid": False, "message": f"Server error: {str(e)}"}), 500


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
    connection = get_db_connection()
    if connection:
        print(f"Connected to MySQL Server version {connection.get_server_info()}")
        connection.close()
    app.run(debug=True, host="0.0.0.0", port=5000)
