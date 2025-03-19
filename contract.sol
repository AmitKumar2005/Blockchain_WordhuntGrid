// SPDX-License-Identifier: MIT

pragma solidity 0.8.0;

contract transfer {
    uint256 public perCorrect = 1e15;
    mapping(address => uint256) public sender;
    address from;
    address to;

    function senderAdd(address s) public {
        from = s;
    }

    function receiverAdd(address s) public {
        to = s;
    }

    function fund(uint256 points) public view returns (uint256) {
        uint256 transferEth = points * perCorrect;
        return transferEth;
    }
}
