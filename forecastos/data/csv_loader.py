import io
from typing import Any, Dict
import pandas as pd

from forecastos.data.validation import validate_dataframe


def load_csv_data(
    file_content: bytes,
    filename: str = "dataset.csv",
    date_col: str = "timestamp",
    value_col: str = "value",
) -> Dict[str, Any]:
    """Parse CSV raw bytes, run validation, and return structured dictionary."""
    try:
        if filename.endswith(".json"):
            df = pd.read_json(io.BytesIO(file_content))
        else:
            df = pd.read_csv(io.BytesIO(file_content))
    except Exception as e:
        raise ValueError(f"Failed to parse file '{filename}': {str(e)}")

    validated = validate_dataframe(df, date_col=date_col, value_col=value_col)
    validated["filename"] = filename
    return validated
