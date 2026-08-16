// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IForecastAuditRegistry
 * @notice Interface for the ForecastOS Cryptographic Audit Registry.
 */
interface IForecastAuditRegistry {
    struct AuditRecord {
        bytes32 forecastId;
        bytes32 datasetHash;
        bytes32 configurationHash;
        bytes32 forecastHash;
        bytes32 compositeHash;
        address recorder;
        uint256 timestamp;
        uint256 blockNumber;
    }

    event ForecastAuditAnchored(
        bytes32 indexed forecastId,
        bytes32 indexed datasetHash,
        bytes32 configurationHash,
        bytes32 forecastHash,
        bytes32 compositeHash,
        address indexed recorder,
        uint256 timestamp,
        uint256 blockNumber
    );

    function anchorForecast(
        bytes32 forecastId,
        bytes32 datasetHash,
        bytes32 configurationHash,
        bytes32 forecastHash,
        bytes32 compositeHash
    ) external;

    function verifyForecast(
        bytes32 forecastId,
        bytes32 datasetHash,
        bytes32 forecastHash
    ) external view returns (bool isVerified, address recorder, uint256 timestamp, uint256 blockNumber);

    function getAuditRecord(bytes32 forecastId) external view returns (AuditRecord memory);

    function getTotalAnchoredCount() external view returns (uint256);

    function getForecastIdAtIndex(uint256 index) external view returns (bytes32);
}
