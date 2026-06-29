import requests
import os
import psycopg2

def run_ingestion():
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey={api_key}"
    response = requests.get(url)
    data = response.json()

    conn = psycopg2.connect(
        host="postgres",
        port=5432,
        dbname="market_data",
        user="airflow",
        password="airflow"
    )
    cursor = conn.cursor()
    time_series = data["Time Series (Daily)"]

    for date, values in time_series.items():
        cursor.execute("""
                       INSERT INTO raw_market_data 
                       (symbol, trade_date, open_price, high_price, low_price, close_price, volume)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, trade_date) DO NOTHING
                       """, (
                           "AAPL",
                           date,
                           values["1. open"],
                           values["2. high"],
                           values["3. low"],
                           values["4. close"],
                           values["5. volume"]
                       ))

    conn.commit()
    cursor.close()
    conn.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    run_ingestion()