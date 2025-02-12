// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract NewsClassification {
    struct News {
        string title;
        bool isFake;
        address reporter;
    }

    struct QueryVerdict {
        string query;
        bool isFake;
    }

    mapping(address => int) public reputation;
    News[] public newsList;
    QueryVerdict[] public queryVerdicts;

    event NewsAdded(string title, bool isFake, address reporter);
    event ReputationUpdated(address user, int newReputation);
    event QueryVerdictAdded(string query, bool isFake);

    constructor() {
        // Initialize the deployer's reputation with 100.
        reputation[msg.sender] = 100;
    }
    
    // Registration: sets reputation to 100 if the account is not yet registered.
    function register() public {
        require(reputation[msg.sender] == 0, "Already registered or reputation nonzero");
        reputation[msg.sender] = 100;
        emit ReputationUpdated(msg.sender, 100);
    }
    
    // Unregister: resets the caller’s reputation to 0.
    function unregister() public {
        require(reputation[msg.sender] != 0, "Not registered");
        reputation[msg.sender] = 0;
        emit ReputationUpdated(msg.sender, 0);
    }

    function addNews(string memory title, bool isFake) public {
        newsList.push(News(title, isFake, msg.sender));
        if (isFake) {
            reputation[msg.sender] -= 10;
        } else {
            reputation[msg.sender] += 5;
        }
        emit NewsAdded(title, isFake, msg.sender);
        emit ReputationUpdated(msg.sender, reputation[msg.sender]);
    }

    function addQueryVerdict(string memory query, bool isFake) public {
        queryVerdicts.push(QueryVerdict(query, isFake));
        emit QueryVerdictAdded(query, isFake);
    }

    function getReputation(address user) public view returns (int) {
        return reputation[user];
    }
    
    // Update reputation function that applies a delta.
    function updateReputation(int delta) public {
        if (reputation[msg.sender] == 0) {
            reputation[msg.sender] = 100;
        }
        reputation[msg.sender] += delta;
        emit ReputationUpdated(msg.sender, reputation[msg.sender]);
    }
}
