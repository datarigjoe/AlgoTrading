import os
import datetime
import csv
import pandas as pd
from pyotp import TOTP
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2

# API and WebSocket setup
key_path = r"D:\Angel_Smart_Api"
os.chdir(key_path)
key_secret = open("key.txt", "r").read().split()

obj = SmartConnect(api_key=key_secret[0])
data = obj.generateSession(key_secret[2], key_secret[3], TOTP(key_secret[4]).now())
feed_token = obj.getfeedToken()

sws = SmartWebSocketV2(data["data"]["jwtToken"], key_secret[0], key_secret[2], feed_token)

# Indicator parameters
EMA_SHORT_PERIOD = 9
EMA_LONG_PERIOD = 21
BOLLINGER_PERIOD = 20
BOLLINGER_STD_DEV = 2
RSI_PERIOD = 14
TRADE_COOLDOWN_PERIOD = datetime.timedelta(seconds=180)

# Trade Parameters
PROFIT_THRESHOLD = 0.4  # Dynamic profit percentage
MIN_HOLD_TIME = datetime.timedelta(minutes=3)

data_buffer = {}
trade_positions = {}
trade_cooldowns = {}

def log_debug(timestamp, message):
    log_file = os.path.join(key_path, f"debug_logs_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv")
    file_exists = os.path.isfile(log_file)
    with open(log_file, 'a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Message"])
        writer.writerow([timestamp, message])
    print(f"[DEBUG] {message}")

def calculate_ema(prices, period):
    return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1] if len(prices) >= period else None

def calculate_bollinger_bands(prices, period, std_dev):
    if len(prices) < period:
        return None, None
    rolling_mean = pd.Series(prices).rolling(window=period).mean()
    rolling_std = pd.Series(prices).rolling(window=period).std()
    return rolling_mean.iloc[-1] + (rolling_std.iloc[-1] * std_dev), rolling_mean.iloc[-1] - (rolling_std.iloc[-1] * std_dev)

def calculate_rsi(prices, period=RSI_PERIOD):
    if len(prices) < period:
        return None
    delta = pd.Series(prices).diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

def calculate_percentage_difference(entry_price, current_price):
    return ((current_price - entry_price) / entry_price) * 100

def log_trade(timestamp, token, trade_type, price):
    csv_file = os.path.join(key_path, f"trades_ema_rsi_bands_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv")
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Token", "Trade Type", "Price"])
        writer.writerow([timestamp, token, trade_type, price])

def decide_trade(token, prices, timestamp):
    global trade_positions, trade_cooldowns
    if len(prices) < max(EMA_LONG_PERIOD, BOLLINGER_PERIOD):
        return
    
    current_price = prices[-1]
    ema_short = calculate_ema(prices, EMA_SHORT_PERIOD)
    ema_long = calculate_ema(prices, EMA_LONG_PERIOD)
    upper_band, lower_band = calculate_bollinger_bands(prices, BOLLINGER_PERIOD, BOLLINGER_STD_DEV)
    rsi = calculate_rsi(prices)
    
    if rsi is None or ema_short is None or ema_long is None or upper_band is None or lower_band is None:
        return
    
    last_trade = trade_positions.get(token, {}).get("type", None)
    if token in trade_cooldowns and (timestamp - trade_cooldowns[token]) < TRADE_COOLDOWN_PERIOD:
        return  
    
    if token in trade_positions:
        entry_price = trade_positions[token]["entry_price"]
        entry_time = trade_positions[token]["entry_time"]
        price_diff = calculate_percentage_difference(entry_price, current_price)
        time_diff = timestamp - entry_time
        if time_diff >= MIN_HOLD_TIME:
            if last_trade == "BUY" and price_diff >= PROFIT_THRESHOLD:
                log_trade(timestamp, token, "SELL", current_price)
                del trade_positions[token]
                trade_cooldowns[token] = timestamp
            elif last_trade == "SELL" and price_diff <= -PROFIT_THRESHOLD:
                log_trade(timestamp, token, "BUY", current_price)
                del trade_positions[token]
                trade_cooldowns[token] = timestamp
        return  
    if token not in trade_positions:  # Ensure no active position before entering
    # BUY Condition: EMA Short crosses above EMA Long & Price near/below Lower Band & RSI confirms strength
        if ema_short > ema_long and current_price <= lower_band and rsi < 30:
            trade_positions[token] = {"entry_price": current_price, "entry_time": timestamp, "type": "BUY"}
            log_trade(timestamp, token, "BUY", current_price)

    # SELL Condition: EMA Short crosses below EMA Long & Price near/above Upper Band & RSI confirms weakness
        elif ema_short < ema_long and current_price >= upper_band and rsi > 70:
            trade_positions[token] = {"entry_price": current_price, "entry_time": timestamp, "type": "SELL"}
            log_trade(timestamp, token, "SELL", current_price)

    # if ema_short > ema_long and current_price < upper_band and rsi < 30 and last_trade is None:
    #     trade_positions[token] = {"entry_price": current_price, "entry_time": timestamp, "type": "BUY"}
    #     log_trade(timestamp, token, "BUY", current_price)
    # elif ema_short < ema_long and current_price > lower_band and rsi > 70 and last_trade is None:
    #     trade_positions[token] = {"entry_price": current_price, "entry_time": timestamp, "type": "SELL"}
    #     log_trade(timestamp, token, "SELL", current_price)

def on_open(wsapp):
    sws.subscribe("stream_1", 3, [{"exchangeType": 1, "tokens": ["10604", "1363", "7229", "694", "1232"]}])

def on_error(wsapp, error):
    print(f"WebSocket error: {error}")
    sws.connect()

def on_data(wsapp, message):
    try:
        token = str(message.get("token"))
        close_price = float(message.get("last_traded_price"))
        timestamp = datetime.datetime.now()
        if token not in data_buffer:
            data_buffer[token] = []
        data_buffer[token].append(close_price)
        if len(data_buffer[token]) > max(EMA_LONG_PERIOD, BOLLINGER_PERIOD):
            data_buffer[token].pop(0)
        decide_trade(token, data_buffer[token], timestamp)
    except Exception as e:
        log_debug(datetime.datetime.now(), f"Error in on_data: {e}")

def main():
    sws.on_open = on_open
    sws.on_data = on_data
    sws.on_error = on_error
    sws.connect()

if __name__ == "__main__":
    main()