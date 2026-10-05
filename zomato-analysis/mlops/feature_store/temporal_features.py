"""
Temporal feature engineering modules for extracting rush hour, cyclic time representations,
and weekend flags from order timestamps.
"""

import numpy as np
import pandas as pd


def extract_temporal_features(timestamps: pd.Series) -> pd.DataFrame:
    """
    Transforms ISO or datetime timestamps into temporal features:
      - order_hour: 0 to 23
      - is_peak_rush: 1.0 during lunch (12-14) or dinner (19-22)
      - is_weekend: 1.0 for Saturday / Sunday
      - hour_sin / hour_cos: Cyclic time representations
    """
    ts = pd.to_datetime(timestamps, errors="coerce").fillna(pd.Timestamp.now())

    hours = ts.dt.hour
    dayofweek = ts.dt.dayofweek

    is_peak = ((hours >= 12) & (hours <= 14)) | ((hours >= 19) & (hours <= 22))
    is_weekend = dayofweek >= 5

    # Cyclic time encoding (24 hour period)
    hour_sin = np.sin(2 * np.pi * hours / 24.0)
    hour_cos = np.cos(2 * np.pi * hours / 24.0)

    return pd.DataFrame({
        "order_hour": hours,
        "is_peak_rush": is_peak.astype(float),
        "is_weekend": is_weekend.astype(float),
        "hour_sin": hour_sin.round(4),
        "hour_cos": hour_cos.round(4)
    }, index=timestamps.index)
