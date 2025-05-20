import re
import os
import json
import mysql.connector
from mysql.connector import Error
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from web3 import Web3
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(
    app,
    origins=["https://blockchain-wordhuntgrid.onrender.com", "http://localhost:3000"],
    supports_credentials=True,
)

ALCHEMY_URL = os.getenv("ALCHEMY_URL")
w3 = None
if ALCHEMY_URL:
    w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
    logger.info(f"Connected to Web3: {w3.is_connected()}")
else:
    logger.error("ALCHEMY_URL not set")
    raise ValueError("ALCHEMY_URL not set")

# Load contract data
try:
    with open("contract_data.json", "r") as file:
        contract_data = json.load(file)
    nft_abi = contract_data["WordHuntNFT"]["abi"]
    transfer_abi = contract_data["transfer"]["abi"]
    logger.info("Loaded ABIs from contract_data.json")
except FileNotFoundError as e:
    logger.error(f"Failed to load contract_data.json: {e}")
    raise
except KeyError as e:
    logger.error(f"Invalid contract_data.json structure: {e}")
    raise

my_address = os.getenv("MY_ADDRESS")
private_key = os.getenv("PRIVATE_KEY")
nft_address = os.getenv("NFT_CONTRACT_ADDRESS")
transfer_address = os.getenv("TRANSFER_CONTRACT_ADDRESS")
if not all([my_address, private_key, nft_address, transfer_address]):
    logger.error("Missing required environment variables")
    raise ValueError(
        "MY_ADDRESS, PRIVATE_KEY, NFT_CONTRACT_ADDRESS, or TRANSFER_CONTRACT_ADDRESS not set"
    )

my_address = w3.to_checksum_address(my_address)
nft_address = w3.to_checksum_address(nft_address)
transfer_address = w3.to_checksum_address(transfer_address)
chain_id = 11155111  # Sepolia

# Initialize contracts
nft_contract = w3.eth.contract(address=nft_address, abi=nft_abi)
transfer_contract = w3.eth.contract(address=transfer_address, abi=transfer_abi)
logger.info(f"NFT contract initialized at: {nft_address}")
logger.info(f"Transfer contract initialized at: {transfer_address}")

DB_CONFIG = {
    "host": os.getenv("HOST"),
    "user": os.getenv("USER"),
    "password": os.getenv("PASSWORD"),
    "database": os.getenv("DATABASE"),
    "port": 4000,
}


def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            logger.info("Connected to MySQL database")
            return connection
        logger.error("MySQL connection established but not connected")
        return None
    except Error as e:
        logger.error(f"Database connection failed: {e}")
        return None


# Test database connection on startup
try:
    connection = get_db_connection()
    if connection:
        logger.info("Database connection successful on startup")
        connection.close()
    else:
        logger.error("Database connection failed on startup")
except Exception as e:
    logger.error(f"Database startup check failed: {e}")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)


@app.route("/api", methods=["GET"])
def api_index():
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
    connection = None
    try:
        data = request.get_json()
        logger.info(f"/balance request: {data}")
        address = data.get("address", "")
        if not address or not is_valid_ethereum_address(address):
            logger.error(f"Invalid Ethereum address: {address}")
            return jsonify({"valid": False, "error": "Invalid Ethereum address"}), 400
        connection = get_db_connection()
        if not connection:
            logger.error("DB connection failed")
            return jsonify({"valid": False, "error": "Database connection failed"}), 500
        cursor = connection.cursor()
        cursor.execute("SELECT balance FROM token WHERE accNo = %s", (address,))
        result = cursor.fetchone()
        if result:
            balance = result[0]
            logger.info(f"Balance for {address}: {balance}")
            return jsonify({"valid": True, "balance": balance})
        logger.info(f"No balance for {address}, inserting 0")
        cursor.execute(
            "INSERT INTO token (accNo, balance) VALUES (%s, %s)", (address, 0)
        )
        connection.commit()
        return jsonify({"valid": True, "balance": 0})
    except Exception as e:
        logger.error(f"Error in /balance: {e}", exc_info=True)
        return jsonify({"valid": False, "error": str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route("/addToBalance", methods=["POST"])
def add_balance():
    connection = None
    try:
        data = request.get_json()
        logger.info(f"/addToBalance request: {data}")
        address = data.get("address", "")
        points = data.get("points", 0)
        if not address or not is_valid_ethereum_address(address):
            logger.error(f"Invalid Ethereum address: {address}")
            return jsonify({"valid": False, "error": "Invalid Ethereum address"}), 400
        if not isinstance(points, int) or points < 0:
            logger.error(f"Invalid points: {points}")
            return (
                jsonify(
                    {"valid": False, "error": "Points must be a non-negative integer"}
                ),
                400,
            )
        connection = get_db_connection()
        if not connection:
            logger.error("DB connection failed")
            return jsonify({"valid": False, "error": "Database connection failed"}), 500
        cursor = connection.cursor()
        cursor.execute("SELECT balance FROM token WHERE accNo = %s", (address,))
        result = cursor.fetchone()
        if not result:
            logger.info(f"No balance for {address}, inserting {points}")
            cursor.execute(
                "INSERT INTO token (accNo, balance) VALUES (%s, %s)", (address, points)
            )
            connection.commit()
            return jsonify({"valid": True, "balance": points})
        current_balance = result[0]
        new_balance = current_balance + points
        cursor.execute(
            "UPDATE token SET balance = %s WHERE accNo = %s", (new_balance, address)
        )
        connection.commit()
        logger.info(f"Updated balance for {address}: {new_balance}")
        return jsonify({"valid": True, "balance": new_balance})
    except Exception as e:
        logger.error(f"Error in /addToBalance: {e}", exc_info=True)
        return jsonify({"valid": False, "error": str(e)}), 500
    finally:
        if connection and connection.is_connected():
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
def verify_address():
    try:
        data = request.get_json()
        logger.info(f"/verifyAddress request: {data}")
        address = data.get("address", "")
        if not is_valid_ethereum_address(address):
            logger.error(f"Invalid Ethereum address: {address}")
            return jsonify({"valid": False, "message": "Invalid Ethereum address"}), 400
        logger.info(f"Valid Ethereum address: {address}")
        return jsonify({"valid": True, "message": "Connected"})
    except Exception as e:
        logger.error(f"Error in /verifyAddress: {e}", exc_info=True)
        return jsonify({"valid": False, "message": str(e)}), 500


@app.route("/walletTransfer", methods=["POST"])
def wallet_transfer():
    connection = None
    try:
        data = request.get_json()
        logger.info(f"/walletTransfer request: {data}")
        points = data.get("points", 0)
        recipient_address = data.get("address", "")
        if not is_valid_ethereum_address(recipient_address):
            logger.error(f"Invalid recipient address: {recipient_address}")
            return jsonify({"valid": False, "message": "Invalid Ethereum address"}), 400
        if not isinstance(points, int) or points <= 0:
            logger.error(f"Invalid points: {points}")
            return (
                jsonify(
                    {"valid": False, "message": "Points must be a positive integer"}
                ),
                400,
            )
        nonce = w3.eth.get_transaction_count(my_address)
        total_amount = transfer_contract.functions.fund(points).call()
        logger.info(f"Fund amount for {points} points: {total_amount}")
        tx = {
            "from": my_address,
            "to": w3.to_checksum_address(recipient_address),
            "value": total_amount,
            "nonce": nonce,
            "chainId": chain_id,
            "gas": 1000000,
            "gasPrice": w3.to_wei("20", "gwei"),
        }
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logger.info(f"Transaction sent: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 0:
            logger.error("Transaction failed")
            return jsonify({"valid": False, "message": "Transaction failed"}), 500
        connection = get_db_connection()
        if not connection:
            logger.error("DB connection failed")
            return jsonify({"valid": False, "error": "Database connection failed"}), 500
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE token SET balance = %s WHERE accNo = %s", (0, recipient_address)
        )
        connection.commit()
        logger.info(f"Reset balance to 0 for {recipient_address}")
        return jsonify({"valid": True, "message": "Successfully sent"})
    except Exception as e:
        logger.error(f"Error in /walletTransfer: {e}", exc_info=True)
        return jsonify({"valid": False, "message": str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route("/transfer", methods=["POST"])
def transfer():
    try:
        data = request.get_json()
        logger.info(f"/transfer request: {data}")
        points = data.get("points", 0)
        recipient_address = data.get("address", "")
        if not is_valid_ethereum_address(recipient_address):
            logger.error(f"Invalid recipient address: {recipient_address}")
            return jsonify({"valid": False, "message": "Invalid Ethereum address"}), 400
        if not isinstance(points, int) or points <= 0:
            logger.error(f"Invalid points: {points}")
            return (
                jsonify(
                    {"valid": False, "message": "Points must be a positive integer"}
                ),
                400,
            )
        nonce = w3.eth.get_transaction_count(my_address)
        total_amount = transfer_contract.functions.fund(points).call()
        logger.info(f"Fund amount for {points} points: {total_amount}")
        tx = {
            "from": my_address,
            "to": w3.to_checksum_address(recipient_address),
            "value": total_amount,
            "nonce": nonce,
            "chainId": chain_id,
            "gas": 1000000,
            "gasPrice": w3.to_wei("20", "gwei"),
        }
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logger.info(f"Transaction sent: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 0:
            logger.error("Transaction failed")
            return jsonify({"valid": False, "message": "Transaction failed"}), 500
        if points == 10:
            token_uri = f"https://ipfs.io/ipfs/QmMockHash/{recipient_address}/{points}"
            logger.info(
                f"Awarding NFT to {recipient_address} with tokenURI: {token_uri}"
            )
            nft_tx = nft_contract.functions.awardNFT(
                w3.to_checksum_address(recipient_address), token_uri
            ).build_transaction(
                {
                    "from": my_address,
                    "nonce": nonce + 1,
                    "chainId": chain_id,
                    "gas": 1000000,
                    "gasPrice": w3.to_wei("20", "gwei"),
                }
            )
            signed_nft_tx = w3.eth.account.sign_transaction(
                nft_tx, private_key=private_key
            )
            nft_tx_hash = w3.eth.send_raw_transaction(signed_nft_tx.rawTransaction)
            logger.info(f"NFT transaction sent: {nft_tx_hash.hex()}")
            w3.eth.wait_for_transaction_receipt(nft_tx_hash)
        return jsonify({"valid": True, "message": "Successfully sent"})
    except Exception as e:
        logger.error(f"Error in /transfer: {e}", exc_info=True)
        return jsonify({"valid": False, "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 4000))
    app.run(host="0.0.0.0", port=port, debug=True)
