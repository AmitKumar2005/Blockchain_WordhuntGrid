import re
import os
import json
import mysql.connector
from mysql.connector import Error
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from solcx import compile_standard, install_solc
from web3 import Web3
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

install_solc("0.8.20")

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5500"], supports_credentials=True)

Alchemy_URL = "https://eth-sepolia.g.alchemy.com/v2/pNASGYMf60h1z4fJpVgbgh_FMzO2iYoe"
w3 = Web3(Web3.HTTPProvider(Alchemy_URL))
logger.info(f"Connected to Web3: {w3.is_connected()}")

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
NODE_MODULES_PATH = os.path.join(BASE_PATH, "node_modules")
logger.info(f"Base path: {BASE_PATH}")
logger.info(f"Node modules path: {NODE_MODULES_PATH}")
logger.info(
    f"OpenZeppelin exists: {os.path.exists(os.path.join(NODE_MODULES_PATH, '@openzeppelin', 'contracts'))}"
)

try:
    with open("contract.sol", "r") as file:
        content = file.read()
except FileNotFoundError as e:
    logger.error(f"Failed to read contract.sol: {e}")
    raise

try:
    compile_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {"contract.sol": {"content": content}},
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": [
                            "abi",
                            "metadata",
                            "evm.bytecode",
                            "evm.bytecode.sourceMap",
                        ]
                    }
                },
                "remappings": [
                    "@openzeppelin/contracts/=node_modules/@openzeppelin/contracts/"
                ],
            },
        },
        solc_version="0.8.20",
        base_path=BASE_PATH,
    )
    logger.info("Contract compilation successful")
except Exception as e:
    logger.error(f"Compilation failed: {e}")
    raise

try:
    with open("package.json", "w") as file:
        json.dump(compile_sol, file)
except IOError as e:
    logger.error(f"Failed to write package.json: {e}")
    raise

my_address = os.getenv("MY_ADDRESS")
private_key = os.getenv("PRIVATE_KEY")
if not my_address or not private_key:
    logger.error("MY_ADDRESS or PRIVATE_KEY not set in .env")
    raise ValueError("MY_ADDRESS or PRIVATE_KEY not set in .env")
my_address = w3.to_checksum_address(my_address)
chain_id = 11155111

nft_bytecode = compile_sol["contracts"]["contract.sol"]["WordHuntNFT"]["evm"][
    "bytecode"
]["object"]
nft_abi = compile_sol["contracts"]["contract.sol"]["WordHuntNFT"]["abi"]
nft_contract = w3.eth.contract(bytecode=nft_bytecode, abi=nft_abi)

nonce = w3.eth.get_transaction_count(my_address)
logger.info(f"Nonce for {my_address}: {nonce}")

nft_trans = nft_contract.constructor().build_transaction(
    {
        "from": my_address,
        "nonce": nonce,
        "chainId": chain_id,
        # "gas": 2000000,
        # "gasPrice": w3.to_wei("50", "gwei"),
    }
)
sign_nft_trans = w3.eth.account.sign_transaction(nft_trans, private_key=private_key)
send_nft_trans = w3.eth.send_raw_transaction(sign_nft_trans.raw_transaction)
logger.info(f"WordHuntNFT transaction sent: {send_nft_trans.hex()}")
receipt_nft_trans = w3.eth.wait_for_transaction_receipt(send_nft_trans)
logger.info(f"WordHuntNFT deployed at: {receipt_nft_trans.contractAddress}")
nft_address = receipt_nft_trans.contractAddress
new_nft_contract = w3.eth.contract(address=nft_address, abi=nft_abi)

bytecode = compile_sol["contracts"]["contract.sol"]["transfer"]["evm"]["bytecode"][
    "object"
]
abi = compile_sol["contracts"]["contract.sol"]["transfer"]["abi"]
nonce += 1
contract = w3.eth.contract(bytecode=bytecode, abi=abi)
trans = contract.constructor(nft_address).build_transaction(
    {
        "from": my_address,
        "nonce": nonce,
        "chainId": chain_id,
        # "gas": 2000000,
        # "gasPrice": w3.to_wei("50", "gwei"),
    }
)
sign_trans = w3.eth.account.sign_transaction(trans, private_key=private_key)
send_trans = w3.eth.send_raw_transaction(sign_trans.raw_transaction)
logger.info(f"Transfer contract transaction sent: {send_trans.hex()}")
receipt_trans = w3.eth.wait_for_transaction_receipt(send_trans)
logger.info(f"Transfer contract deployed at: {receipt_trans.contractAddress}")
cont_add = receipt_trans.contractAddress
new_cont = w3.eth.contract(address=cont_add, abi=abi)


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
        logger.error(f"Database connection failed: {e}")
        return None
    return None


@app.route("/balance", methods=["POST"])
def get_balance():
    try:
        data = request.get_json()
        address = data.get("address", "")
        if not address:
            return jsonify({"valid": False, "error": "Address is required"}), 400
        connection = get_db_connection()
        if not connection:
            return jsonify({"valid": False, "error": "Database connection failed"}), 500
        cursor = connection.cursor()
        cursor.execute("SELECT balance FROM token WHERE accNo = %s", (address,))
        result = cursor.fetchone()
        if result:
            balance = result[0]
            return jsonify({"valid": True, "balance": balance})
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
    data = request.get_json()
    address = data.get("address", "")
    points = data.get("points", 0)
    if not address:
        return jsonify({"valid": False, "error": "Address is required"}), 400
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
    except Exception as e:
        logger.error(f"Error in /addToBalance: {e}")
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
        total_amount = new_cont.functions.fund(points).call()
        tx = {
            "from": my_address,
            "to": w3.to_checksum_address(recipient_address),
            "value": total_amount,
            "nonce": nonce,
            "chainId": chain_id,
            # "gas": 1000000,
            # "gasPrice": w3.to_wei("20", "gwei")
        }
        sign_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        send_tx = w3.eth.send_raw_transaction(sign_tx.raw_transaction)
        receipt_tx = w3.eth.wait_for_transaction_receipt(send_tx)
        if receipt_tx.status == 0:
            return jsonify({"valid": False, "message": "Unsuccessful Transaction"})
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE token SET balance = %s WHERE accNo = %s", (0, recipient_address)
        )
        connection.commit()
        return jsonify({"valid": True, "message": "Successfully sent"})
    except Exception as e:
        logger.error(f"Error in /walletTransfer: {e}")
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
        total_amount = new_cont.functions.fund(points).call()
        tx = {
            "from": my_address,
            "to": w3.to_checksum_address(recipient_address),
            "value": total_amount,
            "nonce": nonce,
            "chainId": chain_id,
            "gas": 1000000,
            "gasPrice": w3.to_wei("20", "gwei"),
        }
        sign_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        send_tx = w3.eth.send_raw_transaction(sign_tx.raw_transaction)
        receipt_tx = w3.eth.wait_for_transaction_receipt(send_tx)
        if receipt_tx.status == 0:
            return jsonify({"valid": False, "message": "Unsuccessful Transaction"})

        if points == 10:
            token_uri = f"https://ipfs.io/ipfs/QmMockHash/{recipient_address}/{points}"
            nft_tx = new_cont.functions.awardNFT(
                recipient_address, token_uri
            ).build_transaction(
                {
                    "from": my_address,
                    "nonce": nonce + 1,
                    "chainId": chain_id,
                    "gas": 1000000,
                    "gasPrice": w3.to_wei("20", "gwei"),
                }
            )
            sign_nft_tx = w3.eth.account.sign_transaction(
                nft_tx, private_key=private_key
            )
            send_nft_tx = w3.eth.send_raw_transaction(sign_nft_tx.raw_transaction)
            w3.eth.wait_for_transaction_receipt(send_nft_tx)

        return jsonify({"valid": True, "message": "Successfully sent"})
    except Exception as e:
        logger.error(f"Error in /transfer: {e}")
        return jsonify({"valid": False, "message": f"Server error: {str(e)}"}), 500


if __name__ == "__main__":
    connection = get_db_connection()
    if connection:
        logger.info(f"Connected to MySQL Server version {connection.get_server_info()}")
        connection.close()
    app.run(debug=True, host="0.0.0.0", port=5000)
