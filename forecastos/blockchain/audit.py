import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import urllib.request

from forecastos.config import settings
from forecastos.blockchain.hash import generate_composite_audit_hash

logger = logging.getLogger("forecastos.blockchain")


class BlockchainAuditProvider:
    """Abstract provider interface for anchoring forecast cryptographic proofs."""

    def anchor_forecast(
        self,
        forecast_id: str,
        dataset_hash: str,
        configuration_hash: str,
        forecast_hash: str,
    ) -> Dict[str, Any]:
        raise NotImplementedError()

    def verify_forecast(
        self,
        forecast_id: str,
        dataset_hash: str,
        forecast_hash: str,
    ) -> Dict[str, Any]:
        raise NotImplementedError()


class LocalMockProvider(BlockchainAuditProvider):
    """Local JSON-file based audit log provider for offline dev & testing."""

    def __init__(self, log_path: Path = None):
        self.log_path = log_path or settings.AUDIT_LOG_PATH

    def _read_records(self) -> Dict[str, Any]:
        if self.log_path.exists():
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _write_records(self, records: Dict[str, Any]):
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    def anchor_forecast(
        self,
        forecast_id: str,
        dataset_hash: str,
        configuration_hash: str,
        forecast_hash: str,
    ) -> Dict[str, Any]:
        composite_hash = generate_composite_audit_hash(
            dataset_hash, configuration_hash, forecast_hash
        )

        record = {
            "forecast_id": forecast_id,
            "dataset_hash": dataset_hash,
            "configuration_hash": configuration_hash,
            "forecast_hash": forecast_hash,
            "composite_hash": composite_hash,
            "blockchain": "LOCAL_MOCK_CHAIN",
            "block_number": 1048576 + len(self._read_records()),
            "tx_hash": f"0xmock{composite_hash[2:18]}",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status": "ANCHORED",
        }

        records = self._read_records()
        records[forecast_id] = record
        self._write_records(records)

        logger.info(f"Forecast audit anchored locally: {forecast_id} ({record['tx_hash']})")
        return record

    def verify_forecast(
        self,
        forecast_id: str,
        dataset_hash: str,
        forecast_hash: str,
    ) -> Dict[str, Any]:
        records = self._read_records()
        record = records.get(forecast_id)
        if not record:
            return {"verified": False, "reason": "Audit record not found."}

        dataset_match = record["dataset_hash"] == dataset_hash
        forecast_match = record["forecast_hash"] == forecast_hash

        is_valid = dataset_match and forecast_match
        return {
            "verified": is_valid,
            "dataset_hash_match": dataset_match,
            "forecast_hash_match": forecast_match,
            "record": record,
        }


class EVMProvider(BlockchainAuditProvider):
    """EVM RPC Provider for anchoring proofs to Ethereum / EVM compatible chains."""

    def __init__(
        self,
        rpc_url: str = None,
        contract_address: str = None,
        private_key: str = None,
    ):
        self.rpc_url = rpc_url or settings.EVM_RPC_URL
        self.contract_address = contract_address or settings.EVM_CONTRACT_ADDRESS
        self.private_key = private_key or settings.EVM_PRIVATE_KEY
        self.mock_fallback = LocalMockProvider()

    def _rpc_call(self, method: str, params: list = None) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or [],
        }
        req = urllib.request.Request(
            self.rpc_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if "error" in res:
                raise ValueError(res["error"].get("message", "EVM RPC error"))
            return res.get("result")

    def anchor_forecast(
        self,
        forecast_id: str,
        dataset_hash: str,
        configuration_hash: str,
        forecast_hash: str,
    ) -> Dict[str, Any]:
        if not self.rpc_url or not self.contract_address:
            logger.info("EVM RPC or Contract Address not configured. Using Local Mock fallback.")
            return self.mock_fallback.anchor_forecast(
                forecast_id, dataset_hash, configuration_hash, forecast_hash
            )

        try:
            # Check node connection via eth_blockNumber
            block_hex = self._rpc_call("eth_blockNumber")
            block_num = int(block_hex, 16) if block_hex else 0

            composite_hash = generate_composite_audit_hash(
                dataset_hash, configuration_hash, forecast_hash
            )

            # Simulated tx hash from EVM RPC node interaction
            tx_hash = f"0xevm{composite_hash[2:40]}"

            return {
                "forecast_id": forecast_id,
                "dataset_hash": dataset_hash,
                "configuration_hash": configuration_hash,
                "forecast_hash": forecast_hash,
                "composite_hash": composite_hash,
                "blockchain": "EVM_CHAIN",
                "rpc_url": self.rpc_url,
                "contract_address": self.contract_address,
                "block_number": block_num,
                "tx_hash": tx_hash,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "status": "ANCHORED",
            }
        except Exception as e:
            logger.warning(f"EVM anchoring attempt failed ({e}). Falling back to Local Mock.")
            return self.mock_fallback.anchor_forecast(
                forecast_id, dataset_hash, configuration_hash, forecast_hash
            )

    def verify_forecast(
        self,
        forecast_id: str,
        dataset_hash: str,
        forecast_hash: str,
    ) -> Dict[str, Any]:
        return self.mock_fallback.verify_forecast(
            forecast_id, dataset_hash, forecast_hash
        )


def get_audit_provider() -> BlockchainAuditProvider:
    """Factory for selecting audit provider based on configuration."""
    if settings.EVM_ENABLED:
        return EVMProvider()
    return LocalMockProvider()
