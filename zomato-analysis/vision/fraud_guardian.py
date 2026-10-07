"""
Fraud Guardian & Perceptual Hashing Engine
Detects duplicate photo re-uploads, stock photo abuse, and adversarial metadata tampering.
Tier: Principal Security & MLOps Engineer Standard
"""

import hashlib
from typing import Union, Dict, Any, List
from pathlib import Path
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS

from vision.preprocessor import ImageQualityAuditor


class FraudGuardian:
    """
    Guards the dispute engine against fraudulent claim patterns:
    - Perceptual difference hashing (dHash) to flag identical or cropped re-uploads.
    - Reverse photo match ledger.
    - EXIF metadata audit for digital modification tools.
    """

    DUPLICATE_HAMMING_THRESHOLD: int = 5  # Distance <= 5 indicates duplicate or minor edit

    def __init__(self):
        # Ledger of (order_id, customer_id, dhash_hex, timestamp)
        self.dispute_ledger: List[Dict[str, Any]] = []

    @classmethod
    def compute_dhash(cls, image_source: Union[str, Path, bytes, Image.Image], hash_size: int = 8) -> str:
        """
        Computes 64-bit difference hash (dHash).
        Resizes to (hash_size + 1, hash_size), converts to grayscale,
        and computes adjacent pixel gradient differences.
        """
        img = ImageQualityAuditor.load_image(image_source)
        resized = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        arr = np.array(resized, dtype=np.float32)

        # Difference between adjacent columns
        diff = arr[:, 1:] > arr[:, :-1]
        
        # Flatten boolean array into hex integer string
        decimal_val = 0
        for bit in diff.flatten():
            decimal_val = (decimal_val << 1) | int(bit)

        return f"{decimal_val:016x}"

    @classmethod
    def hamming_distance(cls, hash1: str, hash2: str) -> int:
        """Calculates bitwise Hamming distance between two hex hash strings."""
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        xor_val = val1 ^ val2
        return bin(xor_val).count("1")

    @classmethod
    def audit_exif_metadata(cls, image_source: Union[str, Path, bytes, Image.Image]) -> Dict[str, Any]:
        """
        Audits EXIF metadata to flag edited photos or missing camera metadata.
        """
        img = ImageQualityAuditor.load_image(image_source)
        exif_raw = img.getexif()

        metadata = {}
        if exif_raw:
            for tag_id, value in exif_raw.items():
                tag_name = TAGS.get(tag_id, str(tag_id))
                metadata[tag_name] = str(value)

        has_camera_hardware = any(k in metadata for k in ["Make", "Model", "LensModel"])
        is_software_edited = "Software" in metadata

        return {
            "has_exif": bool(metadata),
            "camera_model": metadata.get("Model", "Unknown / Stripped"),
            "has_camera_hardware": has_camera_hardware,
            "software_tool": metadata.get("Software", None),
            "is_software_edited": is_software_edited,
            "raw_tags_count": len(metadata)
        }

    def register_and_audit_submission(
        self,
        image_source: Union[str, Path, bytes, Image.Image],
        order_id: str,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Checks submission against historical dispute ledger:
        Flags exact duplicates or cross-account photo recycling.
        """
        image_hash = self.compute_dhash(image_source)
        exif_info = self.audit_exif_metadata(image_source)

        duplicate_found = False
        matching_dispute = None
        min_distance = 64

        for record in self.dispute_ledger:
            dist = self.hamming_distance(image_hash, record["hash"])
            if dist < min_distance:
                min_distance = dist
            if dist <= self.DUPLICATE_HAMMING_THRESHOLD:
                duplicate_found = True
                matching_dispute = record
                break

        # Record this submission in ledger
        self.dispute_ledger.append({
            "order_id": order_id,
            "customer_id": customer_id,
            "hash": image_hash
        })

        fraud_risk = "LOW"
        reasons = []

        if duplicate_found and matching_dispute:
            if matching_dispute["order_id"] == order_id:
                reasons.append("DUPLICATE_RESUBMISSION: Same order photo submitted twice")
                fraud_risk = "HIGH"
            else:
                reasons.append(
                    f"PHOTO_RECYCLING_FRAUD: Photo matched past order #{matching_dispute['order_id']} (Hamming distance: {min_distance})"
                )
                fraud_risk = "CRITICAL"

        return {
            "fraud_risk": fraud_risk,
            "dhash": image_hash,
            "duplicate_detected": duplicate_found,
            "min_historical_distance": min_distance,
            "matched_record": matching_dispute,
            "exif_audit": exif_info,
            "reasons": reasons
        }
