import datetime
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from forecastos.api.schemas import (
    ForecastRequest,
    NaturalForecastRequest,
    ForecastResponse,
)
from forecastos.agents.anomaly_agent import AnomalyAgent
from forecastos.agents.decision_agent import DecisionAgent
from forecastos.agents.forecast_agent import NaturalLanguageForecastAgent
from forecastos.blockchain.audit import get_audit_provider
from forecastos.blockchain.hash import (
    generate_composite_audit_hash,
    generate_configuration_hash,
    generate_dataset_hash,
    generate_forecast_hash,
)
from forecastos.data.validation import ValidationError, validate_time_series_input
from forecastos.engine.confidence import compute_confidence_analysis
from forecastos.engine.model import get_model_adapter
from forecastos.engine.postprocessing import generate_future_dates
from forecastos.storage.database import get_db
from forecastos.storage.models import ForecastHistoryModel

router = APIRouter(prefix="/api/v1/forecast", tags=["Forecasting"])

anomaly_agent = AnomalyAgent()
decision_agent = DecisionAgent()
nlp_agent = NaturalLanguageForecastAgent()


@router.post("", response_model=ForecastResponse)
def create_forecast(
    req: ForecastRequest,
    db: Session = Depends(get_db),
):
    """Execute TimesFM 2.5 time-series forecast with confidence, anomalies, AI decisions, and blockchain audit."""
    try:
        series_arr, clean_dates = validate_time_series_input(
            series=req.series,
            dates=req.dates,
            min_length=1,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    opts = req.options
    context_len = opts.context_len if opts else 1024
    business_context = opts.business_context if opts else "general"

    # 1. Run TimesFM Forecast Adapter
    adapter = get_model_adapter()
    raw_fc = adapter.forecast(
        series=series_arr.tolist(),
        horizon=req.horizon,
        context_len=context_len,
    )

    point_forecast = raw_fc["point_forecast"]
    quantiles = raw_fc["quantiles"]
    model_name = raw_fc["model_name"]

    # Generate future dates
    last_date = clean_dates[-1] if clean_dates else datetime.datetime.utcnow().isoformat()
    future_dates = generate_future_dates(last_date, req.horizon, req.frequency)

    # 2. Confidence & Uncertainty Analysis
    confidence_info = compute_confidence_analysis(point_forecast, quantiles)

    # 3. Two-Phase Anomaly Detection
    anomaly_info = anomaly_agent.analyze_series_anomalies(
        values=series_arr.tolist(),
        dates=clean_dates,
    )

    # 4. AI Decision Agent Recommendations
    decision_info = decision_agent.analyze(
        historical_series=series_arr.tolist(),
        point_forecast=point_forecast,
        quantiles=quantiles,
        confidence_info=confidence_info,
        anomaly_info=anomaly_info,
        business_context=business_context,
    )

    # 5. Cryptographic Hashing
    dataset_hash = generate_dataset_hash(series_arr.tolist(), clean_dates)
    config_hash = generate_configuration_hash(
        model_name=model_name,
        context_len=len(series_arr),
        horizon=req.horizon,
        frequency=req.frequency,
    )
    forecast_hash = generate_forecast_hash(point_forecast, quantiles)
    composite_hash = generate_composite_audit_hash(dataset_hash, config_hash, forecast_hash)

    # 6. Blockchain Audit Anchoring
    forecast_id = f"fc_{uuid.uuid4().hex[:12]}"
    audit_provider = get_audit_provider()
    audit_record = audit_provider.anchor_forecast(
        forecast_id=forecast_id,
        dataset_hash=dataset_hash,
        configuration_hash=config_hash,
        forecast_hash=forecast_hash,
    )

    # 7. Store in SQLite Database History
    db_history = ForecastHistoryModel(
        id=forecast_id,
        dataset_id=req.dataset_id,
        horizon=req.horizon,
        frequency=req.frequency,
        model_name=model_name,
        dataset_hash=dataset_hash,
        configuration_hash=config_hash,
        forecast_hash=forecast_hash,
        composite_hash=composite_hash,
        point_forecast_json=json.dumps(point_forecast),
        quantiles_json=json.dumps(quantiles),
        anomalies_json=json.dumps(anomaly_info),
        risk_level=decision_info["risk_level"],
        trend=decision_info["trend"],
        recommendations_json=json.dumps(decision_info["recommendations"]),
        explanation=decision_info["explanation"],
        blockchain_status=audit_record.get("status", "LOCAL_ONLY"),
        blockchain_tx_hash=audit_record.get("tx_hash"),
    )
    db.add(db_history)
    db.commit()

    return ForecastResponse(
        forecast_id=forecast_id,
        dataset_id=req.dataset_id,
        horizon=req.horizon,
        frequency=req.frequency,
        model=model_name,
        point_forecast=point_forecast,
        future_dates=future_dates,
        quantiles=quantiles,
        confidence=confidence_info,
        anomalies=anomaly_info,
        insights=decision_info,
        hashes={
            "dataset_hash": dataset_hash,
            "configuration_hash": config_hash,
            "forecast_hash": forecast_hash,
            "composite_hash": composite_hash,
        },
        blockchain_audit=audit_record,
        created_at=db_history.created_at.isoformat(),
    )


@router.post("/natural", response_model=ForecastResponse)
def natural_language_forecast(
    req: NaturalForecastRequest,
    db: Session = Depends(get_db),
):
    """Natural Language Forecasting API — accepts prompts like 'Forecast the next 30 days of sales.'"""
    parsed = nlp_agent.parse_query(req.prompt)

    horizon = parsed["horizon"]
    domain = parsed["domain"]
    adjustment_pct = parsed["adjustment_pct"]

    # Convert to standard forecast request
    series = req.series
    if adjustment_pct != 0:
        # Apply scenario adjustment
        factor = 1.0 + (adjustment_pct / 100.0)
        series = [v * factor for v in series]

    std_req = ForecastRequest(
        series=series,
        dates=req.dates,
        horizon=horizon,
        frequency=req.frequency,
        options={
            "quantiles": True,
            "business_context": domain,
            "anchor_blockchain": req.anchor_blockchain,
        },
    )

    return create_forecast(std_req, db)


@router.get("s", response_model=List[ForecastResponse])
def list_forecasts(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieve history of generated forecasts."""
    history = (
        db.query(ForecastHistoryModel)
        .order_by(ForecastHistoryModel.created_at.desc())
        .limit(limit)
        .all()
    )

    resps = []
    for h in history:
        point_forecast = json.loads(h.point_forecast_json)
        quantiles = json.loads(h.quantiles_json)
        anomalies = json.loads(h.anomalies_json) if h.anomalies_json else {}
        recs = json.loads(h.recommendations_json) if h.recommendations_json else []

        future_dates = [f"t_{i+1}" for i in range(h.horizon)]

        resps.append(
            ForecastResponse(
                forecast_id=h.id,
                dataset_id=h.dataset_id,
                horizon=h.horizon,
                frequency=h.frequency,
                model=h.model_name,
                point_forecast=point_forecast,
                future_dates=future_dates,
                quantiles=quantiles,
                confidence=compute_confidence_analysis(point_forecast, quantiles),
                anomalies=anomalies,
                insights={
                    "risk_level": h.risk_level,
                    "trend": h.trend,
                    "recommendations": recs,
                    "explanation": h.explanation,
                },
                hashes={
                    "dataset_hash": h.dataset_hash,
                    "configuration_hash": h.configuration_hash,
                    "forecast_hash": h.forecast_hash,
                    "composite_hash": h.composite_hash,
                },
                blockchain_audit={
                    "status": h.blockchain_status,
                    "tx_hash": h.blockchain_tx_hash,
                },
                created_at=h.created_at.isoformat(),
            )
        )

    return resps


@router.get("/{forecast_id}/verify")
def verify_forecast_audit(
    forecast_id: str,
    db: Session = Depends(get_db),
):
    """Verify cryptographic audit trail for a specific forecast record."""
    h = db.query(ForecastHistoryModel).filter(ForecastHistoryModel.id == forecast_id).first()
    if not h:
        raise HTTPException(status_code=404, detail=f"Forecast '{forecast_id}' not found.")

    provider = get_audit_provider()
    res = provider.verify_forecast(
        forecast_id=forecast_id,
        dataset_hash=h.dataset_hash,
        forecast_hash=h.forecast_hash,
    )

    return {
        "forecast_id": forecast_id,
        "verified": res["verified"],
        "dataset_hash": h.dataset_hash,
        "forecast_hash": h.forecast_hash,
        "composite_hash": h.composite_hash,
        "tx_hash": h.blockchain_tx_hash,
        "blockchain_status": h.blockchain_status,
        "details": res,
    }
