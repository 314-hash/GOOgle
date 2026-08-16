import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from forecastos.storage.database import Base


class DatasetModel(Base):
    __tablename__ = "datasets"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=True)
    row_count = Column(Integer, nullable=False)
    frequency = Column(String(20), nullable=False, default="D")
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    dataset_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


class ForecastHistoryModel(Base):
    __tablename__ = "forecast_history"

    id = Column(String(64), primary_key=True, index=True)
    dataset_id = Column(String(64), nullable=True, index=True)
    horizon = Column(Integer, nullable=False)
    frequency = Column(String(20), nullable=False, default="D")
    model_name = Column(String(100), nullable=False, default="TimesFM-2.5")

    # Hashes
    dataset_hash = Column(String(128), nullable=False)
    configuration_hash = Column(String(128), nullable=False)
    forecast_hash = Column(String(128), nullable=False)
    composite_hash = Column(String(128), nullable=False)

    # Forecast Outputs stored as JSON strings
    point_forecast_json = Column(Text, nullable=False)
    quantiles_json = Column(Text, nullable=False)
    anomalies_json = Column(Text, nullable=True)

    # AI Decision Outputs
    risk_level = Column(String(20), nullable=False, default="medium")
    trend = Column(String(50), nullable=False, default="stable")
    recommendations_json = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)

    # Blockchain Audit Metadata
    blockchain_status = Column(String(50), nullable=False, default="LOCAL_ONLY")  # LOCAL_ONLY, ANCHORED, FAILED
    blockchain_tx_hash = Column(String(128), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
