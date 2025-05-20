const fs = require("fs");
const path = require("path");
const solc = require("solc");

const contractPath = path.resolve(__dirname, "contract.sol");
const source = fs.readFileSync(contractPath, "utf8");

// Map OpenZeppelin imports
const findImports = (importPath) => {
    // Handle OpenZeppelin imports
    if (importPath.startsWith("@openzeppelin/contracts/")) {
        const fullPath = path.resolve(__dirname, "node_modules", importPath);
        if (fs.existsSync(fullPath)) {
            return { contents: fs.readFileSync(fullPath, "utf8") };
        } else {
            return { error: `File not found: ${fullPath}` };
        }
    }
    // Handle other imports (if any)
    const fullPath = path.resolve(__dirname, importPath);
    if (fs.existsSync(fullPath)) {
        return { contents: fs.readFileSync(fullPath, "utf8") };
    }
    return { error: `File not found: ${importPath}` };
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
        remappings: [
            "@openzeppelin/contracts/=node_modules/@openzeppelin/contracts/"
        ],
    },
};

try {
    const output = JSON.parse(solc.compile(JSON.stringify(input), { import: findImports }));

    if (output.errors) {
        console.error("❌ Compilation failed:");
        output.errors.forEach((err) => {
            console.error(err.formattedMessage || err.message);
        });
        process.exit(1);
    }

    const contracts = output.contracts["contract.sol"];
    if (!contracts) {
        console.error("❌ No contracts found in compilation output");
        process.exit(1);
    }

    const contractData = {};
    for (const name in contracts) {
        contractData[name] = {
            abi: contracts[name].abi,
            bytecode: contracts[name].evm.bytecode.object,
        };
        console.log(`✅ Compiled ${name}`);
    }

    const outPath = path.resolve(__dirname, "contract_data.json");
    fs.writeFileSync(
        outPath,
        JSON.stringify(contractData, null, 2),
        "utf8"
    );
    console.log(`✅ Saved ABI and bytecode for all contracts to ${outPath}`);
} catch (error) {
    console.error("❌ Compilation error:", error.message);
    process.exit(1);
}