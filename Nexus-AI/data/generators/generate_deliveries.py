"""
Nexus-AI: Zomato Deliveries Data Generator
============================================
Generates realistic delivery records with:
- Estimated vs actual ETA (with noise for ML training)
- Distance-based delivery times
- Delivery partner performance profiles
- Weather and traffic impact simulation
- This is the PRIMARY ML PREDICTION TARGET for the MLOps pipeline
"""

import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

fake = Faker("en_IN")
Faker.seed(42)
random.seed(42)

# ── Delivery Partner Configuration ────────────────────────────────────────
N_DELIVERY_PARTNERS = 2000

PARTNER_TIERS = {
    "Gold": {"weight": 0.10, "speed_mult": 1.2, "rating_base": 4.5},
    "Silver": {"weight": 0.30, "speed_mult": 1.0, "rating_base": 4.0},
    "Bronze": {"weight": 0.60, "speed_mult": 0.85, "rating_base": 3.5},
}

WEATHER_CONDITIONS = {
    "Clear": {"weight": 0.55, "delay_mult": 1.0},
    "Cloudy": {"weight": 0.20, "delay_mult": 1.05},
    "Rain": {"weight": 0.15, "delay_mult": 1.35},
    "Heavy Rain": {"weight": 0.05, "delay_mult": 1.60},
    "Storm": {"weight": 0.02, "delay_mult": 2.00},
    "Fog": {"weight": 0.03, "delay_mult": 1.25},
}

TRAFFIC_LEVELS = {
    "Low": {"weight": 0.25, "delay_mult": 0.85},
    "Medium": {"weight": 0.40, "delay_mult": 1.00},
    "High": {"weight": 0.25, "delay_mult": 1.30},
    "Jam": {"weight": 0.10, "delay_mult": 1.70},
}

VEHICLE_TYPES = {
    "Bike": {"weight": 0.60, "speed_kmh": 25},
    "Scooter": {"weight": 0.25, "speed_kmh": 22},
    "Bicycle": {"weight": 0.10, "speed_kmh": 12},
    "Car": {"weight": 0.05, "speed_kmh": 20},
}


def _load_orders(raw_dir: str) -> list[dict]:
    """Load orders that were delivered to generate corresponding delivery records."""
    filepath = Path(raw_dir) / "orders.csv"
    if not filepath.exists():
        raise FileNotFoundError(
            f"Orders data not found at {filepath}. "
            "Run generate_orders.py first."
        )
    orders = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["order_status"] == "Delivered" and row["delivery_time"]:
                orders.append(row)
    return orders


def _load_restaurants(raw_dir: str) -> dict[str, dict]:
    """Load restaurant coordinates for distance calculation."""
    filepath = Path(raw_dir) / "restaurants.csv"
    restaurants = {}
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            restaurants[row["restaurant_id"]] = row
    return restaurants


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points on Earth in kilometers."""
    R = 6371  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _generate_partner_profiles(n: int) -> list[dict]:
    """Generate delivery partner profiles with performance tiers."""
    partners = []
    tier_names = list(PARTNER_TIERS.keys())
    tier_weights = [PARTNER_TIERS[t]["weight"] for t in tier_names]

    for i in range(1, n + 1):
        tier = random.choices(tier_names, weights=tier_weights, k=1)[0]
        tier_info = PARTNER_TIERS[tier]

        partners.append(
            {
                "partner_id": f"DLV-{i:05d}",
                "partner_name": fake.name(),
                "tier": tier,
                "speed_mult": tier_info["speed_mult"],
                "rating": round(
                    max(1.0, min(5.0, random.gauss(tier_info["rating_base"], 0.3))),
                    1,
                ),
                "total_deliveries": random.randint(50, 5000),
            }
        )
    return partners


def generate_deliveries(
    output_dir: str = "data/raw",
    n_partners: int = N_DELIVERY_PARTNERS,
) -> Path:
    """
    Generate delivery records for all delivered orders.

    Features generated:
    - Distance (km) between restaurant and customer
    - Estimated ETA (what the system predicted)
    - Actual ETA (what actually happened — with noise for ML)
    - Weather and traffic conditions (delay factors)
    - Delivery partner tier and vehicle type

    Returns the path to the generated file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    filepath = output_path / "deliveries.csv"

    orders = _load_orders(output_dir)
    restaurants = _load_restaurants(output_dir)
    partners = _generate_partner_profiles(n_partners)

    weather_names = list(WEATHER_CONDITIONS.keys())
    weather_weights = [WEATHER_CONDITIONS[w]["weight"] for w in weather_names]
    traffic_names = list(TRAFFIC_LEVELS.keys())
    traffic_weights = [TRAFFIC_LEVELS[t]["weight"] for t in traffic_names]
    vehicle_names = list(VEHICLE_TYPES.keys())
    vehicle_weights = [VEHICLE_TYPES[v]["weight"] for v in vehicle_names]

    fieldnames = [
        "delivery_id",
        "order_id",
        "restaurant_id",
        "partner_id",
        "partner_tier",
        "vehicle_type",
        "distance_km",
        "estimated_eta_min",
        "actual_eta_min",
        "pickup_time",
        "delivery_time",
        "weather_condition",
        "traffic_level",
        "preparation_time_min",
        "delivery_rating",
        "is_late",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, order in enumerate(orders, 1):
            restaurant = restaurants.get(order["restaurant_id"])
            if not restaurant:
                continue

            partner = random.choice(partners)

            # Calculate delivery distance (restaurant to random customer location)
            rest_lat = float(restaurant["latitude"])
            rest_lng = float(restaurant["longitude"])
            # Customer is within 1-12 km radius
            cust_lat = rest_lat + random.uniform(-0.08, 0.08)
            cust_lng = rest_lng + random.uniform(-0.08, 0.08)
            distance = round(_haversine_km(rest_lat, rest_lng, cust_lat, cust_lng), 2)
            distance = max(0.5, min(15.0, distance))  # Clamp realistic range

            # Environmental conditions
            weather = random.choices(weather_names, weights=weather_weights, k=1)[0]
            traffic = random.choices(traffic_names, weights=traffic_weights, k=1)[0]
            vehicle = random.choices(vehicle_names, weights=vehicle_weights, k=1)[0]

            weather_delay = WEATHER_CONDITIONS[weather]["delay_mult"]
            traffic_delay = TRAFFIC_LEVELS[traffic]["delay_mult"]
            vehicle_speed = VEHICLE_TYPES[vehicle]["speed_kmh"]

            # Preparation time (kitchen time: 10-35 min)
            prep_time = random.gauss(18, 5)
            prep_time = max(8, min(40, prep_time))

            # Estimated ETA (what the system would predict — idealized)
            travel_time = (distance / vehicle_speed) * 60  # minutes
            estimated_eta = round(prep_time + travel_time, 1)

            # Actual ETA (with weather, traffic, partner skill, and random noise)
            actual_travel = travel_time * weather_delay * traffic_delay / partner["speed_mult"]
            actual_eta = round(prep_time + actual_travel + random.gauss(0, 3), 1)
            actual_eta = max(10, actual_eta)  # Minimum 10 minutes

            # Timing
            order_time = datetime.strptime(order["order_time"], "%Y-%m-%d %H:%M:%S")
            pickup_time = order_time + timedelta(minutes=prep_time)
            delivery_time = order_time + timedelta(minutes=actual_eta)

            # Delivery rating (correlated with lateness and partner quality)
            is_late = actual_eta > estimated_eta * 1.15  # Late if >15% over estimate
            if is_late:
                rating = round(max(1.0, random.gauss(3.0, 0.8)), 1)
            else:
                rating = round(max(1.0, min(5.0, random.gauss(4.3, 0.4))), 1)

            writer.writerow(
                {
                    "delivery_id": f"DEL-{i:07d}",
                    "order_id": order["order_id"],
                    "restaurant_id": order["restaurant_id"],
                    "partner_id": partner["partner_id"],
                    "partner_tier": partner["tier"],
                    "vehicle_type": vehicle,
                    "distance_km": distance,
                    "estimated_eta_min": round(estimated_eta, 1),
                    "actual_eta_min": round(actual_eta, 1),
                    "pickup_time": pickup_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "delivery_time": delivery_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "weather_condition": weather,
                    "traffic_level": traffic,
                    "preparation_time_min": round(prep_time, 1),
                    "delivery_rating": rating,
                    "is_late": is_late,
                }
            )

    print(f"✅ Generated {len(orders):,} deliveries → {filepath}")
    return filepath


if __name__ == "__main__":
    generate_deliveries()
