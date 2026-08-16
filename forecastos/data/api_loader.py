from typing import Any, Dict
import urllib.request
import json
import pandas as pd

from forecastos.data.validation import validate_dataframe


def fetch_api_dataset(
    url: str,
    date_col: str = "timestamp",
    value_col: str = "value",
    timeout: int = 10,
) -> Dict[str, Any]:
    """Fetch time series data from a remote HTTP API returning JSON."""
    req = urllib.request.Request(url, headers={"User-Agent": "ForecastOS/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Failed to fetch data from API URL '{url}': {str(e)}")

    if isinstance(data, dict):
        # Look for nested array inside common keys
        for key in ["data", "prices", "series", "results", "values"]:
            if key in data and isinstance(data[key], list):
                data = data[key]
                break

    if not isinstance(data, list):
        raise ValueError("API response must be a JSON array or a JSON object containing a data array.")

    df = pd.DataFrame(data)
    validated = validate_dataframe(df, date_col=date_col, value_col=value_col)
    validated["source_url"] = url
    return validated
