"""
Nexus-AI: Zomato Restaurant Data Generator
==========================================
Generates realistic synthetic restaurant data with geospatial coordinates,
cuisine diversity, pricing tiers, and rating distributions that mirror
real-world Zomato patterns.
"""

import csv
import random
from pathlib import Path

from faker import Faker

fake = Faker("en_IN")  # Indian locale for Zomato realism
Faker.seed(42)
random.seed(42)

# ── City Coordinates (Major Indian Metro Cities) ──────────────────────────
CITIES = {
    "Mumbai": {"lat": 19.0760, "lng": 72.8777, "spread": 0.15},
    "Delhi": {"lat": 28.7041, "lng": 77.1025, "spread": 0.12},
    "Bangalore": {"lat": 12.9716, "lng": 77.5946, "spread": 0.10},
    "Hyderabad": {"lat": 17.3850, "lng": 78.4867, "spread": 0.08},
    "Chennai": {"lat": 13.0827, "lng": 80.2707, "spread": 0.07},
    "Kolkata": {"lat": 22.5726, "lng": 88.3639, "spread": 0.08},
    "Pune": {"lat": 18.5204, "lng": 73.8567, "spread": 0.06},
    "Ahmedabad": {"lat": 23.0225, "lng": 72.5714, "spread": 0.07},
    "Jaipur": {"lat": 26.9124, "lng": 75.7873, "spread": 0.05},
    "Lucknow": {"lat": 26.8467, "lng": 80.9462, "spread": 0.05},
}

# ── Cuisine Categories ────────────────────────────────────────────────────
CUISINES = {
    "North Indian": {"weight": 0.18, "avg_cost": 450, "premium_mult": 2.5},
    "South Indian": {"weight": 0.12, "avg_cost": 300, "premium_mult": 2.0},
    "Chinese": {"weight": 0.10, "avg_cost": 400, "premium_mult": 2.2},
    "Fast Food": {"weight": 0.09, "avg_cost": 250, "premium_mult": 1.8},
    "Biryani": {"weight": 0.08, "avg_cost": 350, "premium_mult": 2.0},
    "Pizza": {"weight": 0.07, "avg_cost": 500, "premium_mult": 2.5},
    "Street Food": {"weight": 0.06, "avg_cost": 150, "premium_mult": 1.5},
    "Mughlai": {"weight": 0.05, "avg_cost": 550, "premium_mult": 3.0},
    "Continental": {"weight": 0.05, "avg_cost": 700, "premium_mult": 3.5},
    "Italian": {"weight": 0.04, "avg_cost": 800, "premium_mult": 3.0},
    "Japanese": {"weight": 0.03, "avg_cost": 900, "premium_mult": 3.5},
    "Thai": {"weight": 0.03, "avg_cost": 650, "premium_mult": 2.8},
    "Mexican": {"weight": 0.02, "avg_cost": 600, "premium_mult": 2.5},
    "Desserts": {"weight": 0.04, "avg_cost": 200, "premium_mult": 2.0},
    "Beverages": {"weight": 0.04, "avg_cost": 180, "premium_mult": 2.0},
}

CUISINE_NAMES = list(CUISINES.keys())
CUISINE_WEIGHTS = [CUISINES[c]["weight"] for c in CUISINE_NAMES]

# ── Restaurant Name Templates ─────────────────────────────────────────────
PREFIXES = [
    "The", "Royal", "Spice", "Golden", "Grand", "Urban", "Fresh", "Green",
    "Blue", "Red", "Little", "Big", "Taste", "Flavour", "Aroma", "Saffron",
    "Curry", "Masala", "Tandoor", "Hungry",
]
SUFFIXES = [
    "Kitchen", "Café", "Bistro", "Dhaba", "Lounge", "Express", "House",
    "Corner", "Junction", "Hub", "Palace", "Garden", "Point", "Den",
    "Stop", "Bites", "Grill", "Oven", "Wok", "Bowl",
]


def _generate_restaurant_name() -> str:
    """Generate a realistic restaurant name."""
    style = random.choice(["prefix_suffix", "owner_suffix", "cuisine_suffix"])
    if style == "prefix_suffix":
        return f"{random.choice(PREFIXES)} {random.choice(SUFFIXES)}"
    elif style == "owner_suffix":
        return f"{fake.first_name()}'s {random.choice(SUFFIXES)}"
    else:
        return f"{random.choice(CUISINE_NAMES)} {random.choice(SUFFIXES)}"


def _jitter_coord(base: float, spread: float) -> float:
    """Add realistic jitter to base coordinates."""
    return round(base + random.uniform(-spread, spread), 6)


def generate_restaurants(n: int = 5000, output_dir: str = "data/raw") -> Path:
    """
    Generate n synthetic restaurants and write to CSV.

    Returns the path to the generated file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    filepath = output_path / "restaurants.csv"

    fieldnames = [
        "restaurant_id",
        "name",
        "cuisine_type",
        "city",
        "area",
        "latitude",
        "longitude",
        "avg_cost_for_two",
        "rating",
        "total_reviews",
        "is_premium",
        "has_online_delivery",
        "has_table_booking",
        "is_active",
    ]

    used_names: set[str] = set()

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(1, n + 1):
            # Ensure unique names
            name = _generate_restaurant_name()
            while name in used_names:
                name = _generate_restaurant_name()
            used_names.add(name)

            # Weighted city selection (larger cities get more restaurants)
            city_name = random.choices(
                list(CITIES.keys()),
                weights=[30, 25, 20, 10, 8, 7, 5, 3, 1, 1],
                k=1,
            )[0]
            city = CITIES[city_name]

            # Weighted cuisine selection
            cuisine = random.choices(CUISINE_NAMES, weights=CUISINE_WEIGHTS, k=1)[0]
            cuisine_info = CUISINES[cuisine]

            # Premium restaurant flag (top 15%)
            is_premium = random.random() < 0.15

            # Cost calculation with cuisine-based pricing
            base_cost = cuisine_info["avg_cost"]
            if is_premium:
                cost = int(base_cost * random.uniform(1.5, cuisine_info["premium_mult"]))
            else:
                cost = int(base_cost * random.uniform(0.6, 1.4))

            # Rating distribution (realistic: most between 3.0-4.5)
            if is_premium:
                rating = round(random.gauss(4.2, 0.3), 1)
            else:
                rating = round(random.gauss(3.6, 0.5), 1)
            rating = max(1.0, min(5.0, rating))

            # Total reviews correlated with rating and premium status
            base_reviews = random.randint(10, 500)
            if is_premium:
                base_reviews = int(base_reviews * random.uniform(2.0, 5.0))
            if rating >= 4.0:
                base_reviews = int(base_reviews * 1.5)

            writer.writerow(
                {
                    "restaurant_id": f"REST-{i:05d}",
                    "name": name,
                    "cuisine_type": cuisine,
                    "city": city_name,
                    "area": fake.city_suffix() + " " + fake.street_name(),
                    "latitude": _jitter_coord(city["lat"], city["spread"]),
                    "longitude": _jitter_coord(city["lng"], city["spread"]),
                    "avg_cost_for_two": cost,
                    "rating": rating,
                    "total_reviews": base_reviews,
                    "is_premium": is_premium,
                    "has_online_delivery": random.random() < 0.75,
                    "has_table_booking": random.random() < 0.40,
                    "is_active": random.random() < 0.92,
                }
            )

    print(f"✅ Generated {n:,} restaurants → {filepath}")
    return filepath


if __name__ == "__main__":
    generate_restaurants()
