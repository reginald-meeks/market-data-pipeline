import requests
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Step 1 — Get API key
api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

# Step 2 — Call Alpha Vantage
url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey={api_key}"
response = requests.get(url)
data = response.json()

# Step 3 — Connect to Postgres
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="market_data",
    user="airflow",
    password="airflow"
)
cursor = conn.cursor()

# Step 4 — Insert each trading day
time_series = data["Time Series (Daily)"]

for date, values in time_series.items():
    cursor.execute("""
                   INSERT INTO raw_market_data
                   (symbol, trade_date, open_price, high_price, low_price, close_price, volume)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   """, (
                       "AAPL",
                       date,
                       values["1. open"],
                       values["2. high"],
                       values["3. low"],
                       values["4. close"],
                       values["5. volume"]
                   ))

# Step 5 — Commit and close
conn.commit()
cursor.close()
conn.close()
print("Ingestion complete.")