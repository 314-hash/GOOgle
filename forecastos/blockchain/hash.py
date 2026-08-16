from typing import Any, Dict, List
import hashlib
import json


def compute_sha256(data: str) -> str:
    """Compute 0x-prefixed SHA256 hex string."""
    return "0x" + hashlib.sha256(data.encode("utf-8")).hexdigest()


def generate_dataset_hash(values: List[float], dates: List[str] = None) -> str:
    """Deterministically hash time series values and timestamps."""
    canonical_list = []
    if dates and len(dates) == len(values):
        for d, v in zip(dates, values):
            canonical_list.append(f"{d}:{v:.6f}")
    else:
        for i, v in enumerate(values):
            canonical_list.append(f"{i}:{v:.6f}")

    raw_str = "|".join(canonical_list)
    return compute_sha256(raw_str)


def generate_configuration_hash(
    model_name: str,
    context_len: int,
    horizon: int,
    frequency: str = "D",
) -> str:
    """Deterministically hash model run configuration."""
    config_dict = {
        "model_name": model_name,
        "context_len": context_len,
        "horizon": horizon,
        "frequency": frequency,
    }
    raw_str = json.dumps(config_dict, sort_keys=True)
    return compute_sha256(raw_str)


def generate_forecast_hash(
    point_forecast: List[float],
    quantiles: Dict[str, List[float]] = None,
) -> str:
    """Deterministically hash forecast outputs."""
    pf_str = ",".join([f"{v:.6f}" for v in point_forecast])

    if quantiles:
        q_keys = sorted(quantiles.keys())
        q_parts = []
        for k in q_keys:
            vals_str = ",".join([f"{v:.6f}" for v in quantiles[k]])
            q_parts.append(f"{k}:{vals_str}")
        q_str = ";".join(q_parts)
        raw_str = f"PF:[{pf_str}]|Q:[{q_str}]"
    else:
        raw_str = f"PF:[{pf_str}]"

    return compute_sha256(raw_str)


def generate_composite_audit_hash(
    dataset_hash: str,
    configuration_hash: str,
    forecast_hash: str,
) -> str:
    """Generate master composite hash representing the full auditable execution state."""
    raw_str = f"{dataset_hash}:{configuration_hash}:{forecast_hash}"
    return compute_sha256(raw_str)
