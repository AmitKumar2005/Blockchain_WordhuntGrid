// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

contract WordHuntNFT is ERC721, ERC721URIStorage {
    uint256 private _tokenIds;

    constructor() ERC721("WordHuntNFT", "WHNFT") {
        _tokenIds = 0;
    }

    function tokenURI(
        uint256 tokenId
    ) public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(
        bytes4 interfaceId
    ) public view override(ERC721, ERC721URIStorage) returns (bool) {
        return super.supportsInterface(interfaceId);
    }

    function mintNFT(
        address player,
        string memory tokenURI_
    ) public returns (uint256) {
        _tokenIds += 1;
        uint256 newItemId = _tokenIds;
        _mint(player, newItemId);
        _setTokenURI(newItemId, tokenURI_);
        return newItemId;
    }
}

// contract transfer {
//     uint256 public perCorrect = 1e15;
//     mapping(address => uint256) public sender;
//     address from;
//     address to;
//     WordHuntNFT public nftContract;

//     constructor(address _nftContractAddress) {
//         nftContract = WordHuntNFT(_nftContractAddress);
//     }

//     function senderAdd(address s) public {
//         from = s;
//     }

//     function receiverAdd(address s) public {
//         to = s;
//     }

//     function fund(uint256 points) public view returns (uint256) {
//         uint256 transferEth = points * perCorrect;
//         return transferEth;
//     }

//     function awardNFT(address player, string memory tokenURI_) public {
//         nftContract.mintNFT(player, tokenURI_);
//     }
// }

contract transfer {
    uint256 public perCorrect = 1e15;
    mapping(address => uint256) public sender;
    address from;
    address to;
    WordHuntNFT public nftContract;

    constructor(address _nftContractAddress) {
        nftContract = WordHuntNFT(_nftContractAddress);
    }

    function awardCompletion(
        address player,
        uint256 points,
        string memory tokenURI_
    ) public {
        require(points == 10, "Must complete game (10 points)");
        uint256 transferEth = points * perCorrect;
        payable(player).transfer(transferEth);
        nftContract.mintNFT(player, tokenURI_);
    }

    function spendCoins(
        address player,
        uint256 amount,
        string memory item
    ) public {
        require(amount <= address(this).balance, "Contract lacks funds");
        require(msg.sender == player, "Only player can spend");
        payable(player).transfer(amount); // Refund for simplicity; adjust logic for real spending
        emit CoinSpent(player, amount, item);
    }
    event CoinSpent(address indexed player, uint256 amount, string item);

    function deposit() public payable {}
}
