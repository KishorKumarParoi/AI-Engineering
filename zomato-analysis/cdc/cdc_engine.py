"""
Change Data Capture (CDC) Processing Engine for Zomato Lakehouse Ingestion.
Simulates Debezium / Kafka Connect CDC capture from PostgreSQL into Delta Lake Bronze.
"""

import time
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class CDCOperation(str, Enum):
    INSERT = "c"  # Create / Insert
    UPDATE = "u"  # Update
    DELETE = "d"  # Delete
    READ = "r"    # Initial Snapshot Read


@dataclass
class CDCRecord:
    operation: CDCOperation
    source_table: str
    source_schema: str
    lsn: int                    # Log Sequence Number
    tx_id: int                  # PostgreSQL Transaction ID
    timestamp_ms: int
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None


class CDCIngestionEngine:
    """
    Parses, validates, and transforms Debezium CDC envelopes into Delta Lake Bronze append events.
    """

    def __init__(self, target_bronze_table: str = "raw_cdc_events_bronze"):
        self.target_bronze_table = target_bronze_table
        self.processed_records: List[CDCRecord] = []

    def parse_debezium_payload(self, raw_json_str: str) -> CDCRecord:
        data = json.loads(raw_json_str)
        payload = data.get("payload", data)
        source = payload.get("source", {})

        return CDCRecord(
            operation=CDCOperation(payload.get("op", "c")),
            source_table=source.get("table", "unknown_table"),
            source_schema=source.get("schema", "public"),
            lsn=source.get("lsn", 0),
            tx_id=source.get("txId", 0),
            timestamp_ms=payload.get("ts_ms", int(time.time() * 1000)),
            before_state=payload.get("before"),
            after_state=payload.get("after"),
        )

    def route_to_bronze(self, cdc_record: CDCRecord) -> Dict[str, Any]:
        """
        Formats the CDC record into a standardized Delta Lake Bronze append row.
        """
        self.processed_records.append(cdc_record)
        return {
            "ingest_timestamp": time.time(),
            "source_table": cdc_record.source_table,
            "operation": cdc_record.operation.value,
            "lsn": cdc_record.lsn,
            "primary_key": (cdc_record.after_state or cdc_record.before_state or {}).get("id", "unknown"),
            "data_payload": cdc_record.after_state or cdc_record.before_state or {},
            "is_deleted": cdc_record.operation == CDCOperation.DELETE,
            "lakehouse_layer": "BRONZE"
        }


# Global Singleton CDC Engine
cdc_engine = CDCIngestionEngine()
