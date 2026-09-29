"""
Nexus-AI: Zomato Reviews Data Generator
=========================================
Generates realistic customer reviews with:
- Sentiment-aware text generation (positive/negative/neutral)
- Rating-correlated review text
- Verified purchase flags
- Helpful vote counts
- Aspect-based sentiment tags (food, service, delivery, ambiance)
"""

import csv
import random
from pathlib import Path

from faker import Faker

fake = Faker("en_IN")
Faker.seed(42)
random.seed(42)

# ── Review Templates (Sentiment-Aware) ────────────────────────────────────
POSITIVE_REVIEWS = [
    "Absolutely amazing food! The {cuisine} was authentic and flavorful.",
    "Best {cuisine} I've had in {city}. Will definitely order again!",
    "Quick delivery, hot food, perfect packaging. 10/10 experience.",
    "The portions were generous and the taste was incredible.",
    "Loved every bite! The chef clearly knows their craft.",
    "Outstanding quality for the price. This is my go-to restaurant now.",
    "Fresh ingredients, great taste, and the delivery was super fast.",
    "Exceeded expectations! The {cuisine} here is restaurant-quality.",
    "My family loved it. We've already placed our second order!",
    "Consistent quality every time I order. Highly recommended.",
    "The food arrived piping hot and tasted freshly prepared.",
    "Great value for money. The combo meal is a steal!",
    "The spice levels were perfect. Not too mild, not too hot.",
    "Professional packaging, nothing spilled. Food was delicious.",
    "Been ordering from here for months. Never disappoints!",
]

NEUTRAL_REVIEWS = [
    "Food was decent but nothing extraordinary. Average {cuisine}.",
    "Okay experience. Delivery was on time but food was lukewarm.",
    "Standard {cuisine} fare. Gets the job done when you're hungry.",
    "Reasonable portion sizes. Taste was average.",
    "It's alright for the price but I've had better {cuisine}.",
    "Delivery was a bit delayed but the food quality was acceptable.",
    "Not bad, not great. Solid 3-star experience.",
    "The food was okay but the packaging could be better.",
    "Average taste. Would try something different next time.",
    "Decent option for late-night cravings. Nothing special though.",
]

NEGATIVE_REVIEWS = [
    "Very disappointed. The {cuisine} was bland and overpriced.",
    "Food arrived cold and the packaging was leaking. Not acceptable.",
    "Terrible experience. The order was wrong and support was unhelpful.",
    "Way too oily and the portions were tiny for the price.",
    "Delivery took over an hour and the food was stale by then.",
    "Found a hair in my food. Absolutely disgusting. Never ordering again.",
    "The taste was nothing like what's shown in the photos.",
    "Rude delivery partner and the food was missing items.",
    "Worst {cuisine} I've ever had. Complete waste of money.",
    "Quality has dropped significantly since my last order. Very sad.",
]

# ── Aspect Sentiment Tags ────────────────────────────────────────────────
ASPECTS = ["food_quality", "delivery_speed", "packaging", "value_for_money", "portion_size"]


def _get_review_text(rating: float, cuisine: str, city: str) -> str:
    """Select a review template based on rating and fill placeholders."""
    if rating >= 4.0:
        template = random.choice(POSITIVE_REVIEWS)
    elif rating >= 2.5:
        template = random.choice(NEUTRAL_REVIEWS)
    else:
        template = random.choice(NEGATIVE_REVIEWS)

    return template.format(cuisine=cuisine, city=city)


def _generate_aspect_sentiments(rating: float) -> dict[str, str]:
    """Generate aspect-level sentiments correlated with overall rating."""
    sentiments = {}
    for aspect in ASPECTS:
        noise = random.gauss(0, 0.5)
        adjusted = rating + noise
        if adjusted >= 4.0:
            sentiments[aspect] = "positive"
        elif adjusted >= 2.5:
            sentiments[aspect] = "neutral"
        else:
            sentiments[aspect] = "negative"
    return sentiments


def _load_orders_with_restaurants(raw_dir: str) -> list[dict]:
    """Load orders and merge with restaurant info for context."""
    orders_path = Path(raw_dir) / "orders.csv"
    restaurants_path = Path(raw_dir) / "restaurants.csv"

    # Load restaurants into lookup
    restaurants = {}
    with open(restaurants_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            restaurants[row["restaurant_id"]] = row

    # Load delivered orders and enrich
    enriched = []
    with open(orders_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["order_status"] == "Delivered":
                rest = restaurants.get(row["restaurant_id"], {})
                row["cuisine_type"] = rest.get("cuisine_type", "Mixed")
                row["city"] = rest.get("city", "Mumbai")
                enriched.append(row)

    return enriched


def generate_reviews(
    n: int = 50_000,
    output_dir: str = "data/raw",
) -> Path:
    """
    Generate n synthetic reviews linked to delivered orders.

    Returns the path to the generated file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    filepath = output_path / "reviews.csv"

    orders = _load_orders_with_restaurants(output_dir)

    fieldnames = [
        "review_id",
        "order_id",
        "restaurant_id",
        "customer_id",
        "rating",
        "review_text",
        "review_date",
        "is_verified_purchase",
        "helpful_votes",
        "food_quality_sentiment",
        "delivery_speed_sentiment",
        "packaging_sentiment",
        "value_for_money_sentiment",
        "portion_size_sentiment",
    ]

    # Not every order gets a review; sample a subset
    reviewed_orders = random.sample(orders, min(n, len(orders)))

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, order in enumerate(reviewed_orders, 1):
            # Rating distribution: realistic — most orders 3-5 stars
            rating = round(
                max(1.0, min(5.0, random.choices(
                    [1.0, 2.0, 3.0, 4.0, 5.0],
                    weights=[0.05, 0.08, 0.17, 0.35, 0.35],
                    k=1,
                )[0] + random.uniform(-0.4, 0.4))),
                1,
            )

            review_text = _get_review_text(
                rating, order["cuisine_type"], order["city"]
            )

            aspects = _generate_aspect_sentiments(rating)

            # Review date: 0-7 days after delivery
            order_time = order.get("delivery_time") or order.get("order_time", "2024-06-15 12:00:00")

            # Helpful votes: high-rated or very-low-rated reviews get more
            if rating >= 4.5 or rating <= 2.0:
                helpful = random.randint(0, 25)
            else:
                helpful = random.randint(0, 5)

            writer.writerow(
                {
                    "review_id": f"REV-{i:06d}",
                    "order_id": order["order_id"],
                    "restaurant_id": order["restaurant_id"],
                    "customer_id": order["customer_id"],
                    "rating": rating,
                    "review_text": review_text,
                    "review_date": order_time,
                    "is_verified_purchase": random.random() < 0.90,
                    "helpful_votes": helpful,
                    "food_quality_sentiment": aspects["food_quality"],
                    "delivery_speed_sentiment": aspects["delivery_speed"],
                    "packaging_sentiment": aspects["packaging"],
                    "value_for_money_sentiment": aspects["value_for_money"],
                    "portion_size_sentiment": aspects["portion_size"],
                }
            )

    print(f"✅ Generated {len(reviewed_orders):,} reviews → {filepath}")
    return filepath


if __name__ == "__main__":
    generate_reviews()
