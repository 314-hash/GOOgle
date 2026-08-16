from typing import List
import pandas as pd


def generate_future_dates(
    last_date: str,
    horizon: int,
    frequency: str = "D",
) -> List[str]:
    """Generate ISO date strings for future forecast steps based on frequency."""
    try:
        start_ts = pd.to_datetime(last_date)
        # Handle custom frequencies
        freq_code = frequency if frequency else "D"
        future_range = pd.date_range(start=start_ts, periods=horizon + 1, freq=freq_code)[1:]
        return [d.isoformat() for d in future_range]
    except Exception:
        # Fallback to simple step indexing
        return [f"Step_{i+1}" for i in range(horizon)]
