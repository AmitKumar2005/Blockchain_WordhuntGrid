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

contract Transfer is Ownable {
    uint256 public perCorrect = 1e15; // 0.001 ETH
    mapping(address => uint256) public sender;
    WordHuntNFT public nftContract;

    constructor(address _nftContractAddress) Ownable(msg.sender) {
        nftContract = WordHuntNFT(_nftContractAddress);
    }

    // For points == 10: Transfer Ether and mint NFT
    function awardCompletion(
        address player,
        uint256 points,
        string memory tokenURI_
    ) public payable onlyOwner {
        require(points == 10, "Must complete game (10 points)");
        uint256 transferEth = points * perCorrect; // 10 * 0.001 ETH = 0.01 ETH
        require(
            address(this).balance >= transferEth,
            "Insufficient contract balance"
        );
        payable(player).transfer(transferEth);
        nftContract.mintNFT(player, tokenURI_);
    }

    // For any points: Transfer Ether only
    function transferEther(address player, uint256 points) public onlyOwner {
        require(points > 0, "Points must be greater than zero");
        uint256 transferEth = points * perCorrect; // points * 0.001 ETH
        require(
            address(this).balance >= transferEth,
            "Insufficient contract balance"
        );
        payable(player).transfer(transferEth);
    }

    // Optional: Mint NFT only (if needed separately)
    function mintNFTOnly(
        address player,
        string memory tokenURI_
    ) public onlyOwner {
        nftContract.mintNFT(player, tokenURI_);
    }

    // Allow depositing Ether to fund the contract
    function deposit() public payable {}

    // Event for tracking transfers
    event EtherTransferred(address indexed player, uint256 amount);
    event NFTMinted(address indexed player, uint256 tokenId);
}
