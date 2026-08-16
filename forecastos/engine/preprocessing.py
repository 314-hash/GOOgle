from typing import List, Tuple
import numpy as np


def preprocess_series(
    series: List[float],
    max_context: int = 1024,
) -> Tuple[np.ndarray, float, float]:
    """Clean, impute, and extract the context window for TimesFM.

    Returns:
        Tuple of (context_array, mean, std)
    """
    arr = np.array(series, dtype=np.float64)

    # Impute any NaN values using linear interpolation
    nans = np.isnan(arr)
    if np.any(nans):
        arr = np.where(nans, np.nanmean(arr), arr)

    # Truncate to max context length if needed
    if len(arr) > max_context:
        arr = arr[-max_context:]

    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr))

    return arr, mean_val, std_val
