// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ForecastAuditRegistry
 * @dev On-chain registry for anchoring TimesFM forecast proofs and datasets.
 */
contract ForecastAuditRegistry {
    event AuditAnchored(
        string indexed forecastId,
        string datasetHash,
        string configurationHash,
        string forecastHash,
        string compositeHash,
        address indexed recorder,
        uint256 timestamp
    );

    struct AuditRecord {
        string forecastId;
        string datasetHash;
        string configurationHash;
        string forecastHash;
        string compositeHash;
        address recorder;
        uint256 timestamp;
        uint256 blockNumber;
    }

    // Mapping from forecastId => AuditRecord
    mapping(string => AuditRecord) public records;

    /**
     * @dev Anchors a forecast proof onto the blockchain.
     */
    function anchorForecast(
        string memory forecastId,
        string memory datasetHash,
        string memory configurationHash,
        string memory forecastHash,
        string memory compositeHash
    ) external {
        require(bytes(records[forecastId].forecastId).length == 0, "Forecast ID already anchored");

        records[forecastId] = AuditRecord({
            forecastId: forecastId,
            datasetHash: datasetHash,
            configurationHash: configurationHash,
            forecastHash: forecastHash,
            compositeHash: compositeHash,
            recorder: msg.sender,
            timestamp: block.timestamp,
            blockNumber: block.number
        });

        emit AuditAnchored(
            forecastId,
            datasetHash,
            configurationHash,
            forecastHash,
            compositeHash,
            msg.sender,
            block.timestamp
        );
    }

    /**
     * @dev Verifies if a given dataset and forecast hash match the anchored record.
     */
    function verifyForecast(
        string memory forecastId,
        string memory datasetHash,
        string memory forecastHash
    ) external view returns (bool isVerified, address recorder, uint256 timestamp) {
        AuditRecord memory rec = records[forecastId];
        require(bytes(rec.forecastId).length > 0, "Record does not exist");

        bool datasetMatches = keccak256(bytes(rec.datasetHash)) == keccak256(bytes(datasetHash));
        bool forecastMatches = keccak256(bytes(rec.forecastHash)) == keccak256(bytes(forecastHash));

        return (datasetMatches && forecastMatches, rec.recorder, rec.timestamp);
    }
}
