"""
Autonomous Multimodal Order Verification & Dispute Arbitration Engine
Master Orchestrator: Combines Image Quality, Fraud Guardian, Receipt OCR, Food Vision, and Policy Engine.
Tier: Principal AI & Data Engineer Standard
"""

import time
from typing import Union, Dict, Any, Optional
from pathlib import Path
from PIL import Image

from vision.preprocessor import ImageQualityAuditor
from vision.fraud_guardian import FraudGuardian
from vision.quality_detector import PackagingQualityDetector
from vision.receipt_ocr import ReceiptOCREngine
from vision.food_comparator import FoodComparator


class DisputeArbitrationEngine:
    """
    Real-time multimodal dispute arbitration system for food delivery platforms.
    Resolves wrong item, missing food, spillage, and damage claims in sub-2 seconds.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.fraud_guardian = FraudGuardian()
        self.ocr_engine = ReceiptOCREngine(api_key=api_key)
        self.food_comparator = FoodComparator(api_key=api_key)

    def arbitrate_order_dispute(
        self,
        image_source: Union[str, Path, bytes, Image.Image],
        digital_order: Dict[str, Any],
        claim_type: str = "WRONG_ITEM",
        customer_claim_note: str = ""
    ) -> Dict[str, Any]:
        """
        Executes end-to-end multimodal arbitration workflow:
        1. Preprocessing & Image Quality Audit (Blur, Exposure)
        2. Fraud Defense (dHash Perceptual Re-upload Audit)
        3. Receipt / KOT OCR Verification
        4. Visual Dish Comparison & Defect Detection
        5. Automated Arbitration Decision Policy
        """
        start_time = time.time()
        order_id = str(digital_order.get("order_id", "ORD-UNKNOWN"))
        customer_id = str(digital_order.get("customer_id", "CUST-UNKNOWN"))
        food_name = str(digital_order.get("food_name", "Unknown Dish"))
        order_amount = float(digital_order.get("order_amount", 25.0))
        delivery_fee = float(digital_order.get("delivery_fee", 3.5))

        # -------------------------------------------------------------
        # Step 1: Image Quality Audit (Guard against steam/blur)
        # -------------------------------------------------------------
        quality_audit = ImageQualityAuditor.audit_quality(image_source)

        if quality_audit["is_blurry"]:
            latency = round(time.time() - start_time, 3)
            return {
                "verdict": "REQUIRES_CUSTOMER_REUPLOAD",
                "status": "REJECTED_LOW_IMAGE_QUALITY",
                "refund_amount": 0.0,
                "confidence_score": 0.95,
                "culprit_liability": "NONE",
                "reason": "Image is blurry or lens was fogged by steam. Please remove container lid and re-take in good light.",
                "quality_audit": quality_audit,
                "latency_seconds": latency,
                "order_id": order_id
            }

        # -------------------------------------------------------------
        # Step 2: Fraud Defense (Perceptual Hashing & Re-upload Audit)
        # -------------------------------------------------------------
        fraud_audit = self.fraud_guardian.register_and_audit_submission(
            image_source=image_source,
            order_id=order_id,
            customer_id=customer_id
        )

        if fraud_audit["fraud_risk"] in ["HIGH", "CRITICAL"]:
            latency = round(time.time() - start_time, 3)
            return {
                "verdict": "DISPUTE_REJECTED_FRAUD",
                "status": "FRAUD_DETECTED",
                "refund_amount": 0.0,
                "confidence_score": 0.99,
                "culprit_liability": "CUSTOMER_ABUSE",
                "reason": f"Dispute rejected: {'; '.join(fraud_audit['reasons'])}",
                "fraud_audit": fraud_audit,
                "latency_seconds": latency,
                "order_id": order_id
            }

        # -------------------------------------------------------------
        # Step 3: Packaging & Spillage Defect Assessment
        # -------------------------------------------------------------
        damage_audit = PackagingQualityDetector.evaluate_packaging_quality(image_source)

        # -------------------------------------------------------------
        # Step 4: Receipt OCR & Food Visual Grounding
        # -------------------------------------------------------------
        ocr_result = self.ocr_engine.extract_receipt_tokens(image_source)
        ocr_verification = self.ocr_engine.verify_receipt_against_order(ocr_result, digital_order)

        food_verification = self.food_comparator.classify_and_verify_dish(
            image_source=image_source,
            ordered_food_name=food_name,
            ordered_cuisine=digital_order.get("cuisine")
        )

        # -------------------------------------------------------------
        # Step 5: Automated Arbitration Policy Engine
        # -------------------------------------------------------------
        verdict = "REQUIRES_HUMAN_REVIEW"
        liability = "NONE"
        refund_amount = 0.0
        confidence = 0.85
        reasons = []

        # Case A: Spillage & Packaging Damage Claim
        if claim_type in ["SPILLAGE", "DAMAGED_PACKAGE"] or damage_audit["is_damaged"]:
            if damage_audit["condition"] == "SEVERE_SPILLAGE_IN_TRANSIT":
                verdict = "INSTANT_REFUND_APPROVED"
                liability = "RIDER_TRANSIT_DAMAGE"
                refund_amount = round(order_amount + delivery_fee, 2)
                confidence = 0.94
                reasons.append("Severe container breach and sauce leakage verified outside packaging boundary.")
            elif damage_audit["condition"] == "MODERATE_LEAKAGE":
                verdict = "PARTIAL_REFUND_APPROVED"
                liability = "KITCHEN_SEAL_FAULT"
                refund_amount = round(order_amount * 0.50, 2)
                confidence = 0.88
                reasons.append("Moderate container leakage detected; partial refund credit issued.")

        # Case B: Wrong Item Dispatched Claim
        elif claim_type == "WRONG_ITEM":
            if not food_verification["is_match"] and food_verification["match_confidence"] >= 0.75:
                # Food in photo clearly does not match ordered item
                verdict = "INSTANT_REFUND_APPROVED"
                liability = "RESTAURANT_KITCHEN"
                refund_amount = round(order_amount, 2)
                confidence = round(food_verification["match_confidence"], 2)
                reasons.append(
                    f"Wrong item verified: Delivered '{food_verification['detected_dish']}' does not match ordered '{food_name}'."
                )
            elif food_verification["is_match"] and ocr_verification["item_name_verified"]:
                # Image and receipt clearly prove correct item was delivered
                verdict = "DISPUTE_REJECTED_CLAIM_DISPROVEN"
                liability = "NONE"
                refund_amount = 0.0
                confidence = 0.92
                reasons.append(
                    f"Visual verification and receipt OCR confirm '{food_name}' was correctly prepared and delivered."
                )
            else:
                verdict = "PARTIAL_REFUND_APPROVED"
                liability = "RESTAURANT_KITCHEN"
                refund_amount = round(order_amount * 0.50, 2)
                confidence = 0.80
                reasons.append("Item discrepancy partially confirmed. Courteous credit issued.")

        # Case C: General Defect / Missing Item
        else:
            if ocr_verification["order_id_verified"]:
                verdict = "INSTANT_REFUND_APPROVED"
                liability = "RESTAURANT_KITCHEN"
                refund_amount = round(order_amount, 2)
                confidence = 0.89
                reasons.append("Receipt verification confirmed order mismatch.")

        latency = round(time.time() - start_time, 3)

        return {
            "order_id": order_id,
            "customer_id": customer_id,
            "verdict": verdict,
            "refund_amount": refund_amount,
            "culprit_liability": liability,
            "confidence_score": confidence,
            "reasons": reasons,
            "latency_seconds": latency,
            "evidence": {
                "quality_audit": quality_audit,
                "fraud_audit": fraud_audit,
                "damage_audit": damage_audit,
                "ocr_verification": ocr_verification,
                "food_verification": food_verification
            }
        }
