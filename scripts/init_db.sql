CREATE DATABASE market_data;

\c market_data;

CREATE TABLE raw_market_data (
    id SERIAL PRIMARY KEY,
    symbol TEXT,
    trade_date TEXT,
    open_price TEXT,
    high_price TEXT,
    low_price TEXT,
    close_price TEXT,
    volume TEXT,
    ingested_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_raw_symbol_date UNIQUE (symbol, trade_date)
);

CREATE TABLE processed_market_data (
    id SERIAL PRIMARY KEY,
    symbol TEXT,
    trade_date DATE,
    open_price NUMERIC,
    high_price NUMERIC,
    low_price NUMERIC,
    close_price NUMERIC,
    volume BIGINT,
    ingested_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_processed_symbol_date UNIQUE (symbol, trade_date)
);

CREATE TABLE quarantine_market_data (
    id SERIAL PRIMARY KEY,
    symbol TEXT,
    trade_date TEXT,
    open_price TEXT,
    high_price TEXT,
    low_price TEXT,
    close_price TEXT,
    volume TEXT,
    ingested_at TIMESTAMP DEFAULT NOW(),
    reason TEXT,
    quarantined_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE market_analytics (
    id SERIAL PRIMARY KEY,
    symbol TEXT,
    trade_date DATE,
    close_price NUMERIC,
    moving_avg_7day NUMERIC,
    calculated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_symbol_date UNIQUE (symbol, trade_date)
);

CREATE TABLE pipeline_metrics (
    id SERIAL PRIMARY KEY,
    dag_id TEXT,
    task_id TEXT,
    run_id TEXT,
    rows_processed INTEGER,
    status TEXT,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds NUMERIC
);