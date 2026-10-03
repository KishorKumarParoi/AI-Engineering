"""
Zomato Enterprise Lakehouse: Kafka High-Throughput Stream Producer
Simulates live order events and rider GPS telemetry for Databricks consumption.

Features:
  - Emits JSON order events matching `zomato.order_events`
  - Simulates burst rates (e.g. 100 to 5,000 events/sec)
  - Connects to Kafka broker (default: localhost:9092 from services/docker-compose.yml)
"""

import json
import time
import random
import uuid
from datetime import datetime

try:
    from kafka import KafkaProducer
    HAS_KAFKA = True
except ImportError:
    HAS_KAFKA = False

CITIES = {
    "Bangalore": {"lat": 12.9716, "lng": 77.5946},
    "Mumbai": {"lat": 19.0760, "lng": 72.8777},
    "Delhi": {"lat": 28.7041, "lng": 77.1025},
}

RESTAURANTS = [
    ("rest_101", "Truffles Central", "Bangalore"),
    ("rest_102", "Empire Restaurant", "Bangalore"),
    ("rest_103", "Bastian Bandra", "Mumbai"),
    ("rest_104", "Karim's Historic", "Delhi"),
    ("rest_105", "Meghana Foods", "Bangalore"),
]

ORDER_STATUSES = ["PLACED", "ACCEPTED", "PREPARING", "PICKED_UP", "DELIVERED"]

def generate_order_event():
    rest_id, rest_name, city = random.choice(RESTAURANTS)
    base_coords = CITIES[city]
    
    # Random displacement within 5 km
    rest_lat = base_coords["lat"] + random.uniform(-0.03, 0.03)
    rest_lng = base_coords["lng"] + random.uniform(-0.03, 0.03)
    del_lat = rest_lat + random.uniform(-0.05, 0.05)
    del_lng = rest_lng + random.uniform(-0.05, 0.05)

    return {
        "order_id": f"ORD-{uuid.uuid4().hex[:8].upper()}",
        "customer_id": f"CUST-{random.randint(1000, 9999)}",
        "restaurant_id": rest_id,
        "rider_id": f"RIDER-{random.randint(100, 999)}",
        "order_status": random.choice(ORDER_STATUSES),
        "order_amount": round(random.uniform(180.0, 1450.0), 2),
        "delivery_fee": round(random.choice([25.0, 35.0, 45.0, 60.0]), 2),
        "item_count": random.randint(1, 8),
        "payment_method": random.choice(["UPI", "CREDIT_CARD", "ZOMATO_PAY", "CASH"]),
        "restaurant_lat": round(rest_lat, 6),
        "restaurant_lng": round(rest_lng, 6),
        "delivery_lat": round(del_lat, 6),
        "delivery_lng": round(del_lng, 6),
        "event_timestamp": datetime.utcnow().isoformat() + "Z"
    }

def produce_events(
    bootstrap_servers: str = "localhost:9092",
    topic: str = "zomato.order_events",
    num_events: int = 500,
    rate_per_sec: int = 50
):
    print(f"[*] Starting Kafka Producer: {num_events} events -> [{topic}] at ~{rate_per_sec} evt/sec")
    
    if not HAS_KAFKA:
        print("[!] kafka-python not installed in current environment. Emitting synthetic sample payload:")
        for _ in range(min(5, num_events)):
            print(json.dumps(generate_order_event(), indent=2))
        print("[✓] (Dry run simulated successfully)")
        return

    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: str(k).encode("utf-8"),
        acks=1
    )

    interval = 1.0 / max(rate_per_sec, 1)
    for i in range(num_events):
        event = generate_order_event()
        producer.send(topic, key=event["order_id"], value=event)
        if (i + 1) % 100 == 0:
            print(f"[+] Sent {i + 1}/{num_events} events...")
        time.sleep(interval)

    producer.flush()
    print(f"[✓] Successfully published {num_events} events to {topic}.")

if __name__ == "__main__":
    produce_events(num_events=500, rate_per_sec=100)
