from typing import Any, Dict, List
import numpy as np


def compute_confidence_analysis(
    point_forecast: List[float],
    quantiles: Dict[str, List[float]],
) -> Dict[str, Any]:
    """Calculate forecast uncertainty and confidence metrics based on 80% prediction interval.

    Returns score in [0.0, 1.0], uncertainty spread, and risk rating.
    """
    pts = np.array(point_forecast)
    q10 = np.array(quantiles.get("q10", pts * 0.9))
    q90 = np.array(quantiles.get("q90", pts * 1.1))

    # Calculate prediction interval spread across horizon
    pi_spread = q90 - q10
    abs_pts = np.abs(pts)
    abs_pts = np.where(abs_pts == 0, 1.0, abs_pts)

    relative_spread = pi_spread / abs_pts
    avg_relative_spread = float(np.mean(relative_spread))

    # Map relative spread to confidence score [0.0, 1.0]
    # Small relative spread (< 0.2) -> high confidence (> 0.8)
    confidence_score = max(0.05, min(0.99, 1.0 - (avg_relative_spread / 2.0)))

    if confidence_score > 0.8:
        uncertainty_level = "low"
    elif confidence_score > 0.5:
        uncertainty_level = "medium"
    else:
        uncertainty_level = "high"

    return {
        "confidence_score": round(confidence_score, 3),
        "avg_pi_spread": round(float(np.mean(pi_spread)), 4),
        "uncertainty_level": uncertainty_level,
    }
