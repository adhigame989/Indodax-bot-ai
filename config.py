import os

# API INDODAX
API_KEY = os.environ.get("API_KEY", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "")

# Trading Settings
BASE_TRADE_AMOUNT = 100000

MAX_ACTIVE_TRADES = 8

TAKE_PROFIT = 8
STOP_LOSS = 5

# Trailing Stop
TRAILING_STOP = True
TRAILING_GAP = 2

# Market Scanner
TIMEFRAME = "15m"
SCAN_LIMIT = 25

# Filters
ENABLE_BTC_FILTER = True
ENABLE_SPREAD_FILTER = True
