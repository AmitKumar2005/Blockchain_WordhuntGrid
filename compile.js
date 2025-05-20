const fs = require("fs");
const path = require("path");
const solc = require("solc");

const contractPath = path.resolve(__dirname, "contract.sol");
const source = fs.readFileSync(contractPath, "utf8");

// Map OpenZeppelin imports
const findImports = (importPath) => {
    const fullPath = path.resolve(__dirname, "node_modules", importPath);
    if (fs.existsSync(fullPath)) {
        return { contents: fs.readFileSync(fullPath, "utf8") };
    } else {
        return { error: "File not found: " + importPath };
    }
};

const input = {
    language: "Solidity",
    sources: {
        "contract.sol": {
            content: source,
        },
    },
    settings: {
        outputSelection: {
            "*": {
                "*": ["abi", "evm.bytecode"],
            },
        },
    },
};

const output = JSON.parse(solc.compile(JSON.stringify(input), { import: findImports }));

const contracts = output.contracts["contract.sol"];
if (!contracts) {
    console.error("❌ Compilation failed:", output.errors || output);
    process.exit(1);
}

for (const name in contracts) {
    const abi = contracts[name].abi;
    const bytecode = contracts[name].evm.bytecode.object;

    const outPath = path.resolve(__dirname, "contract_data.json");
    fs.writeFileSync(
        outPath,
        JSON.stringify({ name, abi, bytecode }, null, 2),
        "utf8"
    );
    console.log(`✅ Compiled ${name}, saved ABI and bytecode to contract_data.json`);
}
