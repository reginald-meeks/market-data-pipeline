import pandas as pd
from sqlalchemy import create_engine, text

def run_transform():
    engine = create_engine("postgresql+psycopg2://airflow:airflow@postgres:5432/market_data")

    df = pd.read_sql("SELECT * FROM raw_market_data", engine)

    df["open_price"] = df["open_price"].astype(float)
    df["high_price"] = df["high_price"].astype(float)
    df["low_price"] = df["low_price"].astype(float)
    df["close_price"] = df["close_price"].astype(float)
    df["volume"] = df["volume"].astype(int)
    df["trade_date"] = pd.to_datetime(df["trade_date"])

    df = df.drop(columns=["id"])

    with engine.connect() as conn:
        for row in df.itertuples():
            conn.execute(
                text("""
                     INSERT INTO processed_market_data
                     (symbol, trade_date, open_price, high_price, low_price, close_price, volume)
                     VALUES (:symbol, :trade_date, :open_price, :high_price, :low_price, :close_price, :volume)
                         ON CONFLICT (symbol, trade_date) DO NOTHING
                     """),
                {
                    "symbol": row.symbol,
                    "trade_date": row.trade_date,
                    "open_price": row.open_price,
                    "high_price": row.high_price,
                    "low_price": row.low_price,
                    "close_price": row.close_price,
                    "volume": row.volume
                }
            )
        conn.execute(text("COMMIT"))
    print(f"Transformed {len(df)} rows into processed_market_data.")

if __name__ == "__main__":
    run_transform()