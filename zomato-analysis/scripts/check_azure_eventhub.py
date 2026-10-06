#!/usr/bin/env python3
"""
Zomato Enterprise Lakehouse: Azure Event Hubs Live Telemetry Inspector
Queries Microsoft Azure Event Hubs directly via AMQP 1.0 management protocol.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

try:
    from azure.eventhub import EventHubProducerClient
except ImportError:
    print("[Error] azure-eventhub package not installed. Run: pip install azure-eventhub")
    sys.exit(1)

def get_eventhub_telemetry():
    conn_str = os.getenv("EVENTHUB_CONNECTION_STRING") or os.getenv("CONNECTION_STRING")
    hub_name = os.getenv("EVENT_HUBNAME", "zomato")

    if not conn_str:
        print("[Error] No EVENTHUB_CONNECTION_STRING or CONNECTION_STRING found in .env")
        return None

    try:
        import re
        m = re.search(r'sb://([^.]+)\.servicebus\.windows\.net', conn_str)
        ns = f"{m.group(1)}.servicebus.windows.net" if m else "eventhub-kkp007.servicebus.windows.net"

        client = EventHubProducerClient.from_connection_string(conn_str, eventhub_name=hub_name)
        with client:
            eh_props = client.get_eventhub_properties()
            partitions = eh_props["partition_ids"]
            
            print("=" * 65)
            print("📡 LIVE AZURE EVENT HUBS CLOUD TELEMETRY")
            print("=" * 65)
            print(f"• Event Hub Namespace: {ns}")
            print(f"• Hub Name:            {hub_name}")
            print(f"• Created UTC:         {eh_props['created_at']}")
            print(f"• Total Partitions:    {len(partitions)} ({partitions})")
            print("-" * 65)

            total_events_all_partitions = 0
            for p_id in partitions:
                p_props = client.get_partition_properties(p_id)
                beginning_seq = p_props["beginning_sequence_number"]
                last_seq = p_props["last_enqueued_sequence_number"]
                is_empty = p_props["is_empty"]
                
                count = 0 if is_empty else (last_seq - beginning_seq + 1)
                total_events_all_partitions += count

                print(f"  Partition [{p_id}]:")
                print(f"    - Status:                     {'EMPTY' if is_empty else 'ACTIVE'}")
                print(f"    - Total Enqueued Events:      {count}")
                print(f"    - Last Enqueued Sequence No:  {last_seq}")
                print(f"    - Last Enqueued Offset:       {p_props['last_enqueued_offset']}")
                print(f"    - Last Enqueued UTC Time:     {p_props['last_enqueued_time_utc']}")

            print("=" * 65)
            print(f"🎯 Total Live Events Stored in Azure Event Hub: {total_events_all_partitions}")
            print("=" * 65)
            return total_events_all_partitions
    except Exception as e:
        print(f"[Error] Failed to query Azure Event Hubs: {e}")
        return None

if __name__ == "__main__":
    get_eventhub_telemetry()
