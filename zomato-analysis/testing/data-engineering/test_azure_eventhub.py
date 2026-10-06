#!/usr/bin/env -S uv run python
# -*- coding: utf-8 -*-
"""
Test Suite: testing/data-engineering/test_azure_eventhub.py
Purpose: Azure Event Hubs AMQP Connectivity & Real-time Stream Partition Verification
Tier: Senior Staff / Lead Data Engineer Standard

Validates:
  1. Azure Event Hubs Connection String & Secret Parsing
  2. Live AMQP 1.0 Management Protocol Handshake
  3. Hub Existence, Status, Partition IDs and Live Enqueued Metrics
"""

import os
import sys
import time
import re
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

def print_header(title: str):
    print(f"\n{CYAN}{BOLD}=========================================================={NC}")
    print(f"{CYAN}{BOLD}  {title}{NC}")
    print(f"{CYAN}{BOLD}=========================================================={NC}")

def test_azure_eventhub():
    print_header("AZURE EVENT HUBS REAL-TIME STREAM VERIFICATION")
    
    conn_str = os.getenv("EVENTHUB_CONNECTION_STRING") or os.getenv("CONNECTION_STRING")
    hub_name = os.getenv("EVENT_HUBNAME", "zomato")

    if not conn_str:
        print(f"{RED}[FAIL] Missing EVENTHUB_CONNECTION_STRING in .env!{NC}")
        return False

    try:
        from azure.eventhub import EventHubProducerClient
    except ImportError:
        print(f"{RED}[FAIL] azure-eventhub package is required. Run: uv pip install azure-eventhub{NC}")
        return False

    m = re.search(r'sb://([^.]+)\.servicebus\.windows\.net', conn_str)
    ns = f"{m.group(1)}.servicebus.windows.net" if m else "eventhub-kkp007.servicebus.windows.net"

    print(f"{BLUE}[INFO]{NC} Connecting to Azure Event Hubs Namespace: {BOLD}{ns}{NC} | Hub: {BOLD}{hub_name}{NC}...")

    try:
        client = EventHubProducerClient.from_connection_string(conn_str, eventhub_name=hub_name)
        with client:
            eh_props = client.get_eventhub_properties()
            partitions = eh_props.get("partition_ids", [])
            created_at = eh_props.get("created_at")

            print(f"{GREEN}[PASS]{NC} AMQP 1.0 Handshake Established Successfully!")
            print(f"  - Hub Name:         {hub_name}")
            print(f"  - Namespace:        {ns}")
            print(f"  - Created UTC:      {created_at}")
            print(f"  - Total Partitions: {len(partitions)} ({partitions})")

            total_events = 0
            for p_id in partitions:
                p_props = client.get_partition_properties(p_id)
                beginning_seq = p_props["beginning_sequence_number"]
                last_seq = p_props["last_enqueued_sequence_number"]
                is_empty = p_props["is_empty"]
                count = 0 if is_empty else (last_seq - beginning_seq + 1)
                total_events += count

                status = "EMPTY" if is_empty else f"{GREEN}ACTIVE{NC}"
                print(f"\n  [Partition {p_id}] Status: {status}")
                print(f"    - Enqueued Count:    {count}")
                print(f"    - Last Sequence No:  {last_seq}")
                print(f"    - Last Offset:       {p_props['last_enqueued_offset']}")
                print(f"    - Last Enqueued UTC: {p_props['last_enqueued_time_utc']}")

            print(f"\n{GREEN}[PASS]{NC} Total Live Events in Azure Partition Buffer: {BOLD}{total_events}{NC}")
            print(f"\n{CYAN}{BOLD}=========================================================={NC}")
            print(f"{GREEN}{BOLD}ALL AZURE EVENT HUBS TELEMETRY CHECKS PASSED (100%)!{NC}")
            print(f"{CYAN}{BOLD}=========================================================={NC}")
            return True

    except Exception as e:
        print(f"{RED}[FAIL] Error querying Azure Event Hubs: {e}{NC}")
        return False

if __name__ == "__main__":
    success = test_azure_eventhub()
    sys.exit(0 if success else 1)
