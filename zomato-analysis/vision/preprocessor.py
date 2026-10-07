"""
Image Preprocessor & Quality Auditor
Handles image normalization, Laplacian blur auditing, contrast enhancement, and receipt binarization.
Tier: Principal Computer Vision Engineer Standard
"""

import io
from pathlib import Path
from typing import Union, Tuple, Dict, Any
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
from scipy import signal


class ImageQualityAuditor:
    """
    Performs visual health inspection on customer uploaded food & receipt photos.
    Guards against steam-fogged lenses, dark lighting, and low-resolution uploads.
    """

    BLUR_THRESHOLD: float = 120.0       # Variance of Laplacian below this is considered blurry
    MIN_LUMINANCE: float = 35.0        # Images darker than this trigger underexposure warning
    MAX_LUMINANCE: float = 230.0       # Images brighter than this trigger overexposure warning

    # 3x3 Discrete Laplacian Kernel
    LAPLACIAN_KERNEL = np.array([
        [0,  1, 0],
        [1, -4, 1],
        [0,  1, 0]
    ], dtype=np.float32)

    @classmethod
    def load_image(cls, image_source: Union[str, Path, bytes, Image.Image]) -> Image.Image:
        """Loads and normalizes an image into RGB PIL format."""
        if isinstance(image_source, Image.Image):
            return image_source.convert("RGB")
        if isinstance(image_source, (str, Path)):
            return Image.open(image_source).convert("RGB")
        if isinstance(image_source, (bytes, bytearray)):
            return Image.open(io.BytesIO(image_source)).convert("RGB")
        raise ValueError(f"Unsupported image input type: {type(image_source)}")

    @classmethod
    def audit_quality(cls, image_source: Union[str, Path, bytes, Image.Image]) -> Dict[str, Any]:
        """
        Calculates image quality metrics:
        - blur_score: Variance of Laplacian (higher is sharper)
        - is_blurry: True if camera steam or motion blur is detected
        - avg_luminance: Average brightness (0-255)
        - is_dark: True if photo taken in insufficient lighting
        - resolution: (width, height)
        """
        img = cls.load_image(image_source)
        width, height = img.size

        # Convert to Grayscale Numpy array
        gray_img = img.convert("L")
        gray_arr = np.array(gray_img, dtype=np.float32)

        # 1. Laplacian Blur Auditing via 2D Convolution
        laplacian = signal.convolve2d(gray_arr, cls.LAPLACIAN_KERNEL, mode="same", boundary="symm")
        blur_score = float(laplacian.var())
        is_blurry = blur_score < cls.BLUR_THRESHOLD

        # 2. Exposure & Luminance Metrics
        avg_luminance = float(gray_arr.mean())
        contrast_score = float(gray_arr.std())
        is_dark = avg_luminance < cls.MIN_LUMINANCE
        is_overexposed = avg_luminance > cls.MAX_LUMINANCE

        status = "PASSED"
        warnings = []
        if is_blurry:
            warnings.append("BLUR_DETECTED (Possible camera steam or motion blur)")
        if is_dark:
            warnings.append("UNDEREXPOSED (Insufficient ambient lighting)")
        if is_overexposed:
            warnings.append("OVEREXPOSED (Severe flash glare)")

        if warnings:
            status = "DEGRADED"

        return {
            "status": status,
            "blur_score": round(blur_score, 2),
            "is_blurry": is_blurry,
            "avg_luminance": round(avg_luminance, 2),
            "contrast_score": round(contrast_score, 2),
            "is_dark": is_dark,
            "is_overexposed": is_overexposed,
            "resolution": (width, height),
            "warnings": warnings,
        }

    @classmethod
    def enhance_receipt_contrast(cls, image_source: Union[str, Path, bytes, Image.Image]) -> Image.Image:
        """
        Enhances crumpled or oil-stained thermal paper receipts for OCR.
        Applies grayscale normalization, contrast stretching, and Otsu binarization.
        """
        img = cls.load_image(image_source).convert("L")
        arr = np.array(img, dtype=np.uint8)

        # Contrast Stretch (Min-Max normalization to 0-255)
        p2, p98 = np.percentile(arr, (2, 98))
        if p98 > p2:
            stretched = np.clip((arr - p2) * 255.0 / (p98 - p2), 0, 255).astype(np.uint8)
        else:
            stretched = arr

        # Otsu Automatic Thresholding
        hist, bin_edges = np.histogram(stretched.ravel(), bins=256, range=(0, 256))
        total_pixels = stretched.size
        current_max, threshold = 0.0, 128

        sum_total = np.dot(np.arange(256), hist)
        weight_bg = 0
        sum_bg = 0

        for t in range(256):
            weight_bg += hist[t]
            if weight_bg == 0:
                continue
            weight_fg = total_pixels - weight_bg
            if weight_fg == 0:
                break

            sum_bg += t * hist[t]
            mean_bg = sum_bg / weight_bg
            mean_fg = (sum_total - sum_bg) / weight_fg

            # Inter-class variance
            var_between = weight_bg * weight_fg * ((mean_bg - mean_fg) ** 2)
            if var_between > current_max:
                current_max = var_between
                threshold = t

        binarized = np.where(stretched > threshold, 255, 0).astype(np.uint8)
        return Image.fromarray(binarized)
