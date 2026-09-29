"""
Nexus-AI: Master Data Seeder
==============================
One-command script that orchestrates all data generators in the correct
dependency order: Restaurants → Orders → Deliveries → Reviews.

Usage:
    python data/generators/seed_all.py [--rows-scale 1.0] [--output-dir data/raw]
"""

import argparse
import sys
import time
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def seed_all(scale: float = 1.0, output_dir: str = "data/raw") -> None:
    """
    Generate all synthetic datasets in dependency order.

    Args:
        scale: Multiplier for row counts (0.1 = small sample, 1.0 = full, 2.0 = stress test)
        output_dir: Output directory for generated CSV files
    """
    from data.generators.generate_deliveries import generate_deliveries
    from data.generators.generate_orders import generate_orders
    from data.generators.generate_restaurants import generate_restaurants
    from data.generators.generate_reviews import generate_reviews

    start_time = time.time()

    print("=" * 70)
    print("🚀 NEXUS-AI: Zomato Lakehouse Data Generator")
    print("=" * 70)
    print(f"   Scale Factor: {scale}x")
    print(f"   Output Dir:   {output_dir}")
    print("=" * 70)

    # ── Step 1: Restaurants (no dependencies) ─────────────────────────────
    print("\n📍 Step 1/4: Generating Restaurants...")
    n_restaurants = int(5_000 * scale)
    generate_restaurants(n=n_restaurants, output_dir=output_dir)

    # ── Step 2: Orders (depends on restaurants) ───────────────────────────
    print("\n📦 Step 2/4: Generating Orders...")
    n_orders = int(100_000 * scale)
    generate_orders(n=n_orders, output_dir=output_dir)

    # ── Step 3: Deliveries (depends on orders + restaurants) ──────────────
    print("\n🚗 Step 3/4: Generating Deliveries...")
    generate_deliveries(output_dir=output_dir)

    # ── Step 4: Reviews (depends on orders + restaurants) ─────────────────
    print("\n⭐ Step 4/4: Generating Reviews...")
    n_reviews = int(50_000 * scale)
    generate_reviews(n=n_reviews, output_dir=output_dir)

    # ── Summary ──────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    output_path = Path(output_dir)
    total_size = sum(f.stat().st_size for f in output_path.glob("*.csv"))

    print("\n" + "=" * 70)
    print("✅ DATA GENERATION COMPLETE")
    print("=" * 70)
    print(f"   Files generated in:  {output_path.resolve()}")
    print(f"   Total size:          {total_size / (1024 * 1024):.1f} MB")
    print(f"   Time elapsed:        {elapsed:.1f}s")
    print("=" * 70)

    # List generated files
    print("\n📄 Generated Files:")
    for csv_file in sorted(output_path.glob("*.csv")):
        # Count rows
        with open(csv_file, "r") as f:
            row_count = sum(1 for _ in f) - 1  # Subtract header
        size_mb = csv_file.stat().st_size / (1024 * 1024)
        print(f"   {csv_file.name:<25s}  {row_count:>10,} rows  ({size_mb:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(
        description="Nexus-AI: Generate all Zomato synthetic datasets"
    )
    parser.add_argument(
        "--rows-scale",
        type=float,
        default=1.0,
        help="Scale factor for row counts (default: 1.0 = full, 0.1 = sample)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Output directory for CSV files (default: data/raw)",
    )
    args = parser.parse_args()

    seed_all(scale=args.rows_scale, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
