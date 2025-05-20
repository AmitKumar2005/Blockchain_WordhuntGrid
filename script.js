const words = [
    ['TOONIX', 'SKETCHY', 'FRAMEUP', 'ANIMATE', 'DOODLES', 'CELLART', 'MOTION', 'PIXEL', 'CARTOON', 'FLASHIT'],
    ['BATTING', 'BOWLING', 'WICKETS', 'STUMPED', 'RUNOUTS', 'FIELD', 'SPINNER', 'CREASE', 'UMPIRE', 'GOOGLY'],
    ['SHOWSIP', 'GIGGLES', 'DRAMATE', 'FUNFEST', 'LAUGHING', 'PLAYFUL', 'STARLIT', 'JOKESON', 'GLAMOUR', 'THRILLER'],
    ['NOVELS', 'STORIES', 'FANTASY', 'MYSTICS', 'LEGENDS', 'FABLES', 'TALESPIN', 'IMAGINE', 'MYTHICAL', 'DREAMER'],
    ['CINEMA', 'FRAMES', 'REELSUP', 'SCREEN', 'FILMING', 'CLAPPER', 'POPCORN', 'DIRECTS', 'SCENES', 'TICKET'],
    ['MELODIC', 'RHYTHMS', 'TUNESUP', 'HARMONI', 'BEATS', 'LYRICS', 'CHORDS', 'SINGERS', 'NOTATED', 'JUKEBOX'],
    ['FOREST', 'RIVERS', 'MOUNTAIN', 'OCEANS', 'WILDIFE', 'MEADOW', 'SUNSETS', 'FLORAL', 'BREEZE', 'EARTH'],
    ['ATOMS', 'PHYSICS', 'CHEMIST', 'BIOLOGY', 'RESEARCH', 'LABWORK', 'THEORY', 'EXPERIMENT', 'SCIENCE', 'PROTONS'],
    ['GADGETS', 'CIRCUITS', 'SOFTWARE', 'HARDWARE', 'CODING', 'TECHBIT', 'INNOVATE', 'DIGITAL', 'NETWORK', 'ROBOTS']
];
const dir = ["horizontal_toRight", "horizontal_toLeft", "top_down", "upside_down", "diagonal_left_top", "diagonal_right_top"];

const display = document.querySelector('.display');
const metamaskAccount = document.querySelector('.metamaskAccount');
const wallet = document.querySelector('.wallet');
const timer = document.createElement('div');
const done = document.createElement('div');
const enter = document.querySelector('.enter');
let walletBalance = 0;
let accountNumber = "";
done.className = "done";
display.appendChild(done);
timer.innerText = "02:00";
timer.className = "timer";
let leftTime = 120;
let id;
let correctCount = 0;
let ut;
let wordPositions = [];
let isPressed = false;
let coordinates = [];
let str = "";
let initx = -1;
let inity = -1;

const API_URL = "https://blockchain-wordhuntgrid.onrender.com";

const n = 11, m = 15;
const grid = new Array(n).fill().map(() => new Array(m).fill(-1));

function setup() {
    wordPositions = [];
    let list = words[id];
    let placedWords = 0;

    while (placedWords < list.length) {
        for (let i = 0; i < n; i++) {
            for (let j = 0; j < m; j++) {
                grid[i][j] = -1;
            }
        }
        wordPositions = [];
        placedWords = 0;

        for (let i = 0; i < list.length; i++) {
            let isAssigned = false;
            let maxAttempt = 1000;

            while (!isAssigned && maxAttempt > 0) {
                let len = list[i].length;
                let x = Math.floor(Math.random() * n);
                let y = Math.floor(Math.random() * m);
                let idx = Math.floor(Math.random() * dir.length);
                let positions = [];

                if (idx === 4 && x + len - 1 < n && y + len - 1 < m) {
                    let available = true;
                    for (let j = 0; j < len; j++) if (grid[x + j][y + j] !== -1) available = false;
                    if (available) {
                        for (let j = 0; j < len; j++) {
                            grid[x + j][y + j] = list[i][j];
                            positions.push([x + j, y + j]);
                        }
                        isAssigned = true;
                    }
                }
                else if (idx === 2 && x + len - 1 < n) {
                    let available = true;
                    for (let j = 0; j < len; j++) if (grid[x + j][y] !== -1) available = false;
                    if (available) {
                        for (let j = 0; j < len; j++) {
                            grid[x + j][y] = list[i][j];
                            positions.push([x + j, y]);
                        }
                        isAssigned = true;
                    }
                }
                else if (idx === 0 && y + len - 1 < m) {
                    let available = true;
                    for (let j = 0; j < len; j++) if (grid[x][y + j] !== -1) available = false;
                    if (available) {
                        for (let j = 0; j < len; j++) {
                            grid[x][y + j] = list[i][j];
                            positions.push([x, y + j]);
                        }
                        isAssigned = true;
                    }
                }
                else if (idx === 1 && y - len + 1 >= 0) {
                    let available = true;
                    for (let j = 0; j < len; j++) if (grid[x][y - j] !== -1) available = false;
                    if (available) {
                        for (let j = 0; j < len; j++) {
                            grid[x][y - j] = list[i][j];
                            positions.push([x, y - j]);
                        }
                        isAssigned = true;
                    }
                }
                else if (idx === 3 && x - len + 1 >= 0) {
                    let available = true;
                    for (let j = 0; j < len; j++) if (grid[x - j][y] !== -1) available = false;
                    if (available) {
                        for (let j = 0; j < len; j++) {
                            grid[x - j][y] = list[i][j];
                            positions.push([x - j, y]);
                        }
                        isAssigned = true;
                    }
                }
                else if (idx === 5 && x - len + 1 >= 0 && y + len - 1 < m) {
                    let available = true;
                    for (let j = 0; j < len; j++) if (grid[x - j][y + j] !== -1) available = false;
                    if (available) {
                        for (let j = 0; j < len; j++) {
                            grid[x - j][y + j] = list[i][j];
                            positions.push([x - j, y + j]);
                        }
                        isAssigned = true;
                    }
                }
                if (isAssigned) {
                    wordPositions.push({ word: list[i], positions });
                    placedWords++;
                }
                maxAttempt--;
            }
        }
    }

    for (let i = 0; i < n; i++) {
        for (let j = 0; j < m; j++) {
            if (grid[i][j] === -1) grid[i][j] = String.fromCharCode(65 + Math.floor(Math.random() * 26));
        }
    }
    displayGrid();
    displayList(id);
}

function displayGrid() {
    display.innerHTML = '';
    display.appendChild(timer);
    const table = document.createElement('table');
    table.className = "grid";
    for (let i = 0; i < n; i++) {
        const row = document.createElement('tr');
        row.className = "row";
        for (let j = 0; j < m; j++) {
            const cell = document.createElement('td');
            cell.className = "cell";
            cell.innerText = grid[i][j];
            cell.dataset.row = i;
            cell.dataset.col = j;
            row.appendChild(cell);
        }
        table.appendChild(row);
    }
    display.appendChild(table);
    addGridListener();
    correctGuess();
}

function displayList() {
    const table = document.createElement('table');
    const heading = document.createElement('th');
    const headingRow = document.createElement('tr');
    headingRow.appendChild(heading);
    table.appendChild(headingRow);
    heading.innerText = 'Remaining';
    table.className = 'listGrid';
    table.appendChild(heading);
    for (let i = 0; i < 10; i++) {
        const row = document.createElement('tr');
        row.className = 'listRow';
        row.innerText = words[id][i];
        table.appendChild(row);
    }
    display.appendChild(table);
}

function addGridListener() {
    const cells = document.querySelectorAll('.cell');

    cells.forEach(cell => {
        cell.addEventListener('mousedown', function (e) {
            if (!cell.classList.contains('found') && !isPressed) {
                e.preventDefault();
                isPressed = true;
                str = cell.innerText;
                cell.classList.add('selected');
                initx = parseInt(cell.dataset.row);
                inity = parseInt(cell.dataset.col);
                coordinates.push([initx, inity]);
            }
        });

        cell.addEventListener('mouseover', function (e) {
            e.preventDefault();
            if (isPressed && !cell.classList.contains('found')) {
                let curx = parseInt(cell.dataset.row), cury = parseInt(cell.dataset.col);
                if (isValidDirection(initx, inity, curx, cury, coordinates)) {
                    if (!coordinates.some(([x, y]) => x === curx && y === cury)) {
                        str += cell.innerText;
                        cell.classList.add('selected');
                        coordinates.push([curx, cury]);
                    }
                }
                else {
                    reset();
                }
            }
        });

        cell.addEventListener('mouseup', function (e) {
            e.preventDefault();
            if (isPressed) {
                isPressed = false;
                check();
                reset();
            }
        });
    });

    document.querySelector('.grid').addEventListener('mouseleave', function (e) {
        e.preventDefault();
        if (isPressed) {
            isPressed = false;
            reset();
        }
    });
}

function isValidDirection(initx, inity, curx, cury, coordinates) {
    if (coordinates.length === 1) return true;
    let dx = curx - initx;
    let dy = cury - inity;
    let len = coordinates.length;
    if (dx === 0) {
        return dy === len || dy === -len;
    }
    else if (dy === 0) {
        return dx === len || dx === -len;
    }
    else if (Math.abs(dx) === Math.abs(dy)) {
        return (dx === len && dy === len) || (dx === -len && dy === -len) || (dx === len && dy === -len) || (dx === -len && dy === len);
    }
    return false;
}

function reset() {
    str = "";
    coordinates = [];
    isPressed = false;
    clearSelection();
}

function clearSelection() {
    document.querySelectorAll('.cell.selected').forEach(cell => {
        if (!cell.classList.contains('found')) cell.classList.remove('selected');
    });
}

function check() {
    const rev = str.split('').reverse().join('');
    let foundWord = null;

    wordPositions.forEach(w => {
        if ((w.word === str || w.word === rev) && coordinatesMatch(w.positions, coordinates)) {
            foundWord = w;
        }
    });

    if (foundWord) {
        foundWord.positions.forEach(([row, col]) => {
            const cell = document.querySelector(`.cell[data-row="${row}"][data-col="${col}"]`);
            cell.classList.add('found');
            cell.classList.remove('selected');
        });
        document.querySelectorAll('.listRow').forEach(row => {
            if (row.innerText === foundWord.word) row.classList.add('append');
        });
        correctCount++;
        correctGuess();
    }
}

function coordinatesMatch(wordPos, selectedCoordinates) {
    if (wordPos.length !== selectedCoordinates.length) return false;
    return wordPos.every(([row, col], i) => row === selectedCoordinates[i][0] && col === selectedCoordinates[i][1]) ||
        wordPos.every(([row, col], i) => row === selectedCoordinates[selectedCoordinates.length - 1 - i][0] &&
            col === selectedCoordinates[selectedCoordinates.length - 1 - i][1]);
}

function updateTimer() {
    leftTime--;
    let minute = Math.floor(leftTime / 60);
    let second = leftTime % 60;
    timer.innerText = `0${minute}:${second < 10 ? '0' : ''}${second}`;
    if (leftTime <= 0) {
        clearInterval(ut);
        timer.innerText = "00:00";
        collectAmount();
    }
}

function correctGuess() {
    let done = document.querySelector('.done');
    if (!done) {
        done = document.createElement('div');
        done.className = "done";
        display.appendChild(done);
    }
    done.innerText = `Score: ${correctCount}/10`;
    checkwin();
}

function checkwin() {
    if (correctCount == 10) {
        clearInterval(ut);
        collectAmount();
    }
}

async function collectAmount() {
    display.classList.remove('active');
    const winGame = document.createElement('div');
    winGame.className = 'winGame';
    winGame.innerText = `Your Score is ${correctCount}`;
    const claim = document.createElement('div');
    claim.className = 'option1';
    claim.innerText = 'Claim';
    winGame.appendChild(claim);
    const addToWallet = document.createElement('div');
    addToWallet.className = 'option2';
    addToWallet.innerText = 'Add to Wallet';
    winGame.appendChild(addToWallet);
    document.body.appendChild(winGame);

    claim.addEventListener('mousedown', async function () {
        winGame.innerText = "Processing...";
        try {
            console.log("Sending /transfer request:", { points: correctCount, address: accountNumber });
            const response = await fetch(`${API_URL}/transfer`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ points: correctCount, address: accountNumber })
            });
            console.log(`Response: ${response.status} ${response.statusText}`);
            const res = await response.json();
            if (!response.ok) {
                console.error(`Transfer failed: ${response.status} ${response.statusText}`, res);
                alert(`Transaction failed: ${res.message || res.error || 'Unknown error'} (Status: ${response.status}). Tokens added to wallet.`);
                await addToBalance();
            } else {
                winGame.innerHTML = '';
                winGame.innerText = correctCount === 10 ? "Transaction Success! You've earned an NFT!" : "Transaction Success!";
                setTimeout(() => {
                    document.body.removeChild(winGame);
                    document.querySelector('.category').classList.remove('blur-background');
                }, 2000);
            }
        } catch (error) {
            console.error("Error in collectAmount:", error);
            alert(`Failed to process transaction: ${error.message || 'Network error'}`);
        }
    });

    addToWallet.addEventListener('mousedown', async () => {
        try {
            await addToBalance();
            document.body.removeChild(winGame);
            document.querySelector('.category').classList.remove('blur-background');
        } catch (error) {
            console.error("Error in addToWallet:", error);
            alert(`Failed to add to wallet: ${error.message || 'Network error'}`);
        }
    });
}

function gameStart() {
    display.innerHTML = '';
    leftTime = 120;
    correctCount = 0;
    if (ut) clearInterval(ut);
    setup();
    ut = setInterval(updateTimer, 1000);
}

document.querySelector('.container').addEventListener('click', function (e) {
    if (e.target.classList.contains('choice')) {
        document.querySelector('.category').classList.add('blur-background');
        display.classList.add('active');
        id = parseInt(e.target.id);
        gameStart();
    }
});

function initialize() {
    if (accountNumber === "") {
        setTimeout(() => {
            document.querySelector('.category').classList.add('blur-background');
            metamaskAccount.className = 'metamaskAccount accountNo';
            metamaskAccount.innerHTML = `
                <form class="accForm">
                    <label for="accountNo">Account No.:</label><br><br>
                    <input type="text" name="accountNo" class="accountInput" placeholder="Enter your account address here" required><br><br>
                    <button type="submit" class="accSubmit">Submit</button>
                </form>
            `;
            document.querySelector('.accForm').addEventListener('submit', function (e) {
                e.preventDefault();
                accountNumber = document.querySelector('.accountInput').value;
                document.querySelector('.category').classList.remove('blur-background');
                metamaskAccount.className = 'metamaskAccount';
                metamaskAccount.innerHTML = '';
                processAddress();
                balance();
            });
        }, 1000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initialize();
});

async function processAddress() {
    try {
        console.log("Sending /verifyAddress request:", { address: accountNumber });
        const response = await fetch(`${API_URL}/verifyAddress`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address: accountNumber })
        });
        console.log(`Response: ${response.status} ${response.statusText}`);
        const res = await response.json();
        if (!response.ok) {
            console.error(`Verify address failed: ${response.status} ${response.statusText}`, res);
            alert(`Non-Ethereum browser detected or invalid address: ${res.message || res.error || 'Unknown error'} (Status: ${response.status})`);
            accountNumber = "";
            initialize();
        } else {
            enter.innerText = `Account: ${accountNumber.slice(0, 4)}...${accountNumber.slice(-4)}`;
        }
    } catch (error) {
        console.error("Error in processAddress:", error);
        alert(`Failed to verify address: ${error.message || 'Network error'}`);
        accountNumber = "";
        initialize();
    }
}

async function balance() {
    try {
        console.log("Sending /balance request:", { address: accountNumber });
        const response = await fetch(`${API_URL}/balance`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address: accountNumber })
        });
        console.log(`Response: ${response.status} ${response.statusText}`);
        const res = await response.json();
        if (!response.ok) {
            console.error(`Balance fetch failed: ${response.status} ${response.statusText}`, res);
            alert(`Failed to fetch balance: ${res.error || res.message || 'Unknown error'} (Status: ${response.status})`);
        } else {
            wallet.innerText = `Wallet: ${res.balance}`;
            walletBalance = res.balance;
        }
    } catch (error) {
        console.error("Error in balance:", error);
        alert(`Failed to fetch balance: ${error.message || 'Network error'}`);
    }
}

async function addToBalance() {
    try {
        console.log("Sending /addToBalance request:", { address: accountNumber, points: correctCount });
        const response = await fetch(`${API_URL}/addToBalance`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address: accountNumber, points: correctCount })
        });
        console.log(`Response: ${response.status} ${response.statusText}`);
        const res = await response.json();
        if (!response.ok) {
            console.error(`Add to balance failed: ${response.status} ${response.statusText}`, res);
            alert(`Failed to add to balance: ${res.error || res.message || 'Unknown error'} (Status: ${response.status})`);
        } else {
            wallet.innerText = `Wallet: ${res.balance}`;
            walletBalance = res.balance;
        }
    } catch (error) {
        console.error("Error in addToBalance:", error);
        alert(`Failed to add to balance: ${error.message || 'Network error'}`);
    }
}

wallet.addEventListener('mousedown', () => {
    document.querySelector('.category').classList.add('blur-background');
    display.classList.remove('active');

    if (walletBalance == 0) {
        const winGame = document.createElement('div');
        winGame.className = 'winGame';
        winGame.innerText = `Wallet is empty`;
        document.body.appendChild(winGame);
        setTimeout(() => {
            document.body.removeChild(winGame);
            document.querySelector('.category').classList.remove('blur-background');
        }, 1000);
    } else {
        const winGame = document.createElement('div');
        winGame.className = 'winGame';
        winGame.innerText = `Claim ${walletBalance} Tokens`;
        const claim = document.createElement('div');
        claim.className = 'option1';
        claim.innerText = 'Claim';
        winGame.appendChild(claim);
        const cancel = document.createElement('div');
        cancel.className = 'option2';
        cancel.innerText = 'Cancel';
        winGame.appendChild(cancel);
        document.body.appendChild(winGame);
        claim.addEventListener('mousedown', async function () {
            winGame.innerText = "Processing...";
            try {
                console.log("Sending /walletTransfer request:", { points: walletBalance, address: accountNumber });
                const response = await fetch(`${API_URL}/walletTransfer`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ points: walletBalance, address: accountNumber })
                });
                console.log(`Response: ${response.status} ${response.statusText}`);
                const res = await response.json();
                if (!response.ok) {
                    console.error(`Wallet transfer failed: ${response.status} ${response.statusText}`, res);
                    alert(`Transaction failed: ${res.message || res.error || 'Unknown error'} (Status: ${response.status})`);
                } else {
                    winGame.innerText = "Transaction Success!";
                    wallet.innerText = "Wallet: 0";
                    walletBalance = 0;
                    setTimeout(() => {
                        document.body.removeChild(winGame);
                        document.querySelector('.category').classList.remove('blur-background');
                    }, 1000);
                }
            } catch (error) {
                console.error("Error in walletTransfer:", error);
                alert(`Failed to process wallet transfer: ${error.message || 'Network error'}`);
            }
        });
        cancel.addEventListener('mousedown', () => {
            document.body.removeChild(winGame);
            document.querySelector('.category').classList.remove('blur-background');
        });
    }
});

enter.addEventListener('mousedown', () => {
    document.querySelector('.category').classList.add('blur-background');
    display.classList.remove('active');
    const winGame = document.createElement('div');
    winGame.className = 'winGame';
    winGame.innerText = `Logout`;
    const logout = document.createElement('div');
    logout.className = 'option1';
    logout.innerText = 'Logout';
    winGame.appendChild(logout);
    const cancel = document.createElement('div');
    cancel.className = 'option2';
    cancel.innerText = 'Cancel';
    winGame.appendChild(cancel);
    document.body.appendChild(winGame);
    logout.addEventListener('mousedown', () => {
        accountNumber = "";
        enter.innerText = "";
        wallet.innerText = "Wallet: 0";
        walletBalance = 0;
        document.body.removeChild(winGame);
        document.querySelector('.category').classList.remove('blur-background');
        initialize();
    });
    cancel.addEventListener('mousedown', () => {
        document.body.removeChild(winGame);
        document.querySelector('.category').classList.remove('blur-background');
    });
});