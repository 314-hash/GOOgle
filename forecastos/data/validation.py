from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd


class ValidationError(Exception):
    """Custom exception raised for dataset validation errors."""

    pass


def validate_time_series_input(
    series: List[float],
    dates: List[str] = None,
    min_length: int = 1,
) -> Tuple[np.ndarray, List[str]]:
    """Validate a raw list of numeric values and optional date strings.

    Returns:
        Tuple of (clean_numpy_array, clean_dates_list)
    """
    if not series:
        raise ValidationError("Input series cannot be empty.")

    if len(series) < min_length:
        raise ValidationError(f"Input series length ({len(series)}) is less than required minimum ({min_length}).")

    # Check for NaN / Infinity
    arr = np.array(series, dtype=np.float64)
    if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
        raise ValidationError("Input series contains NaN or infinite values. Please clean or interpolate first.")

    # Validate dates if provided
    if dates is not None:
        if len(dates) != len(series):
            raise ValidationError(f"Dates length ({len(dates)}) does not match series length ({len(series)}).")

        try:
            parsed_dates = pd.to_datetime(dates)
            if parsed_dates.has_duplicates:
                raise ValidationError("Duplicate timestamps detected in date series.")
            clean_dates = [d.isoformat() for d in parsed_dates]
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Invalid timestamp format in dates: {e}")
    else:
        clean_dates = [f"t_{i}" for i in range(len(series))]

    return arr, clean_dates


def validate_dataframe(
    df: pd.DataFrame,
    date_col: str = "timestamp",
    value_col: str = "value",
) -> Dict[str, Any]:
    """Validate a pandas DataFrame for time-series ingestion.

    Returns dictionary with parsed values, dates, frequency, and statistics.
    """
    if df.empty:
        raise ValidationError("Uploaded dataset is empty.")

    # Check columns flexible casing
    cols_lower = {col.lower(): col for col in df.columns}
    actual_date_col = cols_lower.get(date_col.lower(), cols_lower.get("date"))
    actual_value_col = cols_lower.get(value_col.lower(), cols_lower.get("close", cols_lower.get("sales", cols_lower.get("price"))))

    if not actual_value_col:
        # If no explicit value col, take the last numeric column or raises
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            actual_value_col = numeric_cols[-1]
        else:
            raise ValidationError(f"No numeric value column found. Expected column '{value_col}'.")

    if actual_date_col:
        try:
            df[actual_date_col] = pd.to_datetime(df[actual_date_col])
            df = df.sort_values(actual_date_col).reset_index(drop=True)
            if df[actual_date_col].duplicated().any():
                raise ValidationError("Duplicate timestamps found in dataset.")
            dates = [d.isoformat() for d in df[actual_date_col]]
            freq = pd.infer_freq(df[actual_date_col]) or "D"
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Error parsing date column '{actual_date_col}': {e}")
    else:
        dates = [f"Step_{i+1}" for i in range(len(df))]
        freq = "D"

    # Validate value column
    values = pd.to_numeric(df[actual_value_col], errors="coerce")
    if values.isnull().any():
        # Linear interpolation for missing values if minor
        null_count = values.isnull().sum()
        if null_count > len(df) * 0.3:
            raise ValidationError(f"Dataset has too many missing values ({null_count}/{len(df)} rows).")
        values = values.interpolate(method="linear").bfill().ffill()

    val_arr = values.to_numpy(dtype=np.float64)

    return {
        "values": val_arr.tolist(),
        "dates": dates,
        "frequency": freq,
        "row_count": len(val_arr),
        "start_date": dates[0] if dates else None,
        "end_date": dates[-1] if dates else None,
        "min_value": float(np.min(val_arr)),
        "max_value": float(np.max(val_arr)),
        "mean_value": float(np.mean(val_arr)),
    }
