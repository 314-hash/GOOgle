from typing import Any, Dict, List
import numpy as np


class AnomalyAgent:
    """Two-Phase Anomaly Detection Agent for Context and Forecast series."""

    CRITICAL_Z = 2.5
    WARNING_Z = 1.8

    def detect_context_anomalies(
        self,
        values: List[float],
        dates: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """Phase 1: Linear detrending + Z-score anomaly detection on historical context.

        Returns list of anomaly records with date, value, trend, residual, z_score, severity.
        """
        arr = np.array(values, dtype=np.float64)
        n = len(arr)
        if n < 3:
            return []

        idx = np.arange(n, dtype=np.float64)

        try:
            coeffs = np.polyfit(idx, arr, 1)
            trend_line = np.polyval(coeffs, idx)
        except Exception:
            trend_line = np.full(n, np.mean(arr))

        residuals = arr - trend_line
        res_std = float(np.std(residuals)) or 1.0

        records = []
        for i in range(n):
            v = float(arr[i])
            t = float(trend_line[i])
            r = float(residuals[i])
            z = r / res_std if res_std > 0 else 0.0

            abs_z = abs(z)
            if abs_z >= self.CRITICAL_Z:
                severity = "CRITICAL"
            elif abs_z >= self.WARNING_Z:
                severity = "WARNING"
            else:
                severity = "NORMAL"

            if severity != "NORMAL":
                records.append(
                    {
                        "step": i,
                        "date": dates[i] if dates and i < len(dates) else f"t_{i}",
                        "value": round(v, 4),
                        "trend": round(t, 4),
                        "residual": round(r, 4),
                        "z_score": round(float(z), 3),
                        "severity": severity,
                        "phase": "context",
                    }
                )

        return records

    def detect_forecast_anomalies(
        self,
        actual_values: List[float],
        point_forecast: List[float],
        quantiles: Dict[str, List[float]],
        dates: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """Phase 2: Quantile Prediction Interval anomaly detection on future/test periods.

        CRITICAL = outside 80% PI (q10 - q90)
        WARNING  = outside 60% PI (q20 - q80)
        NORMAL   = inside 60% PI
        """
        q10 = quantiles.get("q10", [p * 0.9 for p in point_forecast])
        q20 = quantiles.get("q20", [p * 0.95 for p in point_forecast])
        q80 = quantiles.get("q80", [p * 1.05 for p in point_forecast])
        q90 = quantiles.get("q90", [p * 1.1 for p in point_forecast])

        records = []
        for i, (actual, fc) in enumerate(zip(actual_values, point_forecast)):
            outside_80 = actual < q10[i] or actual > q90[i]
            outside_60 = actual < q20[i] or actual > q80[i]

            if outside_80:
                severity = "CRITICAL"
            elif outside_60:
                severity = "WARNING"
            else:
                severity = "NORMAL"

            if severity != "NORMAL":
                records.append(
                    {
                        "step": i,
                        "date": dates[i] if dates and i < len(dates) else f"f_{i}",
                        "actual": round(float(actual), 4),
                        "forecast": round(float(fc), 4),
                        "q10": round(float(q10[i]), 4),
                        "q90": round(float(q90[i]), 4),
                        "severity": severity,
                        "phase": "forecast",
                    }
                )

        return records

    def analyze_series_anomalies(
        self,
        values: List[float],
        dates: List[str] = None,
    ) -> Dict[str, Any]:
        """Full anomaly assessment for a given dataset."""
        context_anomalies = self.detect_context_anomalies(values, dates)

        critical_count = sum(1 for a in context_anomalies if a["severity"] == "CRITICAL")
        warning_count = sum(1 for a in context_anomalies if a["severity"] == "WARNING")

        if critical_count > 0:
            severity = "high"
        elif warning_count > 0:
            severity = "medium"
        else:
            severity = "low"

        return {
            "anomalies": context_anomalies,
            "anomaly_count": len(context_anomalies),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "severity": severity,
        }
