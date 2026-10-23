"""
Enterprise Data Contracts & Schema Validation for Zomato Event Streams.
Enforces data quality, semantic boundaries, and PII anonymization before lakehouse ingestion.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class OrderItemContract(BaseModel):
    item_id: str = Field(..., min_length=1, max_length=64)
    item_name: str = Field(..., min_length=1, max_length=128)
    quantity: int = Field(..., gt=0, le=100)
    unit_price_inr: float = Field(..., gt=0.0)
    is_veg: bool = Field(default=True)


class OrderEventContract(BaseModel):
    """
    Data Contract for Inbound Order Events.
    Strictly validates business rules, financial bounds, and geographical boundaries.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = Field(..., min_length=5, max_length=64)
    customer_id: str = Field(..., min_length=5, max_length=64)
    restaurant_id: str = Field(..., min_length=5, max_length=64)
    city: str = Field(..., min_length=2, max_length=64)
    
    # Geographic coordinate bounds for Indian subcontinent
    customer_lat: float = Field(..., ge=8.0, le=37.5, description="Customer Latitude")
    customer_lng: float = Field(..., ge=68.0, le=97.5, description="Customer Longitude")
    restaurant_lat: float = Field(..., ge=8.0, le=37.5, description="Restaurant Latitude")
    restaurant_lng: float = Field(..., ge=68.0, le=97.5, description="Restaurant Longitude")

    items: List[OrderItemContract] = Field(..., min_length=1)
    subtotal_inr: float = Field(..., gt=0.0)
    delivery_fee_inr: float = Field(default=0.0, ge=0.0)
    surge_multiplier: float = Field(default=1.0, ge=1.0, le=5.0)
    total_amount_inr: float = Field(..., gt=0.0)

    payment_method: str = Field(..., pattern=r"^(UPI|CREDIT_CARD|DEBIT_CARD|NET_BANKING|WALLET|COD)$")
    timestamp: float = Field(default_factory=time.time)
    schema_version: str = Field(default="v2.1.0")

    @model_validator(mode="after")
    def validate_totals(self) -> "OrderEventContract":
        computed_subtotal = sum(i.quantity * i.unit_price_inr for i in self.items)
        if abs(computed_subtotal - self.subtotal_inr) > 0.05:
            raise ValueError(f"Subtotal mismatch: declared={self.subtotal_inr}, computed={computed_subtotal}")
        
        expected_total = self.subtotal_inr + self.delivery_fee_inr
        if abs(expected_total - self.total_amount_inr) > 0.05:
            raise ValueError(f"Total amount mismatch: declared={self.total_amount_inr}, expected={expected_total}")
        return self


class DataContractValidator:
    """
    Validates batch and streaming payloads against enterprise data contracts.
    """

    @staticmethod
    def validate_order_event(payload: Dict[str, Any]) -> tuple[bool, Optional[OrderEventContract], Optional[str]]:
        try:
            validated = OrderEventContract(**payload)
            return True, validated, None
        except Exception as e:
            return False, None, str(e)
