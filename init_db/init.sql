CREATE TABLE IF NOT EXISTS stock_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(10, 4),
    high_price DECIMAL(10, 4),
    low_price DECIMAL(10, 4),
    close_price DECIMAL(10, 4) NOT NULL,
    volume BIGINT,
    created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (symbol, date)
);