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
  ingested_at TIMESTAMP DEFAULT NOW()
);