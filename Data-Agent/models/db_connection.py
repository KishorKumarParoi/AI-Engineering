import os 
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Database configuration with flexible fallbacks
DB_CONFIG = {
    "host": os.getenv('host') or os.getenv('POSTGRES_HOST', 'localhost'),
    "user": os.getenv('user') or os.getenv('POSTGRES_USER', 'postgres'),
    "password": os.getenv('password') or os.getenv('POSTGRES_PASSWORD', 'postgres'),
    "database": os.getenv('database') or os.getenv('POSTGRES_DB', 'data_agent_db'),
    "port": int(os.getenv('port') or os.getenv('POSTGRES_PORT', '5432'))
}

CSV_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = False

cursor = conn.cursor()
print("Connected to PostgreSQL successfully!")

# SQL DDL for Ride-sharing Data Agent Schema
create_tables_sql = """
CREATE SCHEMA IF NOT EXISTS public;

CREATE TABLE IF NOT EXISTS public.users (
    user_id INTEGER PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(50),
    city VARCHAR(100),
    province VARCHAR(100),
    user_type VARCHAR(50) NOT NULL,
    signup_date DATE,
    is_active BOOLEAN,
    created_at TIMESTAMP
);

-- Vehicles
CREATE TABLE IF NOT EXISTS public.vehicles (
    vehicle_id INTEGER PRIMARY KEY,
    driver_id INTEGER NOT NULL,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INTEGER,
    license_plate VARCHAR(20),
    insurance_provider VARCHAR(100),
    color VARCHAR(50),
    is_active BOOLEAN,
    created_at TIMESTAMP,
    CONSTRAINT fk_vehicle_driver
        FOREIGN KEY (driver_id)
        REFERENCES public.users(user_id)
);

-- Rides
CREATE TABLE IF NOT EXISTS public.rides (
    ride_id INTEGER PRIMARY KEY,
    rider_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    requested_at TIMESTAMP,
    pickup_time TIMESTAMP,
    dropoff_time TIMESTAMP,
    pickup_latitude DECIMAL(9,6),
    pickup_longitude DECIMAL(9,6),
    dropoff_latitude DECIMAL(9,6),
    dropoff_longitude DECIMAL(9,6),
    distance_km DECIMAL(10,2),
    fare DECIMAL(10,2),
    surge_multiplier DECIMAL(4,2),
    status VARCHAR(30),
    cancellation_reason VARCHAR(100),
    CONSTRAINT fk_ride_rider
        FOREIGN KEY (rider_id)
        REFERENCES public.users(user_id),
    CONSTRAINT fk_ride_driver
        FOREIGN KEY (driver_id)
        REFERENCES public.users(user_id)
);

-- Payments
CREATE TABLE IF NOT EXISTS public.payments (
    payment_id INTEGER PRIMARY KEY,
    ride_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    payment_method VARCHAR(50),
    amount DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(50),
    transaction_id VARCHAR(100) UNIQUE,
    payment_time TIMESTAMP,
    created_at TIMESTAMP,
    CONSTRAINT fk_payments_rides
        FOREIGN KEY (ride_id)
        REFERENCES public.rides(ride_id)
);

-- Ratings
CREATE TABLE IF NOT EXISTS public.ratings (
    rating_id INTEGER PRIMARY KEY,
    ride_id INTEGER NOT NULL,
    rider_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    rated_at TIMESTAMP,
    created_at TIMESTAMP,
    CONSTRAINT fk_ratings_rides
        FOREIGN KEY (ride_id)
        REFERENCES public.rides(ride_id),
    CONSTRAINT fk_rating_rider
        FOREIGN KEY (rider_id)
        REFERENCES public.users(user_id),
    CONSTRAINT fk_rating_driver
        FOREIGN KEY (driver_id)
        REFERENCES public.users(user_id),
    CONSTRAINT chk_rating
        CHECK (rating BETWEEN 1 AND 5)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_vehicles_driver_id ON public.vehicles(driver_id);
CREATE INDEX IF NOT EXISTS idx_rides_rider_id ON public.rides(rider_id);
CREATE INDEX IF NOT EXISTS idx_rides_driver_id ON public.rides(driver_id);
CREATE INDEX IF NOT EXISTS idx_rides_requested_at ON public.rides(requested_at);
CREATE INDEX IF NOT EXISTS idx_rides_status ON public.rides(status);
CREATE INDEX IF NOT EXISTS idx_payments_ride_id ON public.payments(ride_id);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON public.payments(user_id);
CREATE INDEX IF NOT EXISTS idx_ratings_ride_id ON public.ratings(ride_id);
CREATE INDEX IF NOT EXISTS idx_ratings_rider_id ON public.ratings(rider_id);
CREATE INDEX IF NOT EXISTS idx_ratings_driver_id ON public.ratings(driver_id);
"""

cursor.execute(create_tables_sql)
print("Tables Created Successfully!")

# Truncate tables before loading fresh data
cursor.execute("""
TRUNCATE TABLE 
public.ratings,
public.payments,
public.rides,
public.vehicles,
public.users
CASCADE;
""")
print("Tables Truncated Successfully!")


def load_csv(table_name, csv_file, columns):
    file_path = os.path.join(CSV_DIR, csv_file)

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"CSV file not found: {file_path}"
        )
    
    copy_sql = sql.SQL("""
    COPY {}.{} ({})
    FROM STDIN
    WITH (
        FORMAT CSV,
        HEADER TRUE,
        DELIMITER ',',
        NULL ''
    )
    """).format(
        sql.Identifier("public"),
        sql.Identifier(table_name),
        sql.SQL(", ").join(
            sql.Identifier(column)
            for column in columns
        )
    )

    with open(file_path, "r", encoding="utf-8") as file:
        cursor.copy_expert(copy_sql, file)

    print(f"Loaded data from {csv_file} into {table_name}")


# Load CSV files into tables
load_csv(
    "users",
    "users.csv",
    [
        "user_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "city",
        "province",
        "user_type",
        "signup_date",
        "is_active",
        "created_at"
    ]
)

load_csv(
    "vehicles",
    "vehicles.csv",
    [
        "vehicle_id",
        "driver_id",
        "make",
        "model",
        "year",
        "license_plate",
        "insurance_provider",
        "color",
        "is_active",
        "created_at"
    ]
)

load_csv(
    "rides",
    "rides.csv",
    [
        "ride_id",
        "rider_id",
        "driver_id",
        "requested_at",
        "pickup_time",
        "dropoff_time",
        "pickup_latitude",
        "pickup_longitude",
        "dropoff_latitude",
        "dropoff_longitude",
        "distance_km",
        "fare",
        "surge_multiplier",
        "status",
        "cancellation_reason"
    ]
)

load_csv(
    "payments",
    "payments.csv",
    [
        "payment_id",
        "ride_id",
        "user_id",
        "payment_method",
        "amount",
        "payment_status",
        "transaction_id",
        "payment_time",
        "created_at"
    ]
)

load_csv(
    "ratings",
    "ratings.csv",
    [
        "rating_id",
        "ride_id",
        "rider_id",
        "driver_id",
        "rating",
        "comment",
        "rated_at",
        "created_at"
    ]
)

tables = [
    "users",
    "vehicles",
    "rides",
    "payments",
    "ratings"
]

print("\nRecord Counts:")
print("-" * 40)

for table in tables:
    cursor.execute(
        sql.SQL(
            "SELECT COUNT(*) FROM {}.{}"
        ).format(
            sql.Identifier("public"),
            sql.Identifier(table)
        )
    )
    count = cursor.fetchone()[0]
    print(f"{table}: {count} records")

conn.commit()

print("\nData Loaded successfully!")
print("Transaction committed.")

cursor.close()
conn.close()

print("PostgreSQL connection closed.")