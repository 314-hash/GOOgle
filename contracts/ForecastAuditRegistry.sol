// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./IForecastAuditRegistry.sol";

/**
 * @title ForecastAuditRegistry
 * @notice Production-ready immutable on-chain registry for ForecastOS cryptographic audit proofs.
 * @dev Stores Keccak256 / SHA256 hashes of time-series datasets, model configurations, and prediction outputs.
 */
contract ForecastAuditRegistry is IForecastAuditRegistry {
    address public admin;
    bool public paused;

    // Role mapping
    mapping(address => bool) public authorizedRecorders;

    // Mapping from forecastId => AuditRecord
    mapping(bytes32 => AuditRecord) private _records;

    // List of all forecast IDs for enumeration
    bytes32[] private _allForecastIds;

    modifier onlyAdmin() {
        require(msg.sender == admin, "Caller is not admin");
        _;
    }

    modifier onlyAuthorized() {
        require(msg.sender == admin || authorizedRecorders[msg.sender], "Caller is not authorized to anchor");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

    constructor(address _admin) {
        require(_admin != address(0), "Invalid admin address");
        admin = _admin;
        authorizedRecorders[_admin] = true;
    }

    /**
     * @notice Set authorized status for a recorder address.
     */
    function setAuthorizedRecorder(address recorder, bool authorized) external onlyAdmin {
        require(recorder != address(0), "Invalid recorder address");
        authorizedRecorders[recorder] = authorized;
    }

    /**
     * @notice Toggle emergency pause state.
     */
    function setPaused(bool _paused) external onlyAdmin {
        paused = _paused;
    }

    /**
     * @notice Anchor a new forecast cryptographic audit proof onto the blockchain.
     */
    function anchorForecast(
        bytes32 forecastId,
        bytes32 datasetHash,
        bytes32 configurationHash,
        bytes32 forecastHash,
        bytes32 compositeHash
    ) external override onlyAuthorized whenNotPaused {
        require(forecastId != bytes32(0), "Invalid forecastId");
        require(datasetHash != bytes32(0), "Invalid datasetHash");
        require(forecastHash != bytes32(0), "Invalid forecastHash");
        require(_records[forecastId].timestamp == 0, "Forecast ID already registered");

        AuditRecord memory record = AuditRecord({
            forecastId: forecastId,
            datasetHash: datasetHash,
            configurationHash: configurationHash,
            forecastHash: forecastHash,
            compositeHash: compositeHash,
            recorder: msg.sender,
            timestamp: block.timestamp,
            blockNumber: block.number
        });

        _records[forecastId] = record;
        _allForecastIds.push(forecastId);

        emit ForecastAuditAnchored(
            forecastId,
            datasetHash,
            configurationHash,
            forecastHash,
            compositeHash,
            msg.sender,
            block.timestamp,
            block.number
        );
    }

    /**
     * @notice Verify if a provided dataset and forecast hash match the anchored record.
     */
    function verifyForecast(
        bytes32 forecastId,
        bytes32 datasetHash,
        bytes32 forecastHash
    ) external view override returns (bool isVerified, address recorder, uint256 timestamp, uint256 blockNumber) {
        AuditRecord memory rec = _records[forecastId];
        if (rec.timestamp == 0) {
            return (false, address(0), 0, 0);
        }

        bool datasetMatches = rec.datasetHash == datasetHash;
        bool forecastMatches = rec.forecastHash == forecastHash;

        return (datasetMatches && forecastMatches, rec.recorder, rec.timestamp, rec.blockNumber);
    }

    /**
     * @notice Get complete audit record for a forecast ID.
     */
    function getAuditRecord(bytes32 forecastId) external view override returns (AuditRecord memory) {
        require(_records[forecastId].timestamp > 0, "Record does not exist");
        return _records[forecastId];
    }

    /**
     * @notice Total number of anchored forecasts.
     */
    function getTotalAnchoredCount() external view override returns (uint256) {
        return _allForecastIds.length;
    }

    /**
     * @notice Get forecast ID at specific index.
     */
    function getForecastIdAtIndex(uint256 index) external view override returns (bytes32) {
        require(index < _allForecastIds.length, "Index out of bounds");
        return _allForecastIds[index];
    }
}
