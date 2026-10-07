#!/usr/bin/env python3
"""
Test Suite: test_vision_ocr.py
Purpose: Verifies the Autonomous Multimodal Order Verification & OCR Dispute Engine.
Scope: Image Quality (Blur/Luminance), Perceptual Hash Fraud Defense, Receipt OCR, Food Vision, and Dispute Arbitration.
Tier: Senior Staff / Principal AI Engineer Standard
"""

import os
import sys
import unittest
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vision.preprocessor import ImageQualityAuditor
from vision.fraud_guardian import FraudGuardian
from vision.quality_detector import PackagingQualityDetector
from vision.receipt_ocr import ReceiptOCREngine, compute_levenshtein_similarity
from vision.food_comparator import FoodComparator
from vision.dispute_engine import DisputeArbitrationEngine


class TestVisionOCREngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples_dir = PROJECT_ROOT / "vision" / "test_samples"
        cls.sample_receipt = cls.samples_dir / "sample_receipt.png"
        cls.sample_curry = cls.samples_dir / "sample_curry.png"
        cls.sample_burger = cls.samples_dir / "sample_burger.png"
        cls.sample_spilled = cls.samples_dir / "sample_spilled.png"
        cls.sample_blurry = cls.samples_dir / "sample_blurry.png"

        assert cls.sample_receipt.exists(), "Sample receipt image missing"
        assert cls.sample_curry.exists(), "Sample curry image missing"
        assert cls.sample_spilled.exists(), "Sample spilled image missing"

    def test_01_image_quality_and_blur_detection(self):
        """Verifies Laplacian variance distinguishes sharp photos from blurry/steam-fogged uploads."""
        sharp_audit = ImageQualityAuditor.audit_quality(self.sample_curry)
        blurry_audit = ImageQualityAuditor.audit_quality(self.sample_blurry)

        print(f"\n  [CV Audit] Sharp image blur score: {sharp_audit['blur_score']}")
        print(f"  [CV Audit] Blurry image blur score: {blurry_audit['blur_score']}")

        self.assertFalse(sharp_audit["is_blurry"])
        self.assertTrue(blurry_audit["is_blurry"])
        self.assertEqual(blurry_audit["status"], "DEGRADED")

    def test_02_fraud_guardian_perceptual_hashing(self):
        """Verifies dHash calculation and cross-account photo recycling detection."""
        guardian = FraudGuardian()
        dhash1 = guardian.compute_dhash(self.sample_curry)
        dhash2 = guardian.compute_dhash(self.sample_burger)

        self.assertEqual(len(dhash1), 16)
        dist_diff = guardian.hamming_distance(dhash1, dhash2)
        self.assertGreater(dist_diff, 5)

        # Submission 1: Customer A
        sub1 = guardian.register_and_audit_submission(self.sample_curry, "ORD-1", "CUST-A")
        self.assertEqual(sub1["fraud_risk"], "LOW")

        # Submission 2: Customer B re-using Customer A's exact image
        sub2 = guardian.register_and_audit_submission(self.sample_curry, "ORD-2", "CUST-B")
        self.assertIn(sub2["fraud_risk"], ["HIGH", "CRITICAL"])
        self.assertTrue(sub2["duplicate_detected"])
        print(f"  [Fraud Guardian] Detected Photo Recycling: {sub2['reasons']}")

    def test_03_packaging_damage_and_spillage_detection(self):
        """Verifies perimeter liquid detection detects soup/curry transit breach."""
        intact_res = PackagingQualityDetector.evaluate_packaging_quality(self.sample_curry)
        spill_res = PackagingQualityDetector.evaluate_packaging_quality(self.sample_spilled)

        print(f"  [Damage Audit] Intact spill score: {intact_res['spillage_score']}")
        print(f"  [Damage Audit] Spilled spill score: {spill_res['spillage_score']} ({spill_res['condition']})")

        self.assertFalse(intact_res["is_damaged"])
        self.assertTrue(spill_res["is_damaged"])
        self.assertIn(spill_res["condition"], ["MODERATE_LEAKAGE", "SEVERE_SPILLAGE_IN_TRANSIT"])

    def test_04_receipt_ocr_and_token_alignment(self):
        """Verifies receipt OCR extraction and Levenshtein token alignment."""
        ocr = ReceiptOCREngine()
        ocr_result = ocr.extract_receipt_tokens(self.sample_receipt)

        print(f"  [OCR Extraction] Order ID: {ocr_result.get('order_id')}, Items: {ocr_result.get('items')}")
        self.assertIsNotNone(ocr_result.get("order_id"))

        digital_order = {
            "order_id": "ORD-2026-9842",
            "food_name": "Paneer Butter Masala"
        }
        verified = ocr.verify_receipt_against_order(ocr_result, digital_order)
        self.assertTrue(verified["receipt_authentic"])
        print(f"  [OCR Alignment] Best item similarity: {verified['best_item_similarity']}")

    def test_05_autonomous_dispute_arbitration(self):
        """Verifies end-to-end dispute arbitration workflow."""
        engine = DisputeArbitrationEngine()
        order = {
            "order_id": "ORD-2026-9842",
            "customer_id": "CUST-774",
            "food_name": "Paneer Butter Masala",
            "order_amount": 31.50,
            "delivery_fee": 3.00,
            "cuisine": "Indian"
        }

        # Case 1: Spillage Claim
        res_spill = engine.arbitrate_order_dispute(self.sample_spilled, order, claim_type="SPILLAGE")
        self.assertIn(res_spill["verdict"], ["INSTANT_REFUND_APPROVED", "PARTIAL_REFUND_APPROVED"])
        self.assertGreater(res_spill["refund_amount"], 0.0)
        print(f"  [Arbitration 1] Spillage Verdict: {res_spill['verdict']} (${res_spill['refund_amount']})")

        # Case 2: Blurry steam upload
        res_blur = engine.arbitrate_order_dispute(self.sample_blurry, order, claim_type="WRONG_ITEM")
        self.assertEqual(res_blur["verdict"], "REQUIRES_CUSTOMER_REUPLOAD")
        print(f"  [Arbitration 2] Blurry Verdict: {res_blur['verdict']}")


def test_vision_ocr():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVisionOCREngine)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    print("\n==========================================================")
    print("   COMPUTER VISION & OCR DISPUTE ARBITRATION TEST SUITE   ")
    print("==========================================================")
    success = test_vision_ocr()
    if success:
        print("\nALL VISION & OCR INTEGRITY CHECKS PASSED (100%)!\n")
        sys.exit(0)
    else:
        print("\nVISION & OCR CHECKS FAILED!\n")
        sys.exit(1)
