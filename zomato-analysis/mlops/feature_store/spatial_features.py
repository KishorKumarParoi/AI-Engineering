"""
Spatial feature engineering modules for calculating delivery distance,
routing radius, and spatial metrics using the Haversine spherical formula.
"""

import numpy as np
import pandas as pd


def calculate_haversine_distance_vectorized(
    lat1: pd.Series, lon1: pd.Series, lat2: pd.Series, lon2: pd.Series
) -> pd.Series:
    """
    Computes great-circle distance between two points on Earth in kilometers.
    Vectorized using NumPy for high-throughput batch and streaming feature pipelines.
    
    Formula:
      a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
      c = 2 * atan2(√a, √(1−a))
      d = R * c  (where R = 6371 km)
    """
    r_km = 6371.0

    phi1 = np.radians(lat1.fillna(0.0))
    phi2 = np.radians(lat2.fillna(0.0))
    delta_phi = np.radians(lat2.fillna(0.0) - lat1.fillna(0.0))
    delta_lambda = np.radians(lon2.fillna(0.0) - lon1.fillna(0.0))

    a = (
        np.sin(delta_phi / 2.0) ** 2
        + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * np.arctan2(np.sqrt(np.clip(a, 0.0, 1.0)), np.sqrt(np.clip(1.0 - a, 0.0, 1.0)))
    
    distance = r_km * c
    # Fallback default for missing coordinates
    return distance.replace(0.0, np.nan).fillna(3.5).round(2)
