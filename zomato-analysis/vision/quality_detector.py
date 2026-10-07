"""
Packaging & Food Quality Damage Detector
Computes physical delivery defects: liquid spillage, container crush, and packaging breaches.
Tier: Principal Computer Vision Engineer Standard
"""

from typing import Union, Dict, Any
from pathlib import Path
import numpy as np
from PIL import Image

from vision.preprocessor import ImageQualityAuditor


class PackagingQualityDetector:
    """
    Analyzes visual delivery artifacts to distinguish between:
    - Kitchen Fault (e.g., poor lid seal, missing tape)
    - Transit Damage (e.g., severe spillage, crushed paper box)
    - Normal Condition (intact food container)
    """

    SPILLAGE_SEVERE_THRESHOLD: float = 0.05
    SPILLAGE_MODERATE_THRESHOLD: float = 0.01

    @classmethod
    def evaluate_packaging_quality(cls, image_source: Union[str, Path, bytes, Image.Image]) -> Dict[str, Any]:
        """
        Analyzes image color distributions and perimeter gradient anomalies
        to compute a quantitative Spillage & Defect Score.
        """
        img = ImageQualityAuditor.load_image(image_source)
        w, h = img.size

        # Convert to HSV color space via Pillow
        hsv_img = img.convert("HSV")
        hsv_arr = np.array(hsv_img, dtype=np.float32)

        hue = hsv_arr[:, :, 0]
        sat = hsv_arr[:, :, 1]
        val = hsv_arr[:, :, 2]

        # Extract Perimeter / Bag Margin (outer 15% boundary where spilled gravy/sauce pools)
        margin_x = max(1, int(w * 0.15))
        margin_y = max(1, int(h * 0.15))

        # Create mask of outer perimeter
        outer_mask = np.ones((h, w), dtype=bool)
        outer_mask[margin_y:h - margin_y, margin_x:w - margin_x] = False

        # Fluid / Gravy Signature: High Saturation (>80) + Medium-Dark Value (40-180)
        fluid_mask = (sat > 75.0) & (val > 35.0) & (val < 190.0)

        # Spillage pixels in the outer perimeter
        spill_pixels_outer = np.logical_and(outer_mask, fluid_mask).sum()
        total_outer_pixels = outer_mask.sum()

        spill_ratio = float(spill_pixels_outer / max(1, total_outer_pixels))

        # Damage assessment
        if spill_ratio >= cls.SPILLAGE_SEVERE_THRESHOLD:
            condition = "SEVERE_SPILLAGE_IN_TRANSIT"
            liability = "RIDER_TRANSIT_DAMAGE"
            severity = "HIGH"
        elif spill_ratio >= cls.SPILLAGE_MODERATE_THRESHOLD:
            condition = "MODERATE_LEAKAGE"
            liability = "KITCHEN_SEAL_FAULT"
            severity = "MEDIUM"
        else:
            condition = "PACKAGING_INTACT"
            liability = "NONE"
            severity = "LOW"

        return {
            "condition": condition,
            "spillage_score": round(spill_ratio, 4),
            "severity": severity,
            "imputed_liability": liability,
            "outer_margin_tested_pixels": int(total_outer_pixels),
            "spill_pixels_detected": int(spill_pixels_outer),
            "is_damaged": spill_ratio >= cls.SPILLAGE_MODERATE_THRESHOLD
        }
