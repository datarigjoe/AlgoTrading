import os
import datetime
import csv
import pandas as pd
from pyotp import TOTP
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import place_order
# -----------------------------------------------
# API and WebSocket Setup
# -----------------------------------------------

KEY_PATH = r"C:\ALGOTRADING_PROJECT"
os.chdir(KEY_PATH)

# Read API credentials
with open("key.txt", "r") as f:
    key_secret = f.read().split()

# Initialize API session
api = SmartConnect(api_key=key_secret[0])
session_data = api.generateSession(key_secret[2], key_secret[3], TOTP(key_secret[4]).now())
feed_token = api.getfeedToken()

# Initialize WebSocket connection
sws = SmartWebSocketV2(session_data["data"]["jwtToken"], key_secret[0], key_secret[2], feed_token)

# -----------------------------------------------
# Indicator Parameters
# -----------------------------------------------

EMA_SHORT_PERIOD = 9
EMA_LONG_PERIOD = 21
BOLLINGER_PERIOD = 20
BOLLINGER_STD_DEV = 2
RSI_PERIOD = 14

# Trade Settings
TRADE_COOLDOWN_PERIOD = datetime.timedelta(seconds=180)
MIN_HOLD_TIME = datetime.timedelta(minutes=3)
FORCE_SELL_TIME = datetime.time(15, 5)  # 3:05 PM

# Data Buffers
price_data = {}         # Stores price history for each token
trade_positions = {}    # Tracks active trades
trade_cooldowns = {}    # Prevents quick repeated trades

# -----------------------------------------------
# Indicator Calculations
# -----------------------------------------------

def calculate_ema(prices, period):
    """Calculate Exponential Moving Average (EMA)."""
    return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1] if len(prices) >= period else None

def calculate_bollinger_bands(prices, period, std_dev):
    """Calculate Bollinger Bands (Upper and Lower)."""
    if len(prices) < period:
        return None, None
    rolling_mean = pd.Series(prices).rolling(window=period).mean()
    rolling_std = pd.Series(prices).rolling(window=period).std()
    upper_band = rolling_mean.iloc[-1] + (rolling_std.iloc[-1] * std_dev)
    lower_band = rolling_mean.iloc[-1] - (rolling_std.iloc[-1] * std_dev)
    return upper_band, lower_band

def calculate_rsi(prices, period=RSI_PERIOD):
    """Calculate Relative Strength Index (RSI)."""
    if len(prices) < period:
        return None
    delta = pd.Series(prices).diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

def calculate_percentage_difference(entry_price, current_price):
    """Calculate percentage difference between two prices."""
    return ((current_price - entry_price) / entry_price) * 100

def get_profit_threshold(timestamp):
    """Dynamically adjust profit threshold based on market time."""
    market_open_time = datetime.time(9, 15)
    high_profit_time = datetime.time(9, 45)
    return 0.6 if market_open_time <= timestamp.time() <= high_profit_time else 0.4

# -----------------------------------------------
# Trade Logging
# -----------------------------------------------

def log_trade(timestamp, token, trade_type, price):
    """Log trade details into a CSV file."""
    csv_file = os.path.join(KEY_PATH, f"trades_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv")
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Token", "Trade Type", "Price"])
        writer.writerow([timestamp, token, trade_type, price])

def log_order(timestamp, token, transaction_type, price):
    """Log placed orders into a CSV file."""
    csv_file = os.path.join(KEY_PATH, f"orders_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv")
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Token", "Transaction Type", "Price"])
        writer.writerow([timestamp, token, transaction_type, price])

def force_close_trades(timestamp):
    """Force close all open trades at 3:05 PM."""
    global trade_positions, trade_cooldowns

    for token, trade_info in list(trade_positions.items()):
        current_price = price_data[token][-1] if token in price_data and price_data[token] else None
        if not current_price:
            continue

        last_trade = trade_info["type"]
        if last_trade == "BUY":
            log_trade(timestamp, token, "SELL", current_price)  # Sell to close
        elif last_trade == "SELL":
            log_trade(timestamp, token, "BUY", current_price)  # Buy back the position

        del trade_positions[token]  # Remove from active trades
        trade_cooldowns[token] = timestamp  # Apply cooldown

# -----------------------------------------------
# Trade Decision Logic
# -----------------------------------------------

def decide_trade(token, prices, timestamp):
    """Decide whether to buy, sell"""
    global trade_positions, trade_cooldowns

    if len(prices) < max(EMA_LONG_PERIOD, BOLLINGER_PERIOD):
        return
    
    current_price = prices[-1]
    ema_short = calculate_ema(prices, EMA_SHORT_PERIOD)
    ema_long = calculate_ema(prices, EMA_LONG_PERIOD)
    upper_band, lower_band = calculate_bollinger_bands(prices, BOLLINGER_PERIOD, BOLLINGER_STD_DEV)
    rsi = calculate_rsi(prices)
    profit_threshold = get_profit_threshold(timestamp)

    if None in [rsi, ema_short, ema_long, upper_band, lower_band]:
        return
    
    last_trade = trade_positions.get(token, {}).get("type", None)

    # Prevent quick repeated trades
    if token in trade_cooldowns and (timestamp - trade_cooldowns[token]) < TRADE_COOLDOWN_PERIOD:
        return  

    # Exit Trade
    if token in trade_positions:
        entry_price = trade_positions[token]["entry_price"]
        entry_time = trade_positions[token]["entry_time"]
        price_diff = calculate_percentage_difference(entry_price, current_price)
        time_diff = timestamp - entry_time

        if time_diff >= MIN_HOLD_TIME:
            if last_trade == "BUY" and price_diff >= profit_threshold:
                log_trade(timestamp, token, "SELL", current_price)
                del trade_positions[token]
                trade_cooldowns[token] = timestamp
            elif last_trade == "SELL" and price_diff <= -profit_threshold:
                log_trade(timestamp, token, "BUY", current_price)
                del trade_positions[token]
                trade_cooldowns[token] = timestamp
        return  

    # Enter Trade
    if ema_short > ema_long and current_price <= lower_band and rsi < 30:
        trade_positions[token] = {"entry_price": current_price, "entry_time": timestamp, "type": "BUY"}
        log_trade(timestamp, token, "BUY", current_price)
        # Call place_order() for BUY
        place_order("BUY", token, current_price, session_data["data"]["jwtToken"], key_secret[0])
        log_order(timestamp, token, "BUY", current_price)  # Log the order

    elif ema_short < ema_long and current_price >= upper_band and rsi > 70:
        trade_positions[token] = {"entry_price": current_price, "entry_time": timestamp, "type": "SELL"}
        log_trade(timestamp, token, "SELL", current_price)
        # Call place_order() for BUY
        place_order("SELL", token, current_price, session_data["data"]["jwtToken"], key_secret[0])
        log_order(timestamp, token, "SELL", current_price)  # Log the order
# -----------------------------------------------
# WebSocket Handlers
# -----------------------------------------------

def on_data(wsapp, message):
    """Handle incoming WebSocket data."""
    try:
        token = str(message.get("token"))
        close_price = float(message.get("last_traded_price"))
        timestamp = datetime.datetime.now()

        if token not in price_data:
            price_data[token] = []
        price_data[token].append(close_price)
        
        if len(price_data[token]) > max(EMA_LONG_PERIOD, BOLLINGER_PERIOD):
            price_data[token].pop(0)
        
        decide_trade(token, price_data[token], timestamp)

    except Exception as e:
        print(f"Error in on_data: {e}")

# -----------------------------------------------
# Main Execution
# -----------------------------------------------

if __name__ == "__main__":
    # sws.on_open = lambda wsapp: sws.subscribe("stream_1", 3, [{"exchangeType": 1, "tokens": ["16675", "21808", "3499", "3351", "694"]}])
    sws.on_open = lambda wsapp: sws.subscribe("stream_1", 3, [{"exchangeType": 1, "tokens": ["26009"]}])

    sws.on_data = on_data
    sws.on_error = lambda wsapp, error: print(f"WebSocket error: {error}")
    sws.connect()