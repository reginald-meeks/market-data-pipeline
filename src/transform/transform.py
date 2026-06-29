import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

def run_transform():
    load_dotenv()

    engine = create_engine("postgresql+psycopg2://airflow:airflow@postgres:5432/market_data")

    df = pd.read_sql("SELECT * FROM raw_market_data", engine)

    df["open_price"] = df["open_price"].astype(float)
    df["high_price"] = df["high_price"].astype(float)
    df["low_price"] = df["low_price"].astype(float)
    df["close_price"] = df["close_price"].astype(float)
    df["volume"] = df["volume"].astype(int)
    df["trade_date"] = pd.to_datetime(df["trade_date"])

    df = df.drop(columns=["id"])

    df.to_sql(
        "processed_market_data",
        engine,
        if_exists="append",
        index=False
    )

    engine.dispose()
    print(f"Transformed {len(df)} rows into processed_market_data.")