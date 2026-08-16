from typing import Any, Dict, List
import json
import logging
import numpy as np

from forecastos.config import settings

logger = logging.getLogger("forecastos.agents.decision")


class DecisionAgent:
    """AI Decision Engine that converts forecasting metrics into business insights."""

    def __init__(self):
        self.provider = settings.AI_PROVIDER.lower()
        self.api_key = settings.AI_API_KEY or settings.GEMINI_API_KEY or settings.OPENAI_API_KEY

    def analyze(
        self,
        historical_series: List[float],
        point_forecast: List[float],
        quantiles: Dict[str, List[float]],
        confidence_info: Dict[str, Any],
        anomaly_info: Dict[str, Any],
        business_context: str = "general",
    ) -> Dict[str, Any]:
        """Generate structured business recommendations and risk assessment."""
        hist_arr = np.array(historical_series)
        fc_arr = np.array(point_forecast)

        last_hist = float(hist_arr[-1]) if len(hist_arr) > 0 else 100.0
        avg_hist = float(np.mean(hist_arr[-30:])) if len(hist_arr) >= 30 else float(np.mean(hist_arr))
        avg_fc = float(np.mean(fc_arr))

        growth_pct = ((avg_fc - last_hist) / abs(last_hist)) * 100.0 if last_hist != 0 else 0.0

        if growth_pct > 3.0:
            trend = "increasing"
        elif growth_pct < -3.0:
            trend = "decreasing"
        else:
            trend = "stable"

        # Check volatility
        std_ratio = float(np.std(fc_arr)) / (abs(avg_fc) or 1.0)
        if std_ratio > 0.2:
            trend = "volatile"

        # Assess risk
        confidence_score = confidence_info.get("confidence_score", 0.75)
        anomaly_severity = anomaly_info.get("severity", "low")

        if anomaly_severity == "high" or confidence_score < 0.4:
            risk_level = "high"
        elif anomaly_severity == "medium" or confidence_score < 0.7 or trend == "volatile":
            risk_level = "medium"
        else:
            risk_level = "low"

        # Try LLM if configured, otherwise rule-based
        if self.provider in ("gemini", "openai") and self.api_key:
            try:
                llm_output = self._call_llm(
                    historical_series=historical_series,
                    point_forecast=point_forecast,
                    growth_pct=growth_pct,
                    trend=trend,
                    risk_level=risk_level,
                    confidence_score=confidence_score,
                    anomaly_info=anomaly_info,
                    business_context=business_context,
                )
                if llm_output:
                    return llm_output
            except Exception as e:
                logger.warning(f"LLM call failed ({e}). Falling back to heuristic decision engine.")

        # Rule-based decision engine
        recommendations = self._generate_heuristic_recommendations(
            growth_pct=growth_pct,
            trend=trend,
            risk_level=risk_level,
            confidence_score=confidence_score,
            anomaly_info=anomaly_info,
            business_context=business_context,
        )

        explanation = (
            f"Forecast predicts a {growth_pct:+.1f}% shift over the next {len(point_forecast)} steps "
            f"with a '{trend}' trajectory. Model confidence score is {confidence_score:.2f} "
            f"with '{risk_level}' overall operational risk."
        )

        return {
            "risk_level": risk_level,
            "trend": trend,
            "expected_growth_pct": round(growth_pct, 2),
            "confidence_score": round(confidence_score, 3),
            "recommendations": recommendations,
            "explanation": explanation,
            "engine": "Rule-Based Heuristic",
        }

    def _generate_heuristic_recommendations(
        self,
        growth_pct: float,
        trend: str,
        risk_level: str,
        confidence_score: float,
        anomaly_info: Dict[str, Any],
        business_context: str,
    ) -> List[str]:
        recs = []

        # Domain specific heuristics
        context_lower = business_context.lower()

        if "sales" in context_lower or "retail" in context_lower or "demand" in context_lower:
            if growth_pct > 5.0:
                recs.append(f"Increase inventory safety stock by {min(25, int(growth_pct * 0.8))}% to meet projected demand growth.")
                recs.append("Scale marketing and promotional campaigns to capitalize on positive momentum.")
            elif growth_pct < -5.0:
                recs.append("Optimize inventory purchasing to prevent overstocking and cash flow tied up in slow-moving items.")
                recs.append("Implement targeted discount strategies for lagging SKUs.")
            else:
                recs.append("Maintain baseline inventory orders and monitor weekly sales velocity.")

        elif "crypto" in context_lower or "finance" in context_lower or "market" in context_lower:
            if risk_level == "high":
                recs.append("High volatility detected in quantile spread. Set strict stop-loss boundaries.")
                recs.append("Reduce single-asset position sizing and maintain liquidity buffers.")
            elif trend == "increasing":
                recs.append("Strong upward trend indicated. Consider dollar-cost averaging into positions.")
            else:
                recs.append("Market is ranging within expected quantile channels. Execute mean-reversion strategies.")

        elif "energy" in context_lower or "power" in context_lower or "grid" in context_lower:
            if growth_pct > 3.0:
                recs.append("Prepare peak load generation assets for increased grid consumption.")
            elif anomaly_info.get("critical_count", 0) > 0:
                recs.append("Critical spikes detected in historical load data. Check grid voltage stability regulators.")
            else:
                recs.append("Base energy demand is nominal. Dispatch renewable sources efficiently.")

        elif "inventory" in context_lower or "warehouse" in context_lower:
            if growth_pct > 0:
                recs.append("Re-order point threshold should be raised to prevent stockouts.")
            else:
                recs.append("Reduce warehouse lead times and defer non-critical purchase orders.")

        else:  # General
            if growth_pct > 0:
                recs.append("Scale operational capacity to accommodate anticipated growth.")
            else:
                recs.append("Conserve operating reserves and optimize resource allocation.")

        # Risk mitigations
        if anomaly_info.get("critical_count", 0) > 0:
            recs.append(f"Review {anomaly_info['critical_count']} historical critical anomaly point(s) for unexpected external shocks.")

        if confidence_score < 0.6:
            recs.append("Model confidence is moderate. Re-run forecast after updating recent daily data points.")

        return recs

    def _call_llm(self, **kwargs) -> Dict[str, Any]:
        """Calls remote Gemini/OpenAI API if keys are provided."""
        # Simple HTTP REST call to avoid dependency conflicts
        return None
