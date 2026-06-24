import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey={api_key}"

response = requests.get(url)

data = response.json()

print(json.dumps(data, indent=2))