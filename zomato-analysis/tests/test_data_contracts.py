"""Unit tests for Zomato Data Contracts and Schema Validation."""

import pytest
from data_contracts.order_event_contract import DataContractValidator, OrderEventContract


def test_valid_order_contract():
    payload = {
        "order_id": "ORD_1001",
        "customer_id": "CUST_400",
        "restaurant_id": "REST_99",
        "city": "Bengaluru",
        "customer_lat": 12.9716,
        "customer_lng": 77.5946,
        "restaurant_lat": 12.9352,
        "restaurant_lng": 77.6245,
        "items": [
            {"item_id": "ITM_1", "item_name": "Chicken Biryani", "quantity": 2, "unit_price_inr": 250.0, "is_veg": False},
            {"item_id": "ITM_2", "item_name": "Gulab Jamun", "quantity": 1, "unit_price_inr": 60.0, "is_veg": True}
        ],
        "subtotal_inr": 560.0,
        "delivery_fee_inr": 40.0,
        "total_amount_inr": 600.0,
        "payment_method": "UPI"
    }

    valid, contract, err = DataContractValidator.validate_order_event(payload)
    assert valid is True
    assert err is None
    assert contract.order_id == "ORD_1001"
    assert contract.total_amount_inr == 600.0


def test_invalid_subtotal_mismatch():
    payload = {
        "order_id": "ORD_1002",
        "customer_id": "CUST_401",
        "restaurant_id": "REST_99",
        "city": "Bengaluru",
        "customer_lat": 12.9716,
        "customer_lng": 77.5946,
        "restaurant_lat": 12.9352,
        "restaurant_lng": 77.6245,
        "items": [
            {"item_id": "ITM_1", "item_name": "Burger", "quantity": 1, "unit_price_inr": 150.0, "is_veg": True}
        ],
        "subtotal_inr": 999.0, # Corrupt subtotal
        "delivery_fee_inr": 30.0,
        "total_amount_inr": 1029.0,
        "payment_method": "UPI"
    }

    valid, contract, err = DataContractValidator.validate_order_event(payload)
    assert valid is False
    assert "Subtotal mismatch" in err


def test_invalid_coordinates_out_of_bounds():
    payload = {
        "order_id": "ORD_1003",
        "customer_id": "CUST_402",
        "restaurant_id": "REST_99",
        "city": "Bengaluru",
        "customer_lat": -45.0, # Out of India bounds
        "customer_lng": 77.5946,
        "restaurant_lat": 12.9352,
        "restaurant_lng": 77.6245,
        "items": [
            {"item_id": "ITM_1", "item_name": "Pizza", "quantity": 1, "unit_price_inr": 300.0, "is_veg": True}
        ],
        "subtotal_inr": 300.0,
        "delivery_fee_inr": 40.0,
        "total_amount_inr": 340.0,
        "payment_method": "CREDIT_CARD"
    }

    valid, contract, err = DataContractValidator.validate_order_event(payload)
    assert valid is False
    assert "greater than or equal to 8" in err
