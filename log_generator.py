"""
log_generator.py
Generates 10,000+ synthetic application log records and saves to CSV.
Simulates a real web application's access/error logs over 30 days.
"""

import random
import csv
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

# Config
NUM_RECORDS = 10500
START_DATE = datetime.now() - timedelta(days=30)
OUTPUT_FILE = "app_logs.csv"

ENDPOINTS = [
    "/api/users", "/api/orders", "/api/products",
    "/api/payments", "/api/auth/login", "/api/auth/logout",
    "/api/reports", "/api/search", "/api/notifications", "/api/health"
]

METHODS = ["GET", "POST", "PUT", "DELETE"]

# Weighted status codes — mostly 200s, some errors
STATUS_CODES = (
    [200] * 70 + [201] * 10 + [204] * 5 +
    [400] * 5 + [401] * 3 + [403] * 2 +
    [404] * 8 + [500] * 5 + [502] * 1 + [503] * 1
)

ERROR_TYPES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
}

# Some endpoints are slower than others
RESPONSE_TIME_BASE = {
    "/api/reports":       (800, 400),
    "/api/search":        (600, 300),
    "/api/payments":      (500, 200),
    "/api/orders":        (300, 150),
    "/api/users":         (200, 100),
    "/api/products":      (180, 80),
    "/api/auth/login":    (250, 120),
    "/api/auth/logout":   (100, 50),
    "/api/notifications": (150, 70),
    "/api/health":        (30,  15),
}

def random_response_time(endpoint, status_code):
    base, std = RESPONSE_TIME_BASE.get(endpoint, (200, 100))
    t = max(10, int(random.gauss(base, std)))
    # Errors tend to take longer
    if status_code >= 500:
        t = int(t * random.uniform(1.5, 3.0))
    return t

def generate_logs():
    records = []
    for i in range(NUM_RECORDS):
        # Spike simulation: higher error rate between day 10-12
        offset_days = random.uniform(0, 30)
        ts = START_DATE + timedelta(
            days=offset_days,
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )

        endpoint = random.choice(ENDPOINTS)
        method   = random.choice(METHODS)
        status   = random.choice(STATUS_CODES)

        # Inject error spike around day 10-12
        day = (ts - START_DATE).days
        if 10 <= day <= 12 and random.random() < 0.3:
            status = random.choice([500, 502, 503])

        response_time = random_response_time(endpoint, status)
        error_type    = ERROR_TYPES.get(status, None)
        user_id       = fake.uuid4()[:8] if random.random() > 0.1 else None

        records.append({
            "log_id":          i + 1,
            "timestamp":       ts.strftime("%Y-%m-%d %H:%M:%S"),
            "endpoint":        endpoint,
            "method":          method,
            "status_code":     status,
            "response_time_ms": response_time,
            "error_type":      error_type if error_type else "",
            "user_id":         user_id if user_id else "",
            "ip_address":      fake.ipv4(),
        })

    # Sort by timestamp
    records.sort(key=lambda x: x["timestamp"])

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    print(f"✅ Generated {len(records)} log records → {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_logs()