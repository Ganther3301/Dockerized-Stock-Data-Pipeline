# 📦 Stock Data Pipeline with Dagster and Docker

## Overview
This project implements a **stock market data pipeline** that:
- Fetches stock data from **Yahoo Finance** (`yfinance`) or **Alpha Vantage** API  
- Cleans and stores it in a **PostgreSQL** database with upsert logic  
- Is orchestrated by **Dagster** for scheduling and monitoring  
- Runs locally or inside **Docker Compose** for full reproducibility  

---

## 🔧 Tech Stack
- **Python** → data fetching & transformation  
- **PostgreSQL** → database for stock data  
- **Dagster** → orchestration, scheduling, monitoring  
- **Docker + Docker Compose** → containerized services  

---

## Features

✅ Configurable data source via `.env`  
✅ Automatic fallback to a secondary source if the primary fails  
✅ Error handling for API rate limits, network issues, and invalid records  
✅ PostgreSQL integration with upsert (`ON CONFLICT`)  
✅ Dagster orchestration with cron-based scheduling  
✅ Dockerized deployment for portability

## 📂 Project Structure
```
.
├── main.py              # Pipeline script (fetch + store)
├── dagster_pipeline.py  # Dagster job & schedule
├── requirements.txt     # Dependencies
├── Dockerfile           # App container (Python + Dagster)
├── docker-compose.yml   # Multi-container setup
├── init.sql             # DB init (creates stock_data table)
├── .env.example         # Example env file
└── README.md            # Documentation
```

---

## ⚙️ Setup (Local)

### 1. Clone repo
```bash
git clone https://github.com/yourusername/stock-data-pipeline.git
cd stock-data-pipeline
```

### 2. Create `.env`
```env
# Database
DB_HOST=localhost
DB_NAME=stocksdb
DB_USER=ganther
DB_PASS=yourpassword

# APIs
ALPHA_API_KEY=your_alpha_key

# Data source
DATA_SOURCE=alpha_vantage   # or yf
FALLBACK_SOURCE=yf          # optional
```

### 3. Initialize DB (locally)
```bash
psql -U postgres -d stocksdb -f init.sql
```

### 4. Run pipeline manually
```bash
python main.py
```

### 5. Run Dagster locally
```bash
dagster dev -f dagster_pipeline.py
```
Dagster UI → [http://localhost:3000](http://localhost:3000)

---

## 🚀 Run with Docker

### 1. Build & start
```bash
docker-compose up --build
```

### 2. Services
- **Dagster UI** → [http://localhost:3000](http://localhost:3000)  
- **Postgres DB** → `localhost:5432` (inside network: `db-stock:5432`)  

### 3. Database volume
```yaml
volumes:
  stock_pg_data:
```
- Keeps Postgres data even if container restarts  
- Initialized with `init.sql`  

---

## 🐳 Docker Compose (snippet)

```yaml
services:
  db-stock:
    image: postgres:15
    container_name: db-stock
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASS}
    ports:
      - "5432:5432"
    volumes:
      - stock_pg_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  dagster:
    build: .
    container_name: dagster
    command: dagster dev -f dagster_pipeline.py -h 0.0.0.0 -p 3000
    ports:
      - "3000:3000"
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db-stock

volumes:
  stock_pg_data:
```

---

## 📊 Database Schema
```sql
CREATE TABLE IF NOT EXISTS stock_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(10, 4),
    high_price DECIMAL(10, 4),
    low_price DECIMAL(10, 4),
    close_price DECIMAL(10, 4) NOT NULL,
    volume BIGINT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (symbol, date)
);
```

---

## 🕒 Scheduling
- Defined in `dagster_pipeline.py` using `ScheduleDefinition`  
- Example: run daily at **12:50 PM IST**  
- Can also trigger manually from Dagster UI  

---

## ✅ Testing

### Local DB
```bash
psql -U ganther -d stocksdb
```

### Docker DB
```bash
docker exec -it db-stock psql -U stockuser -d stocksdb
```

Check data:
```sql
SELECT * FROM stock_data LIMIT 5;
```

---

## Deliverables
- **Python pipeline** → `main.py`  
- **Dagster job & schedule** → `dagster_pipeline.py`  
- **Postgres schema** → `init.sql`  
- **Docker setup** → `Dockerfile`, `docker-compose.yml`  
- **README.md** → documentation  

---
