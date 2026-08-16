import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    # Model Configuration
    TIMESFM_MODEL_ID: str = os.getenv("TIMESFM_MODEL_ID", "google/timesfm-2.5-200m-pytorch")
    TIMESFM_MOCK: bool = os.getenv("TIMESFM_MOCK", "true").lower() in ("true", "1", "yes")
    DEFAULT_CONTEXT_LEN: int = int(os.getenv("DEFAULT_CONTEXT_LEN", "1024"))
    DEFAULT_HORIZON: int = int(os.getenv("DEFAULT_HORIZON", "30"))

    # Serverless Environment Detection
    IS_VERCEL: bool = os.getenv("VERCEL") is not None or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:////tmp/forecastos.db" if (os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")) else "sqlite:///./forecastos.db"
    )

    # Blockchain Configuration
    EVM_ENABLED: bool = os.getenv("EVM_ENABLED", "false").lower() in ("true", "1", "yes")
    EVM_RPC_URL: str = os.getenv("EVM_RPC_URL", "http://127.0.0.1:8545")
    EVM_PRIVATE_KEY: str = os.getenv("EVM_PRIVATE_KEY", "")
    EVM_CONTRACT_ADDRESS: str = os.getenv("EVM_CONTRACT_ADDRESS", "")

    # AI Decision Engine Configuration
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock")  # "mock", "gemini", "openai"
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("AI_API_KEY", ""))
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", os.getenv("AI_API_KEY", ""))

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

    # Storage paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    AUDIT_LOG_PATH: Path = (
        Path("/tmp/forecastos_audit_log.json")
        if (os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
        else BASE_DIR / "forecastos_audit_log.json"
    )


settings = Settings()

