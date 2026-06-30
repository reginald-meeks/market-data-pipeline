import pandas as pd
from sqlalchemy import create_engine, text

def run_analytics():
    engine = create_engine("postgresql+psycopg2://airflow:airflow@postgres:5432/market_data")

    df = pd.read_sql("""
                        SELECT
                            symbol,
                            trade_date,
                            close_price,
                            AVG(close_price) OVER (
                                PARTITION BY symbol
                                ORDER BY trade_date
                                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                            ) AS moving_avg_7day
                        FROM processed_market_data
                        ORDER BY trade_date""", engine)
    with engine.connect() as conn:
        for row in df.itertuples():
            conn.execute(
                text("""
                     INSERT INTO market_analytics
                     (symbol, trade_date, close_price, moving_avg_7day)
                     VALUES (:symbol, :trade_date, :close_price, :moving_avg_7day)
                         ON CONFLICT (symbol, trade_date) DO NOTHING
                     """),
                {
                    "symbol": row.symbol,
                    "trade_date": row.trade_date,
                    "close_price": row.close_price,
                    "moving_avg_7day": row.moving_avg_7day
                }
            )
        conn.execute(text("COMMIT"))
    print(f"Analytics complete. {len(df)} rows written to market_analytics.")

if __name__ == "__main__":
    run_analytics()