import os
import json
import logging
import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS
from web3 import Web3
from dotenv import load_dotenv
from mysql.connector import Error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
CORS(
    app,
    origins=["https://blockchain-wordhuntgrid.onrender.com"],
    supports_credentials=True,
)

ALCHEMY_URL = os.getenv("ALCHEMY_URL")
w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
logger.info(f"Connected to Web3: {w3.is_connected()}")

try:
    with open("contract_data.json", "r") as f:
        contract_info = json.load(f)
    abi = contract_info["abi"]
    bytecode = contract_info["bytecode"]
    logger.info(f"Loaded contract ABI and bytecode for {contract_info['name']}")
except Exception as e:
    logger.error(f"Failed to load contract_data.json: {e}")
    raise

my_address = os.getenv("MY_ADDRESS")
private_key = os.getenv("PRIVATE_KEY")
nft_address = os.getenv("NFT_CONTRACT_ADDRESS")
transfer_address = os.getenv("TRANSFER_CONTRACT_ADDRESS")

if not (my_address and private_key and nft_address and transfer_address):
    raise ValueError(
        "MY_ADDRESS, PRIVATE_KEY, NFT_CONTRACT_ADDRESS, TRANSFER_CONTRACT_ADDRESS must be set"
    )

my_address = w3.to_checksum_address(my_address)
nft_contract = w3.eth.contract(address=w3.to_checksum_address(nft_address), abi=abi)
transfer_contract = w3.eth.contract(
    address=w3.to_checksum_address(transfer_address), abi=abi
)

DB_CONFIG = {
    "host": os.getenv("HOST"),
    "user": os.getenv("USER"),
    "password": os.getenv("PASSWORD"),
    "database": os.getenv("DATABASE"),
}


def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        logger.error(f"Database connection failed: {e}")
    return None


@app.route("/ping")
def ping():
    return jsonify({"status": "ok"}), 200


@app.route("/")
def index():
    return (
        jsonify(
            {
                "message": "Welcome to the WordHuntNFT API",
                "nft_contract_address": nft_address,
                "transfer_contract_address": transfer_address,
            }
        ),
        200,
    )


@app.route("/balance", methods=["POST"])
def get_balance():
    try:
        data = request.get_json()
        address = data.get("address", "")
        if not address:
            return jsonify({"valid": False, "error": "Address is required"}), 400

        connection = get_db_connection()
        if not connection:
            return jsonify({"valid": False, "error": "DB connection failed"}), 500

        cursor = connection.cursor()
        cursor.execute("SELECT balance FROM token WHERE accNo = %s", (address,))
        result = cursor.fetchone()

        if result:
            return jsonify({"valid": True, "balance": result[0]})
        else:
            cursor.execute(
                "INSERT INTO token (accNo, balance) VALUES (%s, %s)", (address, 0)
            )
            connection.commit()
            return jsonify({"valid": True, "balance": 0})
    except Exception as e:
        logger.error(f"Error in /balance: {e}")
        return jsonify({"valid": False, "error": str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route("/addToBalance", methods=["POST"])
def add_balance():
    try:
        data = request.get_json()
        address = data.get("address", "")
        points = data.get("points", 0)

        if not address:
            return jsonify({"valid": False, "error": "Address is required"}), 400

        connection = get_db_connection()
        if not connection:
            return jsonify({"valid": False, "error": "DB connection failed"}), 500

        cursor = connection.cursor()
        cursor.execute("SELECT balance FROM token WHERE accNo = %s", (address,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"valid": False, "error": "Account not found"}), 404

        new_balance = result[0] + points
        cursor.execute(
            "UPDATE token SET balance = %s WHERE accNo = %s", (new_balance, address)
        )
        connection.commit()

        return jsonify({"valid": True, "balance": new_balance})
    except Exception as e:
        logger.error(f"Error in /addToBalance: {e}")
        return jsonify({"valid": False, "error": str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route("/award", methods=["POST"])
def award_completion():
    try:
        data = request.get_json()
        player = w3.to_checksum_address(data["address"])
        points = int(data["points"])
        token_uri = data["tokenURI"]

        nonce = w3.eth.get_transaction_count(my_address)
        txn = transfer_contract.functions.awardCompletion(
            player, points, token_uri
        ).build_transaction(
            {
                "from": my_address,
                "nonce": nonce,
                "gas": 500000,
                "gasPrice": w3.to_wei("20", "gwei"),
            }
        )

        signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return jsonify({"tx_hash": tx_hash.hex()})
    except Exception as e:
        logger.error(f"Error in /award: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/spend", methods=["POST"])
def spend_coins():
    try:
        data = request.get_json()
        player = w3.to_checksum_address(data["address"])
        amount = int(data["amount"])
        item = data["item"]

        nonce = w3.eth.get_transaction_count(my_address)
        txn = transfer_contract.functions.spendCoins(
            player, amount, item
        ).build_transaction(
            {
                "from": my_address,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": w3.to_wei("20", "gwei"),
            }
        )

        signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return jsonify({"tx_hash": tx_hash.hex()})
    except Exception as e:
        logger.error(f"Error in /spend: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/deposit", methods=["POST"])
def deposit():
    try:
        amount = int(request.get_json().get("amount", 0))
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than 0"}), 400

        nonce = w3.eth.get_transaction_count(my_address)
        txn = {
            "from": my_address,
            "to": w3.to_checksum_address(transfer_address),
            "value": amount,
            "gas": 21000,
            "gasPrice": w3.to_wei("20", "gwei"),
            "nonce": nonce,
        }

        signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return jsonify({"tx_hash": tx_hash.hex()})
    except Exception as e:
        logger.error(f"Error in /deposit: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
