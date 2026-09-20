import csv
import os
import random
from datetime import datetime, timedelta

random.seed(42)

OUTPUT_DIR = os.path.dirname(__file__)

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa", "Edward", "Deborah",
    "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon", "Jeffrey", "Laura",
    "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy", "Nicholas", "Shirley",
    "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna", "Larry", "Brenda",
    "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma", "Benjamin", "Samantha",
    "Samuel", "Katherine", "Gregory", "Christine", "Frank", "Debra", "Alexander", "Rachel",
    "Raymond", "Catherine", "Patrick", "Carolyn", "Jack", "Janet", "Dennis", "Ruth"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey"
]

CITIES_PROVINCES = [
    ("Toronto", "ON", 43.6532, -79.3832),
    ("Vancouver", "BC", 49.2827, -123.1207),
    ("Montreal", "QC", 45.5017, -73.5673),
    ("Calgary", "AB", 51.0447, -114.0719),
    ("Ottawa", "ON", 45.4215, -75.6972),
    ("Edmonton", "AB", 53.5461, -113.4938),
    ("Winnipeg", "MB", 49.8951, -97.1384),
    ("Quebec City", "QC", 46.8139, -71.2080),
    ("Halifax", "NS", 44.6488, -63.5752),
    ("Victoria", "BC", 48.4284, -123.3656)
]

MAKES_MODELS = [
    ("Toyota", "Camry"), ("Toyota", "Corolla"), ("Toyota", "RAV4"), ("Toyota", "Prius"),
    ("Honda", "Civic"), ("Honda", "Accord"), ("Honda", "CR-V"),
    ("Hyundai", "Elantra"), ("Hyundai", "Tucson"), ("Hyundai", "Sonata"),
    ("Nissan", "Altima"), ("Nissan", "Sentra"), ("Nissan", "Rogue"),
    ("Ford", "Escape"), ("Ford", "Explorer"), ("Ford", "Fusion"),
    ("Chevrolet", "Malibu"), ("Chevrolet", "Equinox"),
    ("Subaru", "Outback"), ("Subaru", "Forester"),
    ("Kia", "Forte"), ("Kia", "Sportage"), ("Tesla", "Model 3"), ("Tesla", "Model Y")
]

COLORS = ["Black", "White", "Silver", "Grey", "Blue", "Red", "Dark Blue"]
INSURERS = ["Intact Insurance", "Desjardins", "Aviva", "TD Insurance", "ICBC", "Co-operators"]
PAYMENT_METHODS = ["credit_card", "debit_card", "apple_pay", "google_pay", "cash"]
PAYMENT_STATUSES = ["completed", "completed", "completed", "completed", "failed", "refunded"]

COMMENTS_5 = [
    "Great driver and smooth ride!", "Very polite and clean vehicle.", "Best ride of the week!",
    "Quick pickup and very safe driving.", "Excellent driving, pleasant conversation."
]
COMMENTS_4 = [
    "Good ride overall, arrived safely.", "Car was very clean, slight delay due to traffic.",
    "Decent driver, took a good route.", "Pleasant trip."
]
COMMENTS_3 = [
    "Average experience, driver was okay.", "Car could have been cleaner.", "Driver took a longer route."
]
COMMENTS_2 = [
    "Driver was somewhat distracted.", "Air conditioning wasn't working.", "Late pickup."
]
COMMENTS_1 = [
    "Terrible driving and very late.", "Rude driver, uncomfortable ride.", "Will not ride again."
]

def generate():
    num_users = 10000
    num_drivers = 2500
    num_rides = 10000
    
    print(f"Generating {num_users} users...")
    users = []
    used_emails = set()
    driver_ids = []
    rider_ids = []
    
    base_date = datetime(2022, 1, 1)

    for uid in range(1, num_users + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        
        # Ensure unique email
        email = f"{first.lower()}.{last.lower()}{uid}@rideshare.ca"
        while email in used_emails:
            email = f"{first.lower()}.{last.lower()}{uid}_{random.randint(10,99)}@rideshare.ca"
        used_emails.add(email)

        city_info = random.choice(CITIES_PROVINCES)
        city, province = city_info[0], city_info[1]

        # First num_drivers are drivers, rest are riders
        is_driver = (uid <= num_drivers)
        user_type = "driver" if is_driver else "rider"
        if is_driver:
            driver_ids.append(uid)
        else:
            rider_ids.append(uid)

        signup_dt = base_date + timedelta(days=random.randint(0, 700), seconds=random.randint(0, 86400))
        phone = f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        is_active = random.random() > 0.05  # 95% active
        created_at = signup_dt.strftime("%Y-%m-%d %H:%M:%S")
        signup_date = signup_dt.strftime("%Y-%m-%d")

        users.append([
            uid, first, last, email, phone, city, province, user_type, signup_date, is_active, created_at
        ])

    users_file = os.path.join(OUTPUT_DIR, "users.csv")
    with open(users_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "user_id", "first_name", "last_name", "email", "phone", "city",
            "province", "user_type", "signup_date", "is_active", "created_at"
        ])
        writer.writerows(users)
    print(f"-> {users_file} written ({len(users)} rows)")

    # Vehicles (1 per driver)
    print(f"Generating {len(driver_ids)} vehicles...")
    vehicles = []
    used_plates = set()

    for vid, did in enumerate(driver_ids, start=1):
        make, model = random.choice(MAKES_MODELS)
        year = random.randint(2018, 2024)
        
        # Unique plate
        plate = f"{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}{random.randint(10, 99)}-{random.randint(100, 999)}-{vid}"
        while plate in used_plates:
            plate = f"CAN-{vid:05d}"
        used_plates.add(plate)

        insurer = random.choice(INSURERS)
        color = random.choice(COLORS)
        is_active = True
        created_at = (base_date + timedelta(days=random.randint(100, 750))).strftime("%Y-%m-%d %H:%M:%S")

        vehicles.append([
            vid, did, make, model, year, plate, insurer, color, is_active, created_at
        ])

    vehicles_file = os.path.join(OUTPUT_DIR, "vehicles.csv")
    with open(vehicles_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "vehicle_id", "driver_id", "make", "model", "year", "license_plate",
            "insurance_provider", "color", "is_active", "created_at"
        ])
        writer.writerows(vehicles)
    print(f"-> {vehicles_file} written ({len(vehicles)} rows)")

    # Rides (10,000 rides)
    print(f"Generating {num_rides} rides...")
    rides = []
    payments = []
    ratings = []
    used_txns = set()

    start_ride_dt = datetime(2024, 1, 1, 0, 0, 0)

    for rid in range(1, num_rides + 1):
        rider_id = random.choice(rider_ids)
        driver_id = random.choice(driver_ids)

        req_dt = start_ride_dt + timedelta(minutes=random.randint(0, 365 * 24 * 60))
        
        is_cancelled = random.random() < 0.08  # 8% cancellation rate
        city_tuple = random.choice(CITIES_PROVINCES)
        base_lat, base_lng = city_tuple[2], city_tuple[3]

        p_lat = round(base_lat + random.uniform(-0.08, 0.08), 6)
        p_lng = round(base_lng + random.uniform(-0.08, 0.08), 6)
        d_lat = round(base_lat + random.uniform(-0.08, 0.08), 6)
        d_lng = round(base_lng + random.uniform(-0.08, 0.08), 6)

        dist_km = round(random.uniform(1.5, 38.0), 2)
        surge = round(random.choice([1.0, 1.0, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0]), 2)
        
        if is_cancelled:
            status = "cancelled"
            cancellation_reason = random.choice(["rider_cancelled", "driver_cancelled", "no_show"])
            pickup_time = ""
            dropoff_time = ""
            fare = 0.00 if cancellation_reason == "driver_cancelled" else 5.00
        else:
            status = "completed"
            cancellation_reason = ""
            pickup_dt = req_dt + timedelta(minutes=random.randint(3, 12))
            trip_duration = max(5, int(dist_km * 2.2 + random.randint(-3, 8)))
            dropoff_dt = pickup_dt + timedelta(minutes=trip_duration)
            pickup_time = pickup_dt.strftime("%Y-%m-%d %H:%M:%S")
            dropoff_time = dropoff_dt.strftime("%Y-%m-%d %H:%M:%S")
            # Base $3.50 + $1.40/km * surge
            fare = round((3.50 + dist_km * 1.40) * surge, 2)

        req_time_str = req_dt.strftime("%Y-%m-%d %H:%M:%S")

        rides.append([
            rid, rider_id, driver_id, req_time_str, pickup_time, dropoff_time,
            p_lat, p_lng, d_lat, d_lng, dist_km, fare, surge, status, cancellation_reason
        ])

        # Payment for every ride with fare > 0
        pay_method = random.choice(PAYMENT_METHODS)
        p_status = "completed" if status == "completed" else ("failed" if fare == 0 else "completed")
        
        # Unique transaction ID
        txn_id = f"TXN-{rid:06d}-{random.randint(1000, 9999)}"
        while txn_id in used_txns:
            txn_id = f"TXN-{rid:06d}-{random.randint(10000, 99999)}"
        used_txns.add(txn_id)

        pay_time = (dropoff_time if dropoff_time else req_time_str)
        payments.append([
            rid, rid, rider_id, pay_method, fare, p_status, txn_id, pay_time, pay_time
        ])

        # Rating for completed rides (or rated rides)
        if status == "completed":
            score = random.choices([5, 4, 3, 2, 1], weights=[65, 20, 8, 4, 3])[0]
            if score == 5:
                comm = random.choice(COMMENTS_5)
            elif score == 4:
                comm = random.choice(COMMENTS_4)
            elif score == 3:
                comm = random.choice(COMMENTS_3)
            elif score == 2:
                comm = random.choice(COMMENTS_2)
            else:
                comm = random.choice(COMMENTS_1)
        else:
            score = random.choice([1, 2, 3])
            comm = "Ride was cancelled."

        rated_dt = (datetime.strptime(dropoff_time, "%Y-%m-%d %H:%M:%S") if dropoff_time else req_dt) + timedelta(minutes=random.randint(2, 45))
        rated_at_str = rated_dt.strftime("%Y-%m-%d %H:%M:%S")
        ratings.append([
            rid, rid, rider_id, driver_id, score, comm, rated_at_str, rated_at_str
        ])

    rides_file = os.path.join(OUTPUT_DIR, "rides.csv")
    with open(rides_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ride_id", "rider_id", "driver_id", "requested_at", "pickup_time", "dropoff_time",
            "pickup_latitude", "pickup_longitude", "dropoff_latitude", "dropoff_longitude",
            "distance_km", "fare", "surge_multiplier", "status", "cancellation_reason"
        ])
        writer.writerows(rides)
    print(f"-> {rides_file} written ({len(rides)} rows)")

    payments_file = os.path.join(OUTPUT_DIR, "payments.csv")
    with open(payments_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "payment_id", "ride_id", "user_id", "payment_method", "amount",
            "payment_status", "transaction_id", "payment_time", "created_at"
        ])
        writer.writerows(payments)
    print(f"-> {payments_file} written ({len(payments)} rows)")

    ratings_file = os.path.join(OUTPUT_DIR, "ratings.csv")
    with open(ratings_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rating_id", "ride_id", "rider_id", "driver_id",
            "rating", "comment", "rated_at", "created_at"
        ])
        writer.writerows(ratings)
    print(f"-> {ratings_file} written ({len(ratings)} rows)")

    print("\nDataset generation completed successfully!")

if __name__ == "__main__":
    generate()
