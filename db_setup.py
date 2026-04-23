"""
db_setup.py
Creates the PostgreSQL schema and loads log data from CSV.
"""

import psycopg2
import pandas as pd
from psycopg2.extras import execute_batch

# ── CONFIG ────────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "log_monitor",
    "user": "postgres",
    # ❌ No password (trust mode)
}

CSV_FILE = "app_logs.csv"

# ── SCHEMA ────────────────────────────────────────────────────────────────────
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS app_logs (
    log_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    endpoint VARCHAR(100) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    error_type VARCHAR(100),
    user_id VARCHAR(50),
    ip_address VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_timestamp ON app_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_status_code ON app_logs(status_code);
CREATE INDEX IF NOT EXISTS idx_endpoint ON app_logs(endpoint);
"""

# ── LOAD ──────────────────────────────────────────────────────────────────────
def load_data():
    df = pd.read_csv(CSV_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["error_type"] = df["error_type"].replace("", None)
    df["user_id"] = df["user_id"].replace("", None)

    rows = [
        (
            row.timestamp, row.endpoint, row.method, row.status_code,
            row.response_time_ms, row.error_type, row.user_id, row.ip_address
        )
        for row in df.itertuples(index=False)
    ]

    # ✅ Explicit connection (no password)
    conn = psycopg2.connect(
    host="172.18.0.2",
    port=5432,
    database="log_monitor",
    user="postgres",
    password="postgres"
)

    cur = conn.cursor()

    cur.execute(CREATE_TABLE_SQL)
    cur.execute("TRUNCATE app_logs RESTART IDENTITY;")

    execute_batch(cur, """
        INSERT INTO app_logs
        (timestamp, endpoint, method, status_code, response_time_ms, error_type, user_id, ip_address)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, rows, page_size=500)

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Loaded {len(rows)} records into PostgreSQL (app_logs table)")

if __name__ == "__main__":
    load_data()