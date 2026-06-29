import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

def run_validation():
    load_dotenv()

    engine = create_engine("postgresql+psycopg2://airflow:airflow@postgres:5432/market_data")

    df = pd.read_sql("SELECT * FROM raw_market_data", engine)

    null_mask = df[["symbol", "trade_date", "open_price",
                    "high_price", "low_price", "close_price",
                    "volume"]].isnull().any(axis=1)

    def is_numeric(val):
        try:
            float(val)
            return True
        except (ValueError, TypeError):
            return False

    price_cols = ["open_price", "high_price", "low_price", "close_price", "volume"]
    numeric_mask = ~df[price_cols].apply(lambda col: col.map(is_numeric)).all(axis=1)

    range_mask = (
            (df["open_price"].astype(float) <= 0) |
            (df["high_price"].astype(float) <= 0) |
            (df["low_price"].astype(float) <= 0) |
            (df["close_price"].astype(float) <= 0) |
            (df["volume"].astype(float) <= 0)
    )

    duplicate_mask = df.duplicated(subset=["symbol", "trade_date"], keep=False)

    invalid_mask = null_mask | numeric_mask | range_mask | duplicate_mask
    valid_df = df[~invalid_mask]
    invalid_df = df[invalid_mask]

    invalid_df = invalid_df.copy()
    invalid_df["reason"] = "failed validation"
    invalid_df["quarantined_at"] = pd.Timestamp.now()

    if len(invalid_df) > 0:
        invalid_df.to_sql(
            "quarantine_market_data",
            engine,
            if_exists="append",
            index=False
        )

    print(f"Valid records: {len(valid_df)}")
    print(f"Quarantined records: {len(invalid_df)}")

    engine.dispose()