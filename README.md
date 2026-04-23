# 🚀 Application Log Monitor & Alert Dashboard

A production-style **log monitoring system** that ingests synthetic web application logs, stores them in PostgreSQL, performs SQL-based analytics, triggers threshold-based alerts using Python, and visualizes system health via Grafana dashboards.

---

## 🛠️ Tech Stack

| Layer          | Tool / Technology                               |
| -------------- | ----------------------------------------------- |
| Log Generation | Python (Faker, CSV)                             |
| Database       | PostgreSQL 15                                   |
| Analytics      | SQL (CTEs, Window Functions, `PERCENTILE_CONT`) |
| Alerting       | Python (psycopg2)                               |
| Dashboard      | Grafana                                         |
| Infrastructure | Docker + Docker Compose                         |

---

## 📂 Project Structure

```bash
log_monitor/
├── log_generator.py       # Generates 10,000+ synthetic log records → CSV
├── db_setup.py            # Creates PostgreSQL schema & loads CSV data
├── queries.sql            # SQL queries for log analysis
├── alerting.py            # Threshold-based alert engine
├── grafana_dashboard.json # Grafana dashboard (import via UI)
├── docker-compose.yml     # PostgreSQL + Grafana setup
└── grafana_provisioning/  # Datasource configuration
```

---

## ⚙️ Setup Instructions

### 1️⃣ Start Services

```bash
docker compose up -d
```

* PostgreSQL → `localhost:5432`
* Grafana → `http://localhost:3000` (admin/admin)

---

### 2️⃣ Install Dependencies

```bash
pip install faker psycopg2-binary pandas
```

---

### 3️⃣ Generate Logs

```bash
python log_generator.py
```

* Generates `app_logs.csv`
* ~10,500 records over 30 days
* Includes simulated error spike (days 10–12)

---

### 4️⃣ Load Data

```bash
python db_setup.py
```

* Creates `app_logs` table
* Adds indexes
* Loads CSV into PostgreSQL

---

### 5️⃣ Run SQL Queries

```bash
psql -U postgres -d log_monitor -f queries.sql
```

---

### 6️⃣ Run Alert Engine

```bash
# Run once
python alerting.py

# Continuous monitoring
python alerting.py --watch 60
```

* Alerts printed in console
* Saved to `alerts.log`

---

### 7️⃣ Setup Grafana Dashboard

* Open: `http://localhost:3000`
* Login: `admin / admin`

#### Add Data Source:

* Host → `postgres:5432`
* Database → `log_monitor`
* User → `postgres`
* Password → `postgres`
* SSL → Disable

#### Import Dashboard:

* Go to → Dashboards → Import
* Upload → `grafana_dashboard.json`

---

## 📊 SQL Queries Overview

| # | Query                   | Technique Used       |
| - | ----------------------- | -------------------- |
| 1 | Overall error rate      | Aggregate + CASE     |
| 2 | Error rate per endpoint | GROUP BY + HAVING    |
| 3 | P95 / P99 response time | `PERCENTILE_CONT`    |
| 4 | Hourly spike detection  | CTE + STDDEV         |
| 5 | Top failing endpoints   | Filtered aggregation |
| 6 | Daily traffic trends    | `DATE_TRUNC`         |
| 7 | Slowest requests        | `ROW_NUMBER()`       |
| 8 | Error type breakdown    | Window functions     |

---

## 🚨 Alert Rules

| Rule                | Threshold        | Severity    |
| ------------------- | ---------------- | ----------- |
| High Error Rate     | > 5% (last hour) | 🚨 CRITICAL |
| Slow Response (P95) | > 1000 ms        | ⚠️ WARNING  |
| Server Error Spike  | > 10 (15 min)    | 🚨 CRITICAL |

---

## 🧠 Key Design Decisions

* 📌 **Synthetic Error Spike**
  Simulated failures to test anomaly detection logic

* 📌 **P95/P99 over Average**
  Industry-standard SLO metrics (better than mean)

* 📌 **Polling-based Alert Engine**
  Mirrors real tools like Splunk scheduled alerts

* 📌 **Indexed Columns**
  `timestamp`, `status_code`, `endpoint` for performance

---

## 📸 Screenshots

> Add Grafana dashboard screenshots here

---

## 💡 Use Cases

* Application performance monitoring
* Backend observability systems
* Error tracking & debugging
* DevOps monitoring pipelines

---

## 🚀 Future Improvements

* Kafka-based real-time streaming
* Prometheus integration
* Email/SMS alerts
* Cloud deployment

---

## 👨‍💻 Author

**Akash Masane**

---

## ⭐ Support

If you found this useful, consider giving a ⭐ on GitHub!
