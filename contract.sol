// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

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

contract transfer is Ownable {
    uint256 public perCorrect = 1e15;
    mapping(address => uint256) public sender;
    address from;
    address to;
    WordHuntNFT public nftContract;

    constructor(address _nftContractAddress) Ownable(msg.sender) {
        nftContract = WordHuntNFT(_nftContractAddress);
    }

    function awardCompletion(
        address player,
        uint256 points,
        string memory tokenURI_
    ) public payable onlyOwner {
        require(points == 10, "Must complete game (10 points)");
        uint256 transferEth = points * perCorrect;
        require(
            address(this).balance >= transferEth,
            "Insufficient contract balance"
        );
        payable(player).transfer(transferEth);
        nftContract.mintNFT(player, tokenURI_);
    }

    function transferEtherOnly(
        address player,
        uint256 points
    ) public onlyOwner {
        require(points == 10, "Must complete game (10 points)");
        uint256 transferEth = points * perCorrect;
        require(
            address(this).balance >= transferEth,
            "Insufficient contract balance"
        );
        payable(player).transfer(transferEth);
    }

    function mintNFTOnly(
        address player,
        string memory tokenURI_
    ) public onlyOwner {
        nftContract.mintNFT(player, tokenURI_);
    }

    function spendCoins(
        address player,
        uint256 amount,
        string memory item
    ) public {
        require(amount <= address(this).balance, "Contract lacks funds");
        require(msg.sender == player, "Only player can spend");
        payable(player).transfer(amount);
        emit CoinSpent(player, amount, item);
    }

    event CoinSpent(address indexed player, uint256 amount, string item);

    function deposit() public payable {}
}
