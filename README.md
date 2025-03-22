## Wordhunt Grid
This is a Blockchain based memory game, where the user is supposed to find word from the grid. 
For each word found, user gets 1 token and after the finish of game, user gets ether price corresponding to the tokens collected.

## Working
We have a client-side website where players select categories and find words in an 11x15 grid. Each correct word earns a token, tracked on the frontend. These tokens are powered by Ethereum Smart Contracts, which serve as the business logic for token management.</br>
The Ethereum Smart Contracts govern the transfer of Ether rewards, with a Flask backend and MySQL database managing wallet balances.</br>
Once earned, Ether can be claimed to any Ethereum wallet or stored for later withdrawal.
The current implementation uses fungible ETH rewards (0.001 ETH per token).</br>
 
## Rules
1. The user selects a category (e.g., Animation, Science) from the main screen.</br>
2. A grid appears with 10 hidden words; the player has 120 seconds to find them.</br>
3. Click and drag across the grid to select a word; if it matches a hidden word, you earn +1 token.</br>
4. A MetaMask pop-up may appear to confirm token-related transactions on the Ethereum network.</br>
5. Found words are highlighted, and their listing blurs out on the sidebar.</br>
6. If a selected sequence doesn’t match, it resets, allowing you to try again.</br>
7. The game ends when the timer runs out or all 10 words are found; you can then claim your Ether rewards either in your wallet or directly to your account.</br>


## Technologies used

**Ethereum / Solidity** </br>
Ethereum provides open access to digital money and data-friendly services for everyone, regardless of background or location. </br>
Solidity is an object-oriented, high-level language for implementing smart contracts, which govern account behavior within the Ethereum state. </br>

**Flask**</br>
Flask is a lightweight Python web framework used to build the backend server for handling API requests and blockchain interactions.</br>

**Web3.py**</br>
Web3.py is a Python library for interacting with Ethereum, used here to deploy contracts and handle transactions.</br>

**MySQL**</br>
MySQL is used to store player wallet balances, tracking tokens earned in the game.</br>

**Metamask**</br>
MetaMask is a software cryptocurrency wallet that interacts with the Ethereum blockchain, enabling users to manage keys, send/receive ETH, and handle transactions.</br>

**JavaScript / HTML / CSS**</br>
JavaScript powers the game logic and interactivity, while HTML and CSS create a responsive, visually appealing frontend interface.</br>
