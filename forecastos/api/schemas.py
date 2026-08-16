from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ForecastRequestOptions(BaseModel):
    quantiles: bool = True
    context_len: int = Field(default=1024, ge=1, le=16384)
    business_context: str = Field(default="general", description="e.g. sales, crypto, energy, inventory")
    anchor_blockchain: bool = False


class ForecastRequest(BaseModel):
    series: List[float] = Field(..., description="Context time-series values")
    dates: Optional[List[str]] = Field(default=None, description="ISO timestamp strings")
    horizon: int = Field(default=30, ge=1, le=1024, description="Forecast horizon steps")
    frequency: str = Field(default="D", description="Time-series frequency code (e.g. D, H, M)")
    dataset_id: Optional[str] = Field(default=None, description="Optional uploaded dataset ID")
    options: Optional[ForecastRequestOptions] = Field(default_factory=ForecastRequestOptions)


class NaturalForecastRequest(BaseModel):
    prompt: str = Field(..., description="Natural language request (e.g., 'Forecast the next 30 days of sales.')")
    series: List[float] = Field(..., description="Context time-series values")
    dates: Optional[List[str]] = Field(default=None, description="ISO timestamp strings")
    frequency: str = Field(default="D")
    anchor_blockchain: bool = False


class ForecastResponse(BaseModel):
    forecast_id: str
    dataset_id: Optional[str] = None
    horizon: int
    frequency: str
    model: str
    point_forecast: List[float]
    future_dates: List[str]
    quantiles: Dict[str, List[float]]
    confidence: Dict[str, Any]
    anomalies: Dict[str, Any]
    insights: Dict[str, Any]
    hashes: Dict[str, str]
    blockchain_audit: Dict[str, Any]
    created_at: str


class DatasetResponse(BaseModel):
    id: str
    name: str
    filename: Optional[str]
    row_count: int
    frequency: str
    start_date: Optional[str]
    end_date: Optional[str]
    dataset_hash: str
    created_at: str


class DatasetListResponse(BaseModel):
    datasets: List[DatasetResponse]
    total: int


class HealthResponse(BaseModel):
    status: str
    version: str
    model_status: str
    model_name: str
    is_mock: bool
    database_connected: bool
    evm_enabled: bool
