from forecastos.blockchain.audit import LocalMockProvider
from forecastos.blockchain.hash import (
    generate_composite_audit_hash,
    generate_configuration_hash,
    generate_dataset_hash,
    generate_forecast_hash,
)


def test_deterministic_hashes():
    h1 = generate_dataset_hash([10.0, 20.0], ["2026-01-01", "2026-01-02"])
    h2 = generate_dataset_hash([10.0, 20.0], ["2026-01-01", "2026-01-02"])
    assert h1 == h2
    assert h1.startswith("0x")

    cfg1 = generate_configuration_hash("TimesFM-2.5", 100, 30)
    cfg2 = generate_configuration_hash("TimesFM-2.5", 100, 30)
    assert cfg1 == cfg2

    fc1 = generate_forecast_hash([1.0, 2.0], {"q10": [0.9, 1.9]})
    fc2 = generate_forecast_hash([1.0, 2.0], {"q10": [0.9, 1.9]})
    assert fc1 == fc2


def test_local_mock_audit_provider(tmp_path):
    log_file = tmp_path / "test_audit.json"
    provider = LocalMockProvider(log_path=log_file)

    d_hash = generate_dataset_hash([1.0, 2.0])
    c_hash = generate_configuration_hash("TimesFM-2.5", 2, 5)
    f_hash = generate_forecast_hash([2.1, 2.2])

    rec = provider.anchor_forecast("fc_test1", d_hash, c_hash, f_hash)
    assert rec["status"] == "ANCHORED"

    verify_res = provider.verify_forecast("fc_test1", d_hash, f_hash)
    assert verify_res["verified"] is True
