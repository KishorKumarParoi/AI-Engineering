import pytest
import uuid
import time
import json
from cdc.cdc_engine import CDCIngestionEngine, CDCOperation, CDCRecord
from patterns.outbox import ZomatoOutboxService, OutboxEventStatus, ZomatoOutboxRecord
from patterns.order_saga import ZomatoOrderSagaCoordinator

def test_cdc_engine_parse_and_route_to_bronze():
    engine = CDCIngestionEngine(target_bronze_table="orders_bronze")
    raw_event = json.dumps({
        "payload": {
            "op": "c",
            "ts_ms": int(time.time() * 1000),
            "source": {
                "table": "orders",
                "schema": "public",
                "lsn": 1024500,
                "txId": 501
            },
            "before": None,
            "after": {
                "id": "ORD_5501",
                "customer_id": "CUST_99",
                "amount": 450.0,
                "status": "PLACED"
            }
        }
    })
    cdc_record = engine.parse_debezium_payload(raw_event)
    assert cdc_record.operation == CDCOperation.INSERT
    assert cdc_record.source_table == "orders"
    assert cdc_record.lsn == 1024500

    bronze_row = engine.route_to_bronze(cdc_record)
    assert bronze_row["source_table"] == "orders"
    assert bronze_row["operation"] == "c"
    assert bronze_row["primary_key"] == "ORD_5501"
    assert bronze_row["is_deleted"] is False
    assert bronze_row["lakehouse_layer"] == "BRONZE"

def test_cdc_engine_delete_operation():
    engine = CDCIngestionEngine()
    delete_event = json.dumps({
        "payload": {
            "op": "d",
            "source": {"table": "orders", "schema": "public", "lsn": 1024600, "txId": 502},
            "before": {"id": "ORD_5501", "status": "CANCELLED"},
            "after": None
        }
    })
    record = engine.parse_debezium_payload(delete_event)
    assert record.operation == CDCOperation.DELETE
    bronze_row = engine.route_to_bronze(record)
    assert bronze_row["is_deleted"] is True
    assert bronze_row["primary_key"] == "ORD_5501"

def test_outbox_idempotency_and_dispatch():
    outbox = ZomatoOutboxService()
    idemp_key = "IDEMP_" + str(uuid.uuid4())
    payload = {"order_id": "ORD_991", "amount": 250.0}

    # First insert
    rec1 = outbox.insert_outbox_event(
        aggregate_type="ORDER",
        aggregate_id="ORD_991",
        topic_name="zomato.orders.events",
        payload=payload,
        idempotency_key=idemp_key
    )
    assert rec1.status == OutboxEventStatus.PENDING

    # Second insert with same idempotency key must return exact same record
    rec2 = outbox.insert_outbox_event(
        aggregate_type="ORDER",
        aggregate_id="ORD_991",
        topic_name="zomato.orders.events",
        payload=payload,
        idempotency_key=idemp_key
    )
    assert rec2.event_id == rec1.event_id

    # Dispatch pending records
    dispatched = outbox.poll_and_dispatch()
    assert len(dispatched) >= 1
    assert any(r.event_id == rec1.event_id and r.status == OutboxEventStatus.PUBLISHED for r in dispatched)

def test_saga_orchestrator_success_and_compensation():
    # Test successful saga
    saga = ZomatoOrderSagaCoordinator(order_id="ORD_SAGA_SUCCESS")
    state = {"kitchen_booked": False, "payment_debited": False}

    saga.add_step(
        name="ReserveKitchenSlot",
        action=lambda: state.update({"kitchen_booked": True}),
        compensate=lambda: state.update({"kitchen_booked": False})
    )
    saga.add_step(
        name="AuthorizePayment",
        action=lambda: state.update({"payment_debited": True}),
        compensate=lambda: state.update({"payment_debited": False})
    )

    success = saga.execute()
    assert success is True
    assert state["kitchen_booked"] is True
    assert state["payment_debited"] is True

    # Test saga failure and backward compensation
    fail_saga = ZomatoOrderSagaCoordinator(order_id="ORD_SAGA_FAILURE")
    fail_state = {"kitchen_booked": False, "rider_assigned": False}

    def failing_rider_assignment():
        raise RuntimeError("No delivery partner available in 5km radius")

    fail_saga.add_step(
        name="ReserveKitchenSlot",
        action=lambda: fail_state.update({"kitchen_booked": True}),
        compensate=lambda: fail_state.update({"kitchen_booked": False})
    )
    fail_saga.add_step(
        name="AssignRider",
        action=failing_rider_assignment,
        compensate=lambda: fail_state.update({"rider_assigned": False})
    )

    success_fail = fail_saga.execute()
    assert success_fail is False
    # Verify backward compensation revoked kitchen booking
    assert fail_state["kitchen_booked"] is False
