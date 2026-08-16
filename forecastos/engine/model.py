import logging
from typing import Any, Dict, List, Tuple
import numpy as np

from forecastos.config import settings

logger = logging.getLogger("forecastos.engine")


class MockTimesFM:
    """Mock TimesFM model for fast local development, offline mode, and testing."""

    def __init__(self, model_id: str = "google/timesfm-2.5-200m-pytorch"):
        self.model_id = model_id
        self.compiled = False
        self.max_context = 1024
        self.max_horizon = 30

    def compile(self, forecast_config: Any = None):
        self.compiled = True
        if forecast_config:
            self.max_context = getattr(forecast_config, "max_context", 1024)
            self.max_horizon = getattr(forecast_config, "max_horizon", 30)

    def forecast(
        self, horizon: int, inputs: List[np.ndarray]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Simulate realistic TimesFM point and quantile forecasts."""
        batch_size = len(inputs)
        point_outputs = []
        quantile_outputs = []

        for ts in inputs:
            if len(ts) == 0:
                last_val = 100.0
                std_val = 5.0
            else:
                last_val = float(ts[-1])
                std_val = float(np.std(ts[-30:])) if len(ts) >= 30 else float(np.std(ts)) or 2.0
                if std_val == 0:
                    std_val = max(1.0, abs(last_val) * 0.05)

            # Fit a simple linear trend from last points
            if len(ts) >= 5:
                x = np.arange(len(ts[-15:]))
                slope, _ = np.polyfit(x, ts[-15:], 1)
            else:
                slope = 0.0

            # Generate synthetic future trajectory with damped slope & seasonality
            t_future = np.arange(1, horizon + 1)
            trend_component = last_val + slope * t_future * 0.5
            seasonal_component = np.sin(t_future * (2 * np.pi / 7.0)) * (std_val * 0.3)
            median_fc = trend_component + seasonal_component

            # Generate 10 quantiles: [mean, q10, q20, q30, q40, q50, q60, q70, q80, q90]
            # Spread widens as horizon increases
            uncertainty_growth = np.sqrt(t_future) * (std_val * 0.25)

            q_matrix = np.zeros((horizon, 10))
            q_matrix[:, 5] = median_fc  # q50
            q_matrix[:, 0] = median_fc  # mean

            quantile_multipliers = {
                1: -1.28,  # q10
                2: -0.84,  # q20
                3: -0.52,  # q30
                4: -0.25,  # q40
                6: 0.25,   # q60
                7: 0.52,   # q70
                8: 0.84,   # q80
                9: 1.28,   # q90
            }

            for q_idx, mult in quantile_multipliers.items():
                q_matrix[:, q_idx] = median_fc + mult * (std_val + uncertainty_growth)

            point_outputs.append(median_fc)
            quantile_outputs.append(q_matrix)

        return np.array(point_outputs), np.array(quantile_outputs)


class TimesFMAdapter:
    """Production Adapter for Google TimesFM 2.5 foundation model."""

    _instance = None
    _model = None

    def __init__(self):
        self.use_mock = settings.TIMESFM_MOCK
        self.model_id = settings.TIMESFM_MODEL_ID
        self.loaded = False
        self._initialize_model()

    def _initialize_model(self):
        if self.use_mock:
            logger.info("Initializing TimesFM in MOCK mode.")
            self._model = MockTimesFM(model_id=self.model_id)
            self.loaded = True
            return

        try:
            logger.info(f"Attempting to load real TimesFM 2.5 PyTorch model: {self.model_id}")
            from timesfm import ForecastConfig, TimesFM_2p5_200M_torch

            self._model = TimesFM_2p5_200M_torch.from_pretrained(
                model_id=self.model_id,
                torch_compile=False,
            )
            self.loaded = True
            logger.info("TimesFM PyTorch model loaded successfully.")
        except Exception as e:
            logger.warning(
                f"Could not load real TimesFM model ({e}). Falling back to MockTimesFM mode."
            )
            self._model = MockTimesFM(model_id=self.model_id)
            self.use_mock = True
            self.loaded = True

    def forecast(
        self,
        series: List[float],
        horizon: int = 30,
        context_len: int = 1024,
    ) -> Dict[str, Any]:
        """Generate point and quantile forecasts for a time-series input."""
        context_arr = np.array(series, dtype=np.float32)
        if len(context_arr) > context_len:
            context_arr = context_arr[-context_len:]

        # Compile model for given context and horizon
        try:
            if not self.use_mock:
                from timesfm import ForecastConfig
                fc = ForecastConfig(
                    max_context=max(32, len(context_arr)),
                    max_horizon=horizon,
                    per_core_batch_size=32,
                    use_continuous_quantile_head=True,
                )
                self._model.compile(fc)
            else:
                self._model.compile()
        except Exception as e:
            logger.warning(f"Compilation warning: {e}. Proceeding with default execution.")

        # Run model inference
        point_fc, quantiles_fc = self._model.forecast(
            horizon=horizon,
            inputs=[context_arr],
        )

        # Extract 1D point forecast and quantiles dictionary
        point_series = point_fc[0].tolist()
        q_matrix = quantiles_fc[0]  # shape: (horizon, 10)

        quantile_dict = {
            "mean": q_matrix[:, 0].tolist(),
            "q10": q_matrix[:, 1].tolist(),
            "q20": q_matrix[:, 2].tolist(),
            "q30": q_matrix[:, 3].tolist(),
            "q40": q_matrix[:, 4].tolist(),
            "q50": q_matrix[:, 5].tolist(),
            "q60": q_matrix[:, 6].tolist(),
            "q70": q_matrix[:, 7].tolist(),
            "q80": q_matrix[:, 8].tolist(),
            "q90": q_matrix[:, 9].tolist(),
        }

        return {
            "point_forecast": point_series,
            "quantiles": quantile_dict,
            "horizon": horizon,
            "context_len": len(context_arr),
            "model_name": "TimesFM-2.5-Mock" if self.use_mock else "TimesFM-2.5",
            "is_mock": self.use_mock,
        }


# Singleton accessor
_adapter_instance = None


def get_model_adapter() -> TimesFMAdapter:
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = TimesFMAdapter()
    return _adapter_instance
