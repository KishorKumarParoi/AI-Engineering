"""
Nexus-AI: Zomato Orders Data Generator
=======================================
Generates realistic order data with temporal patterns (lunch/dinner peaks),
payment method distributions, discount logic, and realistic order values
tied to restaurant pricing tiers.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

fake = Faker("en_IN")
Faker.seed(42)
random.seed(42)

# ── Order Configuration ──────────────────────────────────────────────────
PAYMENT_METHODS = {
    "UPI": 0.40,
    "Credit Card": 0.20,
    "Debit Card": 0.15,
    "Cash on Delivery": 0.15,
    "Wallet": 0.10,
}

ORDER_STATUSES = {
    "Delivered": 0.82,
    "Cancelled": 0.08,
    "Returned": 0.03,
    "In Transit": 0.04,
    "Preparing": 0.03,
}

# Hourly order probability (0-23h) — peaks at lunch (12-14) and dinner (19-21)
HOURLY_WEIGHTS = [
    0.01, 0.005, 0.003, 0.002, 0.002, 0.005,  # 0-5 AM
    0.01, 0.02, 0.04, 0.05, 0.06, 0.08,        # 6-11 AM
    0.10, 0.09, 0.06, 0.04, 0.03, 0.04,         # 12-17 PM (lunch peak)
    0.06, 0.09, 0.11, 0.10, 0.07, 0.04,         # 18-23 PM (dinner peak)
]


def _load_restaurants(raw_dir: str) -> list[dict]:
    """Load restaurant data to link orders to real restaurant IDs and costs."""
    filepath = Path(raw_dir) / "restaurants.csv"
    if not filepath.exists():
        raise FileNotFoundError(
            f"Restaurant data not found at {filepath}. "
            "Run generate_restaurants.py first."
        )
    restaurants = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["is_active"].lower() == "true":
                restaurants.append(row)
    return restaurants


def _random_datetime_in_range(
    start: datetime, end: datetime, hourly_weights: list[float]
) -> datetime:
    """Generate a random datetime biased toward lunch/dinner peaks."""
    # Pick a random day
    delta_days = (end - start).days
    random_day = start + timedelta(days=random.randint(0, delta_days))

    # Pick an hour weighted by meal patterns
    hour = random.choices(range(24), weights=hourly_weights, k=1)[0]
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    return random_day.replace(hour=hour, minute=minute, second=second)


def generate_orders(
    n: int = 100_000,
    output_dir: str = "data/raw",
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
) -> Path:
    """
    Generate n synthetic orders linked to existing restaurants.

    Returns the path to the generated file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    filepath = output_path / "orders.csv"

    restaurants = _load_restaurants(output_dir)
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    payment_methods = list(PAYMENT_METHODS.keys())
    payment_weights = list(PAYMENT_METHODS.values())
    status_list = list(ORDER_STATUSES.keys())
    status_weights = list(ORDER_STATUSES.values())

    fieldnames = [
        "order_id",
        "restaurant_id",
        "customer_id",
        "order_time",
        "delivery_time",
        "total_amount",
        "discount_amount",
        "tax_amount",
        "net_amount",
        "payment_method",
        "order_status",
        "items_count",
        "is_first_order",
        "platform_fee",
        "delivery_fee",
    ]

    # Generate a pool of customer IDs (returning customers are realistic)
    n_customers = int(n * 0.3)  # 30% unique customers = repeat orders
    customer_pool = [f"CUST-{i:06d}" for i in range(1, n_customers + 1)]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        customer_order_counts: dict[str, int] = {}

        for i in range(1, n + 1):
            restaurant = random.choice(restaurants)
            customer_id = random.choice(customer_pool)
            customer_order_counts[customer_id] = customer_order_counts.get(customer_id, 0) + 1

            order_time = _random_datetime_in_range(start, end, HOURLY_WEIGHTS)
            status = random.choices(status_list, weights=status_weights, k=1)[0]

            # Delivery time (30-75 min after order, None if not delivered)
            if status == "Delivered":
                delivery_minutes = random.gauss(45, 12)
                delivery_minutes = max(20, min(90, delivery_minutes))
                delivery_time = order_time + timedelta(minutes=delivery_minutes)
            else:
                delivery_time = ""

            # Order value based on restaurant pricing
            avg_cost = int(restaurant["avg_cost_for_two"])
            items_count = random.choices([1, 2, 3, 4, 5], weights=[0.15, 0.35, 0.30, 0.15, 0.05], k=1)[0]
            base_amount = int((avg_cost / 2) * items_count * random.uniform(0.7, 1.3))

            # Discount logic (20% of orders have discounts)
            has_discount = random.random() < 0.20
            if has_discount:
                discount_pct = random.choice([10, 15, 20, 25, 30, 40, 50])
                discount_amount = int(base_amount * discount_pct / 100)
                discount_amount = min(discount_amount, 200)  # Cap at ₹200
            else:
                discount_amount = 0

            # Tax (5% GST)
            tax_amount = int((base_amount - discount_amount) * 0.05)

            # Fees
            platform_fee = random.choice([0, 5, 10, 15])
            delivery_fee = random.choice([0, 20, 30, 40, 50]) if base_amount < 500 else 0

            net_amount = base_amount - discount_amount + tax_amount + platform_fee + delivery_fee

            writer.writerow(
                {
                    "order_id": f"ORD-{i:07d}",
                    "restaurant_id": restaurant["restaurant_id"],
                    "customer_id": customer_id,
                    "order_time": order_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "delivery_time": delivery_time.strftime("%Y-%m-%d %H:%M:%S") if delivery_time else "",
                    "total_amount": base_amount,
                    "discount_amount": discount_amount,
                    "tax_amount": tax_amount,
                    "net_amount": net_amount,
                    "payment_method": random.choices(payment_methods, weights=payment_weights, k=1)[0],
                    "order_status": status,
                    "items_count": items_count,
                    "is_first_order": customer_order_counts[customer_id] == 1,
                    "platform_fee": platform_fee,
                    "delivery_fee": delivery_fee,
                }
            )

    print(f"✅ Generated {n:,} orders → {filepath}")
    return filepath


if __name__ == "__main__":
    generate_orders()
