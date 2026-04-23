"""
alerting.py
Threshold-based alerting engine — queries live DB metrics and fires alerts.
"""

import psycopg2
import argparse
import time
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
# ✅ FIXED DB CONNECTION (explicit, stable)
def get_connection():
    return psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        database="log_monitor",
        user="postgres",
        password="postgres"
    )

# Alert thresholds
THRESHOLDS = {
    "error_rate_pct":      5.0,
    "p95_response_ms":   1000,
    "server_error_count":  10,
}

ALERT_LOG_FILE = "alerts.log"


# ── QUERIES ───────────────────────────────────────────────────────────────────
def check_error_rate(cur):
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS errors
        FROM app_logs
        WHERE timestamp >= NOW() - INTERVAL '1 hour'
    """)
    total, errors = cur.fetchone()
    if total == 0:
        return None
    rate = round(errors * 100.0 / total, 2)
    if rate > THRESHOLDS["error_rate_pct"]:
        return {
            "level":   "🚨 CRITICAL",
            "rule":    "High Error Rate",
            "message": f"Error rate is {rate}% in the last hour ({errors}/{total} requests). Threshold: {THRESHOLDS['error_rate_pct']}%",
        }
    return None


def check_p95_response(cur):
    cur.execute("""
        SELECT
            endpoint,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) AS p95
        FROM app_logs
        WHERE timestamp >= NOW() - INTERVAL '1 hour'
        GROUP BY endpoint
        HAVING PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) > %s
        ORDER BY p95 DESC
    """, (THRESHOLDS["p95_response_ms"],))
    rows = cur.fetchall()
    if rows:
        details = ", ".join([f"{r[0]} ({int(r[1])}ms)" for r in rows])
        return {
            "level":   "⚠️ WARNING",
            "rule":    "High P95 Response Time",
            "message": f"Slow endpoints detected (P95 > {THRESHOLDS['p95_response_ms']}ms): {details}",
        }
    return None


def check_server_errors(cur):
    cur.execute("""
        SELECT COUNT(*)
        FROM app_logs
        WHERE status_code >= 500
          AND timestamp >= NOW() - INTERVAL '15 minutes'
    """)
    count = cur.fetchone()[0]
    if count > THRESHOLDS["server_error_count"]:
        return {
            "level":   "🚨 CRITICAL",
            "rule":    "Server Error Spike",
            "message": f"{count} server errors (5xx) detected in the last 15 minutes. Threshold: {THRESHOLDS['server_error_count']}",
        }
    return None


# ── ALERT ENGINE ──────────────────────────────────────────────────────────────
CHECKS = [check_error_rate, check_p95_response, check_server_errors]


def run_checks():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"  Alert Check — {now}")
    print(f"{'='*60}")

    try:
        conn = get_connection()
        cur = conn.cursor()

        alerts_fired = 0
        for check in CHECKS:
            result = check(cur)
            if result:
                alerts_fired += 1
                msg = (
                    f"[{now}] {result['level']} | {result['rule']}\n"
                    f"  → {result['message']}"
                )
                print(msg)
                with open(ALERT_LOG_FILE, "a") as f:
                    f.write(msg + "\n")

        if alerts_fired == 0:
            print("  ✅ All systems normal — no alerts triggered.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"  ❌ DB connection error: {e}")
        print("     Make sure PostgreSQL is running and config is correct.")


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log Monitor Alert Engine")
    parser.add_argument("--watch", type=int, default=0,
                        help="Poll interval in seconds (0 = run once)")
    args = parser.parse_args()

    if args.watch > 0:
        print(f"🔄 Watching for alerts every {args.watch} seconds. Ctrl+C to stop.")
        while True:
            run_checks()
            time.sleep(args.watch)
    else:
        run_checks()