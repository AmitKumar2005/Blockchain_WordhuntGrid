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

app = Flask(__name__, static_folder=".")
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
    logger.info("Serving index.html from root")
    try:
        return send_from_directory(app.static_folder, "index.html")
    except FileNotFoundError:
        logger.error("index.html not found in root")
        return jsonify({"error": "index.html not found"}), 404


@app.route("/<path:path>")
def serve_static(path):
    logger.info(f"Serving file from root: {path}")
    try:
        return send_from_directory(app.static_folder, path)
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        return jsonify({"error": f"File {path} not found"}), 404


@app.route("/debug/static-files", methods=["GET"])
def list_static_files():
    try:
        files = os.listdir(app.static_folder)
        logger.info(f"Root folder contents: {files}")
        return jsonify({"static_files": files})
    except Exception as e:
        logger.error(f"Error listing root files: {e}")
        return jsonify({"error": str(e)}), 500


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
        total_amount = points * 10**15
        logger.info(f"Transfer amount for {points} points: {total_amount}")
        nonce = w3.eth.get_transaction_count(my_address)
        tx = {
            "from": my_address,
            "to": w3.to_checksum_address(recipient_address),
            "value": total_amount,
            "nonce": nonce,
            "chainId": chain_id,
            "gas": 21000,
            "gasPrice": w3.to_wei("20", "gwei"),
        }
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
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
        return jsonify({"valid": True, "message": "Successfully sent Ether"})
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
        if points == 10:
            # Use awardCompletion for points == 10 to transfer Ether and mint NFT
            token_uri = (
                "https://ipfs.io/ipfs/QmActualHash"  # Replace with your IPFS hash
            )
            logger.info(
                f"Calling awardCompletion for {recipient_address} with points: {points}, tokenURI: {token_uri}"
            )
            nonce = w3.eth.get_transaction_count(my_address)
            # Estimate gas
            try:
                gas = transfer_contract.functions.awardCompletion(
                    w3.to_checksum_address(recipient_address), points, token_uri
                ).estimate_gas({"from": my_address})
            except Exception as gas_error:
                logger.error(f"Gas estimation failed: {gas_error}")
                return (
                    jsonify(
                        {
                            "valid": False,
                            "message": f"Gas estimation failed: {str(gas_error)}",
                        }
                    ),
                    500,
                )
            tx = transfer_contract.functions.awardCompletion(
                w3.to_checksum_address(recipient_address), points, token_uri
            ).build_transaction(
                {
                    "from": my_address,
                    "nonce": nonce,
                    "chainId": chain_id,
                    "gas": gas + 10000,
                    "gasPrice": w3.to_wei("20", "gwei"),
                }
            )
            signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 0:
                # Try to fetch revert reason
                try:
                    w3.eth.call(
                        {
                            "from": my_address,
                            "to": transfer_address,
                            "data": transfer_contract.encodeABI(
                                fn_name="awardCompletion",
                                args=[
                                    w3.to_checksum_address(recipient_address),
                                    points,
                                    token_uri,
                                ],
                            ),
                        },
                        block_identifier=receipt.blockNumber,
                    )
                except Exception as revert_error:
                    revert_reason = str(revert_error)
                    logger.error(
                        f"Transaction failed with revert reason: {revert_reason}"
                    )
                    # Fallback: Try direct Ether transfer
                    logger.info(
                        "awardCompletion failed, attempting direct Ether transfer"
                    )
                    nonce += 1
                    total_amount = points * 10**15
                    tx_ether = {
                        "from": my_address,
                        "to": w3.to_checksum_address(recipient_address),
                        "value": total_amount,
                        "nonce": nonce,
                        "chainId": chain_id,
                        "gas": 21000,
                        "gasPrice": w3.to_wei("20", "gwei"),
                    }
                    signed_ether_tx = w3.eth.account.sign_transaction(
                        tx_ether, private_key=private_key
                    )
                    ether_tx_hash = w3.eth.send_raw_transaction(
                        signed_ether_tx.raw_transaction
                    )
                    logger.info(
                        f"Ether transfer transaction sent: {ether_tx_hash.hex()}"
                    )
                    ether_receipt = w3.eth.wait_for_transaction_receipt(ether_tx_hash)
                    if ether_receipt.status == 0:
                        logger.error("Ether transfer transaction failed")
                        return (
                            jsonify(
                                {
                                    "valid": False,
                                    "message": f"Transaction failed: {revert_reason}",
                                }
                            ),
                            500,
                        )
                    # Proceed to mint NFT directly
                    logger.info("Ether transfer succeeded, attempting NFT mint")
                    nonce += 1
                    try:
                        gas = nft_contract.functions.mintNFT(
                            w3.to_checksum_address(recipient_address), token_uri
                        ).estimate_gas({"from": my_address})
                    except Exception as gas_error:
                        logger.error(f"NFT mint gas estimation failed: {gas_error}")
                        return (
                            jsonify(
                                {
                                    "valid": False,
                                    "message": f"NFT mint failed: {str(gas_error)}",
                                }
                            ),
                            500,
                        )
                    tx_nft = nft_contract.functions.mintNFT(
                        w3.to_checksum_address(recipient_address), token_uri
                    ).build_transaction(
                        {
                            "from": my_address,
                            "nonce": nonce,
                            "chainId": chain_id,
                            "gas": gas + 10000,
                            "gasPrice": w3.to_wei("20", "gwei"),
                        }
                    )
                    signed_nft_tx = w3.eth.account.sign_transaction(
                        tx_nft, private_key=private_key
                    )
                    nft_tx_hash = w3.eth.send_raw_transaction(
                        signed_nft_tx.raw_transaction
                    )
                    logger.info(f"NFT mint transaction sent: {nft_tx_hash.hex()}")
                    nft_receipt = w3.eth.wait_for_transaction_receipt(nft_tx_hash)
                    if nft_receipt.status == 0:
                        logger.error("NFT mint transaction failed")
                        try:
                            revert_reason = w3.eth.call(
                                {
                                    "from": my_address,
                                    "to": nft_address,
                                    "data": nft_contract.encodeABI(
                                        fn_name="mintNFT",
                                        args=[
                                            w3.to_checksum_address(recipient_address),
                                            token_uri,
                                        ],
                                    ),
                                },
                                block_identifier=nft_receipt.blockNumber,
                            )
                        except Exception as revert_error:
                            revert_reason = str(revert_error)
                        return (
                            jsonify(
                                {
                                    "valid": False,
                                    "message": f"NFT mint failed: {revert_reason}",
                                }
                            ),
                            500,
                        )
                    logger.info(f"NFT and Ether transferred to {recipient_address}")
                    return jsonify(
                        {"valid": True, "message": "Successfully sent NFT and Ether"}
                    )
                logger.error("Transaction failed without specific revert reason")
                return jsonify({"valid": False, "message": "Transaction failed"}), 500
            logger.info(f"NFT and Ether transferred to {recipient_address}")
            return jsonify(
                {"valid": True, "message": "Successfully sent NFT and Ether"}
            )
        else:
            # Handle non-10 points case (direct Ether transfer)
            total_amount = points * 10**15
            logger.info(f"Transfer amount for {points} points: {total_amount}")
            nonce = w3.eth.get_transaction_count(my_address)
            tx = {
                "from": my_address,
                "to": w3.to_checksum_address(recipient_address),
                "value": total_amount,
                "nonce": nonce,
                "chainId": chain_id,
                "gas": 21000,
                "gasPrice": w3.to_wei("20", "gwei"),
            }
            signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 0:
                logger.error("Transaction failed")
                return jsonify({"valid": False, "message": "Transaction failed"}), 500
            return jsonify({"valid": True, "message": "Successfully sent Ether"})
    except Exception as e:
        logger.error(f"Error in /transfer: {e}", exc_info=True)
        return jsonify({"valid": False, "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 4000))
    app.run(host="0.0.0.0", port=port, debug=True)
