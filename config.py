import os

# =========================================
# API INDODAX
# =========================================

API_KEY = os.environ.get(
    "API_KEY",
    ""
)

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    ""
)

# =========================================
# TRADING SETTINGS
# =========================================

# modal per trade
BASE_TRADE_AMOUNT = 100000

# maksimum posisi aktif
MAX_ACTIVE_TRADES = 8

# take profit %
TAKE_PROFIT = 8

# stop loss %
STOP_LOSS = 5

# =========================================
# TRAILING STOP
# =========================================

TRAILING_STOP = True

# trailing gap %
TRAILING_GAP = 2

# =========================================
# SLIPPAGE
# =========================================

# buy +0.2%
BUY_SLIPPAGE = 0.002

# sell -0.2%
SELL_SLIPPAGE = 0.002

# =========================================
# MARKET SCANNER
# =========================================

TIMEFRAME = "15m"

SCAN_LIMIT = 25

# minimum volume market
MIN_VOLUME = 100000000

# maksimum spread %
MAX_SPREAD = 3

# =========================================
# FILTER
# =========================================

ENABLE_BTC_FILTER = True

ENABLE_SPREAD_FILTER = True

# =========================================
# SAFETY
# =========================================

# minimum saldo IDR
MINIMUM_IDR = 50000

# delay trader loop
TRADER_INTERVAL = 15

# delay scanner update
SCANNER_INTERVAL = 300
