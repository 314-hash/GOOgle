from fastapi import APIRouter
from forecastos import __version__
from forecastos.config import settings
from forecastos.engine.model import get_model_adapter
from forecastos.api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    """System health check endpoint."""
    adapter = get_model_adapter()

    return HealthResponse(
        status="ok",
        version=__version__,
        model_status="ready" if adapter.loaded else "initializing",
        model_name="TimesFM-2.5-Mock" if adapter.use_mock else "TimesFM-2.5",
        is_mock=adapter.use_mock,
        database_connected=True,
        evm_enabled=settings.EVM_ENABLED,
    )
