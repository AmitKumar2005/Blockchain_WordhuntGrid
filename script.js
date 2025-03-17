const words = [
    ['TOONIX', 'SKETCHY', 'FRAMEUP', 'ANIMATE', 'DOODLES', 'CELLART', 'MOTION', 'PIXEL', 'CARTOON', 'FLASHIT'],
    ['BATTING', 'BOWLING', 'WICKETS', 'STUMPED', 'RUNOUTS', 'FIELD', 'SPINNER', 'CREASE', 'UMPIRE', 'GOOGLY'],
    ['SHOWSIP', 'GIGGLES', 'DRAMATE', 'FUNFEST', 'LAUGHING', 'PLAYFUL', 'STARLIT', 'JOKESON', 'GLAMOUR', 'THRILLER'],
    ['NOVELS', 'STORIES', 'FANTASY', 'MYSTICS', 'LEGENDS', 'FABLES', 'TALESPIN', 'IMAGINE', 'MYTHICAL', 'DREAMER'],
    ['CINEMA', 'FRAMES', 'REELSUP', 'SCREEN', 'FILMING', 'CLAPPER', 'POPCORN', 'DIRECTS', 'SCENES', 'TICKET'],
    ['MELODIC', 'RHYTHMS', 'TUNESUP', 'HARMONI', 'BEATS', 'LYRICS', 'CHORDS', 'SINGERS', 'NOTATED', 'JUKEBOX'],
    ['FOREST', 'RIVERS', 'MOUNTIAN', 'OCEANS', 'WILDIFE', 'MEADOW', 'SUNSETS', 'FLORAL', 'BREEZE', 'EARTH'],
    ['ATOMS', 'PHYSICS', 'CHEMIST', 'BIOLOGY', 'RESEARCH', 'LABWORK', 'THEORY', 'EXPERIMENT', 'SCIENCE', 'PROTONS'],
    ['GADGETS', 'CIRCUITS', 'SOFTWARE', 'HARDWARE', 'CODING', 'TECHBIT', 'INNOVATE', 'DIGITAL', 'NETWORK', 'ROBOTS']
];
const dir = ["horizontal_toRight", "horizontal_toLeft", "top_down", "upside_down", "diagonal_left_top", "diagonal_right_top"];

const display = document.querySelector('.display');
const timer = document.createElement('div');
const done = document.createElement('div');
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

const n = 11;
const grid = new Array(n).fill().map(() => new Array(n).fill(-1));

function setup() {
    wordPositions = [];
    let list = words[id];
    let placedWords = 0;

    while (placedWords < list.length) {
        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
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
                let y = Math.floor(Math.random() * n);
                let idx = Math.floor(Math.random() * dir.length);
                let positions = [];

                if (idx === 0 && y + len - 1 < n) {
                    let available = true;
                    for (let j = 0; j < len; j++) if (grid[x][y + j] !== -1) available = false;
                    if (available) {
                        for (let j = 0; j < len; j++) {
                            grid[x][y + j] = list[i][j];
                            positions.push([x, y + j]);
                        }
                        isAssigned = true;
                    }
                } else if (idx === 1 && y - len + 1 >= 0) {
                    let available = true;
                    for (let j = 0; j < len; j++) if (grid[x][y - j] !== -1) available = false;
                    if (available) {
                        for (let j = 0; j < len; j++) {
                            grid[x][y - j] = list[i][j];
                            positions.push([x, y - j]);
                        }
                        isAssigned = true;
                    }
                } else if (idx === 2 && x + len - 1 < n) {
                    let available = true;
                    for (let j = 0; j < len; j++) if (grid[x + j][y] !== -1) available = false;
                    if (available) {
                        for (let j = 0; j < len; j++) {
                            grid[x + j][y] = list[i][j];
                            positions.push([x + j, y]);
                        }
                        isAssigned = true;
                    }
                } else if (idx === 3 && x - len + 1 >= 0) {
                    let available = true;
                    for (let j = 0; j < len; j++) if (grid[x - j][y] !== -1) available = false;
                    if (available) {
                        for (let j = 0; j < len; j++) {
                            grid[x - j][y] = list[i][j];
                            positions.push([x - j, y]);
                        }
                        isAssigned = true;
                    }
                } else if (idx === 4 && x + len - 1 < n && y + len - 1 < n) {
                    let available = true;
                    for (let j = 0; j < len; j++) if (grid[x + j][y + j] !== -1) available = false;
                    if (available) {
                        for (let j = 0; j < len; j++) {
                            grid[x + j][y + j] = list[i][j];
                            positions.push([x + j, y + j]);
                        }
                        isAssigned = true;
                    }
                } else if (idx === 5 && x - len + 1 >= 0 && y + len - 1 < n) {
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
        for (let j = 0; j < n; j++) {
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
        for (let j = 0; j < n; j++) {
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


function addGridListener(){
    const cells = document.querySelectorAll('.cell');

    cells.forEach(cell => {
        cell.addEventListener('mousedown', function(e){
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

        cell.addEventListener('mouseover', function(e){
            e.preventDefault();
                if (isPressed && !cell.classList.contains('found')) {
                let curx = parseInt(cell.dataset.row), cury = parseInt(cell.dataset.col);
                if(isValidDirection(initx, inity, curx, cury, coordinates)){
                    if (!coordinates.some(([x, y]) => x === curx && y === cury)) {
                        str += cell.innerText;
                        cell.classList.add('selected');
                        coordinates.push([curx, cury]);
                    }
                }
                else{
                    reset();
                }
            }
        });


        cell.addEventListener('mouseup', function(e){
            e.preventDefault();
            if (isPressed) {
                isPressed = false;
                check();
                reset();
            }
        });
    })

    document.querySelector('.grid').addEventListener('mouseleave', function(e) {
        e.preventDefault();
        if (isPressed) {
            isPressed = false;
            reset();
        }
    });
}

function isValidDirection(initx, inity, curx, cury, coordinates){
    if (coordinates.length === 1) return true;
    let dx = curx - initx;
    let dy = cury - inity;
    let len = coordinates.length;
    if (dx === 0){                                       
        return dy === len || dy === -len;
    }
    else if (dy === 0){                                  
        return dx === len || dx === -len;
    }
    else if (Math.abs(dx) === Math.abs(dy)){             
        return (dx === len && dy === len) || (dx === -len && dy === -len) || (dx === len && dy === -len) || (dx === -len && dy === len);
    }
    return false;
}

function reset(){
    str = "";
    coordinates = [];
    isPressed = false;
    clearSelection();
}

function clearSelection(){
    document.querySelectorAll('.cell.selected').forEach(cell => {
        if (!cell.classList.contains('found')) cell.classList.remove('selected');
    })
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
    if (wordPos.length !== selectedCoordinates.length)      return false;
    return wordPos.every(([row, col], i) => row === selectedCoordinates[i][0] && col === selectedCoordinates[i][1]) || 
           wordPos.every(([row, col], i) => row === selectedCoordinates[selectedCoordinates.length - 1 - i][0] && 
                                            col === selectedCoordinates[selectedCoordinates.length - 1 - i][1]);
}

function displayList(){
    const table = document.createElement('table');
    const heading = document.createElement('th');
    const headingRow = document.createElement('tr');
    headingRow.appendChild(heading);
    table.appendChild(headingRow);
    heading.innerText = 'Remaining';
    table.className = 'listGrid';
    table.appendChild(heading);
    for(let i=0;i<10;i++){
        const row = document.createElement('tr');
        row.className = 'listRow';
        row.innerText = words[id][i];
        table.appendChild(row);
    }
    display.appendChild(table);
}

function updateTimer() {
    leftTime--;
    let minute = Math.floor(leftTime / 60);
    let second = leftTime % 60;
    timer.innerText = `0${minute}:${second < 10 ? '0' : ''}${second}`;
    if (leftTime <= 0) {
        clearInterval(ut);
        timer.innerText = "00:00";
        lose();
    }
}

function lose(){
    display.classList.remove('active');
    const loseGame = document.createElement('div');
    loseGame.className = 'loseGame';
    loseGame.innerText = `Your Score is ${correctCount}`;
    const claim = document.createElement('div');
    claim.className = 'claim';
    claim.innerText = 'Claim';
    loseGame.appendChild(claim);
    const addToWallet = document.createElement('div');
    addToWallet.className = 'addToWallet';
    addToWallet.innerText = 'Add to Wallet';
    loseGame.appendChild(addToWallet);
    document.body.appendChild(loseGame);
}

function correctGuess(){
    let done = document.querySelector('.done');
    if (!done) {
        done = document.createElement('div');
        done.className = "done";
        display.appendChild(done);
    }
    done.innerText = `Score: ${correctCount}/10`;
    checkwin();
}

function checkwin(){
    if(correctCount==10){
        clearInterval(ut);
        win();
    }
}

function win(){
    display.classList.remove('active');
    const winGame = document.createElement('div');
    winGame.className = 'winGame';
    winGame.innerText = `Your Score is ${correctCount}`;
    const claim = document.createElement('div');
    claim.className = 'claim';
    claim.innerText = 'Claim';
    winGame.appendChild(claim);
    const addToWallet = document.createElement('div');
    addToWallet.className = 'addToWallet';
    addToWallet.innerText = 'Add to Wallet';
    winGame.appendChild(addToWallet);
    document.body.appendChild(winGame);
}

function gameStart() {
    display.innerHTML = '';
    leftTime = 120;
    correctCount = 0;
    if (ut) clearInterval(ut);
    setup();
    ut = setInterval(updateTimer, 1000);
}

document.querySelector('.container').addEventListener('click', function(e){
    if (e.target.classList.contains('choice')) {
        document.querySelector('.category').classList.add('blur-background');
        display.classList.add('active');
        id = parseInt(e.target.id);
        gameStart();
    }
});