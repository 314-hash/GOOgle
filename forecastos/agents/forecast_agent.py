import re
from typing import Any, Dict


class NaturalLanguageForecastAgent:
    """Agent that translates natural-language user queries into structured forecast parameters."""

    def parse_query(self, prompt: str) -> Dict[str, Any]:
        """Parse natural language instruction prompt into structured options."""
        prompt_clean = prompt.strip().lower()

        # Extract horizon if specified (e.g. "next 30 days", "14 steps", "60 periods")
        horizon = 30
        horizon_match = re.search(r"(\d+)\s*(days?|weeks?|months?|steps?|periods?|hours?)", prompt_clean)
        if horizon_match:
            val = int(horizon_match.group(1))
            unit = horizon_match.group(2)
            if "week" in unit:
                horizon = val * 7
            elif "month" in unit:
                horizon = val * 30
            else:
                horizon = val

        # Extract scenario percentage adjustments (e.g. "increases by 20%", "demand drops 15%")
        adjustment_pct = 0.0
        adj_match = re.search(r"(increase|decrease|drop|rise|grow)\w*\s*by\s*(\d+(?:\.\d+)?)%", prompt_clean)
        if adj_match:
            direction = adj_match.group(1)
            pct = float(adj_match.group(2))
            if direction in ("decrease", "drop"):
                adjustment_pct = -pct
            else:
                adjustment_pct = pct

        # Detect domain context
        domain = "general"
        if any(k in prompt_clean for k in ["sales", "revenue", "retail", "demand"]):
            domain = "sales"
        elif any(k in prompt_clean for k in ["crypto", "btc", "eth", "price", "stock", "market"]):
            domain = "crypto"
        elif any(k in prompt_clean for k in ["energy", "power", "grid", "kw", "mw"]):
            domain = "energy"
        elif any(k in prompt_clean for k in ["inventory", "stock", "warehouse", "units"]):
            domain = "inventory"

        # Detect intent type
        if "what happens if" in prompt_clean or adjustment_pct != 0:
            query_type = "what_if"
        elif "highest" in prompt_clean or "peak" in prompt_clean or "lowest" in prompt_clean:
            query_type = "peak_analysis"
        else:
            query_type = "standard_forecast"

        return {
            "original_prompt": prompt,
            "horizon": max(1, min(1024, horizon)),
            "adjustment_pct": adjustment_pct,
            "domain": domain,
            "query_type": query_type,
        }
