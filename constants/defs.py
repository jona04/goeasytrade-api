import os
from dotenv import load_dotenv

load_dotenv()

SELL = -1
BUY = 1
NONE = 0

API_ID = os.environ.get("API_ID")
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
OPENFX_URL = os.environ.get("OPENFX_URL")


BINANCE_KEY = os.environ.get("BINANCE_KEY")
BINANCE_SECRET = os.environ.get("BINANCE_SECRET")

BINANCE_TESTNET_KEY = os.environ.get("BINANCE_TESTNET_KEY")
BINANCE_TESTNET_SECRET = os.environ.get("BINANCE_TESTNET_SECRET")


SECURE_HEADER = {
    "Authorization": f"Basic {API_ID}:{API_KEY}:{API_SECRET}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

LABEL_MAP = {
    "Open": "o",
    "High": "h",
    "Low": "l",
    "Close": "c",
}

THROTTLE_TIME = 0.3

MONGO_CONN = "mongodb://localhost:27017/"

TFS = {"M1": 1, "M5": 300, "H15": 900, "H1": 3600}
