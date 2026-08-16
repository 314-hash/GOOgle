from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from forecastos.agents.anomaly_agent import AnomalyAgent
from forecastos.agents.decision_agent import DecisionAgent
from forecastos.agents.forecast_agent import NaturalLanguageForecastAgent
from forecastos.blockchain.deploy_and_verify import EVMSmartContractVerifier
from forecastos.data.validation import validate_time_series_input
from forecastos.engine.confidence import compute_confidence_analysis
from forecastos.engine.model import get_model_adapter
from forecastos.storage.database import get_db

router = APIRouter(prefix="/api/v1/chat", tags=["WebChat"])

nlp_agent = NaturalLanguageForecastAgent()
anomaly_agent = AnomalyAgent()
decision_agent = DecisionAgent()
contract_verifier = EVMSmartContractVerifier()


class ChatMessage(BaseModel):
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Text content")


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message input")
    history: Optional[List[ChatMessage]] = Field(default_factory=list)
    series: Optional[List[float]] = Field(default=None, description="Optional time series data context")
    dates: Optional[List[str]] = Field(default=None)


class ChatResponse(BaseModel):
    reply: str
    intent: str
    action_data: Optional[Dict[str, Any]] = None
    suggestions: List[str]


def generate_sample_series():
    import math
    values, dates = [], []
    val = 120.0
    for i in range(60):
        val = val + 0.4 + math.sin(i * 0.8) * 3.5
        values.append(round(val, 2))
        dates.append(f"2026-01-{(i%30)+1:02d}")
    return values, dates


@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse)
def handle_chat_message(

    req: ChatRequest,
    db: Session = Depends(get_db),
):
    """WebChat conversational endpoint — routes questions to TimesFM, Anomaly, Decision, or Blockchain agents."""
    msg = req.message.strip().lower()

    # Default fallback sample data if none provided
    series = req.series
    dates = req.dates
    if not series or len(series) < 3:
        series, dates = generate_sample_series()

    # Intent 1: Blockchain / Smart Contract query
    if any(k in msg for k in ["contract", "abi", "blockchain", "verify", "solidity", "proof", "address"]):
        compiled = contract_verifier.compile_contract()
        deployed_addr = contract_verifier.deploy()

        reply = (
            f"🛡️ **ForecastOS Smart Contract Info**\n\n"
            f"• **Contract Name**: `{compiled['contract_name']}`\n"
            f"• **EVM Address**: `{deployed_addr}`\n"
            f"• **Admin Address**: `{contract_verifier.admin_address}`\n"
            f"• **Bytecode SHA256**: `{compiled['bytecode_hash'][:18]}...`\n\n"
            f"All forecasts generate SHA256 cryptographic proofs anchored to `ForecastAuditRegistry.sol`."
        )

        return ChatResponse(
            reply=reply,
            intent="blockchain_info",
            action_data={
                "contract_address": deployed_addr,
                "abi": compiled["abi"],
            },
            suggestions=["Forecast sales for next 30 days", "Check for anomalies", "Explain risk model"],
        )

    # Intent 2: Anomaly Query
    if any(k in msg for k in ["anomaly", "anomalies", "outlier", "spike", "drop", "suspicious"]):
        anomaly_info = anomaly_agent.analyze_series_anomalies(series, dates)
        count = anomaly_info["anomaly_count"]
        severity = anomaly_info["severity"]

        reply = (
            f"🔍 **Two-Phase Anomaly Detection Analysis**\n\n"
            f"• **Total Anomalies Detected**: {count}\n"
            f"• **Critical Count**: {anomaly_info['critical_count']}\n"
            f"• **Warning Count**: {anomaly_info['warning_count']}\n"
            f"• **Overall Severity**: `{severity.upper()}`\n\n"
        )
        if count > 0:
            reply += "Sample Anomaly: " + str(anomaly_info["anomalies"][0])
        else:
            reply += "No unexpected spikes or residual Z-score outliers found in the context series."

        return ChatResponse(
            reply=reply,
            intent="anomaly_check",
            action_data=anomaly_info,
            suggestions=["Forecast next 30 days", "Get business recommendations", "Show smart contract"],
        )

    # Intent 3: Recommendations / Decision Query
    if any(k in msg for k in ["recommend", "decision", "advice", "what should i do", "action", "risk"]):
        adapter = get_model_adapter()
        raw_fc = adapter.forecast(series=series, horizon=30)
        confidence = compute_confidence_analysis(raw_fc["point_forecast"], raw_fc["quantiles"])
        anomaly_info = anomaly_agent.analyze_series_anomalies(series, dates)

        decision_info = decision_agent.analyze(
            historical_series=series,
            point_forecast=raw_fc["point_forecast"],
            quantiles=raw_fc["quantiles"],
            confidence_info=confidence,
            anomaly_info=anomaly_info,
            business_context="sales",
        )

        recs_str = "\n".join([f"• {r}" for r in decision_info["recommendations"]])
        reply = (
            f"💡 **AI Decision Agent Insights**\n\n"
            f"**Operational Risk**: `{decision_info['risk_level'].upper()}`\n"
            f"**Predicted Trend**: `{decision_info['trend'].upper()}` ({decision_info['expected_growth_pct']:+.1f}%)\n\n"
            f"**Recommended Actions**:\n{recs_str}"
        )

        return ChatResponse(
            reply=reply,
            intent="decision_analysis",
            action_data=decision_info,
            suggestions=["Forecast 30 days", "Verify contract proof", "Check anomalies"],
        )

    # Intent 4: Natural Language Forecast Request (Default)
    parsed = nlp_agent.parse_query(req.message)
    horizon = parsed["horizon"]
    domain = parsed["domain"]

    adapter = get_model_adapter()
    raw_fc = adapter.forecast(series=series, horizon=horizon)
    confidence = compute_confidence_analysis(raw_fc["point_forecast"], raw_fc["quantiles"])
    anomaly_info = anomaly_agent.analyze_series_anomalies(series, dates)
    decision_info = decision_agent.analyze(
        historical_series=series,
        point_forecast=raw_fc["point_forecast"],
        quantiles=raw_fc["quantiles"],
        confidence_info=confidence,
        anomaly_info=anomaly_info,
        business_context=domain,
    )

    avg_fc = sum(raw_fc["point_forecast"]) / len(raw_fc["point_forecast"])

    reply = (
        f"📈 **TimesFM 2.5 Forecast Executed!**\n\n"
        f"• **Horizon**: {horizon} steps ({domain.capitalize()} domain)\n"
        f"• **Average Predicted Value**: `{avg_fc:.2f}`\n"
        f"• **Confidence Score**: `{confidence['confidence_score']*100:.1f}%` ({confidence['uncertainty_level']} uncertainty)\n"
        f"• **Risk Rating**: `{decision_info['risk_level'].upper()}`\n\n"
        f"**Primary Action**: {decision_info['recommendations'][0] if decision_info['recommendations'] else 'Maintain current ops.'}"
    )

    return ChatResponse(
        reply=reply,
        intent="forecast_execution",
        action_data={
            "horizon": horizon,
            "point_forecast": raw_fc["point_forecast"],
            "quantiles": raw_fc["quantiles"],
            "confidence": confidence,
            "insights": decision_info,
        },
        suggestions=["Detect anomalies", "Verify smart contract", "What happens if sales drop 20%?"],
    )
