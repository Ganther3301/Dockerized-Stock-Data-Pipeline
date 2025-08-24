# 📈 Dockerized Stock Data Pipeline with Dagster

## Overview

This project implements a **data pipeline** that:

- Fetches daily stock market data for multiple tickers (e.g., `GOOGL`, `MSFT`, `NVDA`)  
- Supports **multiple data sources**:  
  - [Alpha Vantage](https://www.alphavantage.co/) (API key required)  
  - [Yahoo Finance](https://pypi.org/project/yfinance/) (`yfinance`, no API key required)  
- Stores the cleaned data into a **PostgreSQL** database with **upsert** logic (no duplicates).  
- Is orchestrated with **Dagster**, with a scheduled job.  
- Can be run locally or via **Docker Compose**.

## Features

✅ Configurable data source via `.env`  
✅ Automatic fallback to a secondary source if the primary fails  
✅ Error handling for API rate limits, network issues, and invalid records  
✅ PostgreSQL integration with upsert (`ON CONFLICT`)  
✅ Dagster orchestration with cron-based scheduling  
✅ Dockerized deployment for portability

## Project Structure

```
.
├── main.py              # Main pipeline script (fetch + store)
├── dagster_pipeline.py  # Dagster job & schedule definition
├── requirements.txt     # Dependencies
├── Dockerfile           # App container
├── docker-compose.yml   # Multi-service setup (Dagster + Postgres)
├── init.sql             # DB init script (creates stock_data table)
├── .env.example         # Example environment config
└── README.md            # Documentation
```

## Running with Docker

### 1. Build and start services

```bash
docker-compose up --build
```

### 2. Services

- **Postgres DB** → `localhost:5432`  
- **Dagster UI** → [http://localhost:3000](http://localhost:3000)  

### 3. Volumes

- PostgreSQL data is persisted in `stock_pg_data`

## Database Schema

`init.sql` creates the table with unique constraint:

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

Upserts ensure no duplicates:

```sql
ON CONFLICT (symbol, date) DO UPDATE SET ...
```

## Error Handling

- **Alpha Vantage**  
  - Handles rate limits → waits 12s between requests  
  - Detects quota exceeded → falls back to Yahoo Finance if configured  
- **Yahoo Finance (yfinance)**  
  - Handles empty/no data case  
- **Database**  
  - Transactions rollback on failure  
  - Closes connections gracefully  

## Deliverables

- **Python script (`main.py`)** → data fetching & storing  
- **Dagster job (`dagster_pipeline.py`)** → orchestration & scheduling  
- **Postgres schema (`init.sql`)** → ensures table/constraints  
- **Docker setup (`Dockerfile`, `docker-compose.yml`)** → reproducible environment  
- **README.md** (this file) → documentation  

✨ With this setup, you can fetch, process, and store stock data reliably, with orchestration and portability built-in.  
