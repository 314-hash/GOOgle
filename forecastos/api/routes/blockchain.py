from fastapi import APIRouter
from forecastos.config import settings
from forecastos.blockchain.deploy_and_verify import EVMSmartContractVerifier

router = APIRouter(prefix="/api/v1/blockchain", tags=["Blockchain"])

verifier = EVMSmartContractVerifier()
compiled_info = verifier.compile_contract()
deployed_address = verifier.deploy()


@router.get("/contract-info")
def get_contract_info():
    """Retrieve deployed smart contract metadata, address, and ABI."""
    return {
        "contract_name": compiled_info["contract_name"],
        "contract_address": settings.EVM_CONTRACT_ADDRESS or deployed_address,
        "admin_address": verifier.admin_address,
        "rpc_url": settings.EVM_RPC_URL,
        "evm_enabled": settings.EVM_ENABLED,
        "bytecode_hash": compiled_info["bytecode_hash"],
        "abi": compiled_info["abi"],
    }
