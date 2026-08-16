import pytest
from forecastos.blockchain.deploy_and_verify import EVMSmartContractVerifier


def test_solidity_contract_compilation():
    verifier = EVMSmartContractVerifier()
    compilation = verifier.compile_contract()
    assert compilation["contract_name"] == "ForecastAuditRegistry"
    assert compilation["source_lines"] > 50
    assert compilation["bytecode_hash"].startswith("0x")


def test_solidity_contract_deployment():
    verifier = EVMSmartContractVerifier()
    addr = verifier.deploy()
    assert addr.startswith("0x")
    assert len(addr) == 42


def test_anchor_and_verify_forecast_on_chain():
    verifier = EVMSmartContractVerifier()
    verifier.deploy()

    forecast_id = "fc_test_999"
    dataset_hash = "0xds111111111111111111111111111111"
    config_hash = "0xcfg2222222222222222222222222222"
    forecast_hash = "0xfc3333333333333333333333333333"
    composite_hash = "0xcomp44444444444444444444444444"

    # Anchor
    tx_rec = verifier.anchor_forecast_on_chain(
        forecast_id, dataset_hash, config_hash, forecast_hash, composite_hash
    )
    assert tx_rec["txHash"].startswith("0x")
    assert verifier.total_count == 1

    # Verify matching hash
    v_res = verifier.verify_forecast_on_chain(forecast_id, dataset_hash, forecast_hash)
    assert v_res["isVerified"] is True
    assert v_res["recorder"] == verifier.admin_address

    # Verify mismatched hash fails
    v_mismatch = verifier.verify_forecast_on_chain(forecast_id, "0xWRONGDATASETHASH", forecast_hash)
    assert v_mismatch["isVerified"] is False


def test_duplicate_anchor_raises_error():
    verifier = EVMSmartContractVerifier()
    verifier.deploy()

    verifier.anchor_forecast_on_chain("fc_dup", "0xds", "0xcfg", "0xfc", "0xcomp")
    with pytest.raises(ValueError):
        verifier.anchor_forecast_on_chain("fc_dup", "0xds", "0xcfg", "0xfc", "0xcomp")
