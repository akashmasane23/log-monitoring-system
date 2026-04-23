-- =============================================================================
-- queries.sql
-- 8 Business SQL Queries for Application Log Analysis
-- Run against the app_logs table in PostgreSQL
-- =============================================================================


-- ── QUERY 1: Overall Error Rate ───────────────────────────────────────────────
-- What percentage of all requests result in an error (4xx or 5xx)?
SELECT
    COUNT(*)                                                        AS total_requests,
    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END)            AS total_errors,
    ROUND(
        SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) * 100.0
        / COUNT(*), 2
    )                                                               AS error_rate_pct
FROM app_logs;


-- ── QUERY 2: Error Rate Per Endpoint ─────────────────────────────────────────
-- Which endpoints have the highest error rate? (Most actionable for support)
SELECT
    endpoint,
    COUNT(*)                                                        AS total_requests,
    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END)            AS errors,
    ROUND(
        SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) * 100.0
        / COUNT(*), 2
    )                                                               AS error_rate_pct
FROM app_logs
GROUP BY endpoint
HAVING SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) > 0
ORDER BY error_rate_pct DESC;


-- ── QUERY 3: P95 Response Time Per Endpoint (Window Function) ────────────────
-- 95th percentile response time — identifies slow endpoints under load
SELECT
    endpoint,
    ROUND(AVG(response_time_ms), 1)                                AS avg_response_ms,
    MAX(response_time_ms)                                          AS max_response_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) AS p95_response_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) AS p99_response_ms
FROM app_logs
GROUP BY endpoint
ORDER BY p95_response_ms DESC;


-- ── QUERY 4: Hourly Error Spike Detection (CTE) ───────────────────────────────
-- Detects hours where error count is significantly above the average — like an alert rule
WITH hourly_errors AS (
    SELECT
        DATE_TRUNC('hour', timestamp)   AS hour,
        COUNT(*)                        AS total_requests,
        SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS error_count
    FROM app_logs
    GROUP BY DATE_TRUNC('hour', timestamp)
),
stats AS (
    SELECT
        AVG(error_count)    AS avg_errors,
        STDDEV(error_count) AS std_errors
    FROM hourly_errors
)
SELECT
    h.hour,
    h.total_requests,
    h.error_count,
    ROUND(h.error_count * 100.0 / h.total_requests, 2) AS error_rate_pct,
    ROUND(s.avg_errors, 1)                              AS avg_hourly_errors,
    CASE
        WHEN h.error_count > s.avg_errors + (2 * s.std_errors) THEN '🚨 SPIKE'
        WHEN h.error_count > s.avg_errors + s.std_errors       THEN '⚠️  WARNING'
        ELSE 'OK'
    END                                                 AS alert_status
FROM hourly_errors h, stats s
WHERE h.error_count > s.avg_errors + s.std_errors
ORDER BY h.error_count DESC
LIMIT 20;


-- ── QUERY 5: Top Failing Endpoints in Last 24 Hours ──────────────────────────
-- Real-time support view: what's breaking right now?
SELECT
    endpoint,
    method,
    status_code,
    error_type,
    COUNT(*)        AS occurrences,
    MIN(timestamp)  AS first_seen,
    MAX(timestamp)  AS last_seen
FROM app_logs
WHERE
    status_code >= 400
    AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY endpoint, method, status_code, error_type
ORDER BY occurrences DESC
LIMIT 15;


-- ── QUERY 6: Daily Traffic & Error Trend (30 Days) ───────────────────────────
-- High-level daily overview for dashboard time-series panels
SELECT
    DATE(timestamp)                                                  AS day,
    COUNT(*)                                                         AS total_requests,
    SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END)             AS server_errors,
    SUM(CASE WHEN status_code BETWEEN 400 AND 499 THEN 1 ELSE 0 END) AS client_errors,
    ROUND(AVG(response_time_ms), 1)                                  AS avg_response_ms
FROM app_logs
GROUP BY DATE(timestamp)
ORDER BY day;


-- ── QUERY 7: Slowest Requests Ranked by Endpoint (ROW_NUMBER) ────────────────
-- Identify the top 3 slowest requests per endpoint for deep-dive debugging
WITH ranked AS (
    SELECT
        log_id,
        timestamp,
        endpoint,
        method,
        status_code,
        response_time_ms,
        ROW_NUMBER() OVER (
            PARTITION BY endpoint
            ORDER BY response_time_ms DESC
        ) AS rank
    FROM app_logs
)
SELECT *
FROM ranked
WHERE rank <= 3
ORDER BY endpoint, rank;


-- ── QUERY 8: Error Type Breakdown & Frequency ────────────────────────────────
-- Which error types dominate? Used to prioritize fixes.
SELECT
    error_type,
    status_code,
    COUNT(*)                                AS occurrences,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_all_errors,
    MIN(timestamp)                          AS first_occurrence,
    MAX(timestamp)                          AS latest_occurrence
FROM app_logs
WHERE status_code >= 400
GROUP BY error_type, status_code
ORDER BY occurrences DESC;