# import time
# import datetime
# import csv
# import threading
# from SmartApi.smartWebSocketV2 import SmartWebSocketV2
# from SmartApi import SmartConnect
# from pyotp import TOTP
# import numpy as np

# # SmartAPI Setup
# API_KEY = "4GznkDiG"
# CLIENT_ID = "R103352"
# PIN = 7020
# TOTP_SECRET = "RV62S7GJBGHGWKRAYSQ6SRTPVM"

# obj = SmartConnect(API_KEY)
# data = obj.generateSession(CLIENT_ID, PIN, TOTP(TOTP_SECRET).now())
# feed_token = obj.getfeedToken()

# # Define token list for the stocks
# token_list = [
#        {"exchangeType": 1, "tokens": ["1964"]},  # trent
#     {"exchangeType": 1, "tokens": ["10999"]},  #maruti
#     {"exchangeType": 1, "tokens": ["3432"]},  # tatconsumer
#     {"exchangeType": 1, "tokens": ["1660"]},  # itc
#     {"exchangeType": 1, "tokens": ["1348"]},  # heromotoco 

# ]
  

# # CSV File Setup
# filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".csv"
# csv_path = rf'D:\Angel_Smart_Api\{filename}'

# # WebSocket Initialization
# sws = SmartWebSocketV2(data["data"]["jwtToken"], API_KEY, CLIENT_ID, feed_token)

# # Historical Data Storage (For Tick-Based Buffer)
# price_history = []
# highs = []
# lows = []
# closes = []
# BOLLINGER_WINDOW = 20  # Bollinger Bands needs 20 ticks
# ATR_WINDOW = 14  # ATR needs 14 ticks

# # Global Variables for Indicators
# upper_band, lower_band, atr_value = None, None, None

# # WebSocket Reconnection Management
# MAX_RETRIES = 5
# retry_count = 0

# # Function: Bollinger Bands (Direct Calculation)
# def calculate_bollinger_bands(prices, window=20):
#     """Calculate Bollinger Bands using a list of prices."""
#     if len(prices) < window:
#         return None, None  # Not enough data
    
#     # Simple Moving Average (SMA)
#     sma = np.mean(prices[-window:])
    
#     # Standard Deviation
#     std = np.std(prices[-window:])
    
#     # Upper and Lower Bands
#     upper_band = sma + (2 * std)  # 2 standard deviations above the SMA
#     lower_band = sma - (2 * std)  # 2 standard deviations below the SMA
    
#     return upper_band, lower_band

# # Function: ATR (Direct Calculation)
# def calculate_atr(highs, lows, closes, window=14):
#     """Calculate ATR using lists of high, low, and close prices."""
#     if len(highs) < window:
#         return None  # Not enough data
    
#     # Calculate True Range (TR)
#     tr_values = []
#     for i in range(1, len(highs)):
#         tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
#         tr_values.append(tr)
    
#     # Average True Range (ATR)
#     atr = np.mean(tr_values[-window:])
#     return atr

# # Function: Process Indicators in Separate Thread
# def process_indicators():
#     """Runs Bollinger Bands & ATR calculations in a separate thread."""
#     global upper_band, lower_band, atr_value

#     if len(price_history) >= BOLLINGER_WINDOW:
#         upper_band, lower_band = calculate_bollinger_bands(price_history)

#     if len(highs) >= ATR_WINDOW:
#         atr_value = calculate_atr(highs, lows, closes)

# # WebSocket: Data Handling
# def on_data(wsapp, message):
#     global price_history, highs, lows, closes

#     try:
#         # Extract required fields
#         last_price = message['last_traded_price']
#         high_price = message['high_price_of_the_day']
#         low_price = message['low_price_of_the_day']

#         # Store Values in Lists
#         price_history.append(last_price)
#         highs.append(high_price)
#         lows.append(low_price)
#         closes.append(last_price)  # Assuming close = last_traded_price

#         # Maintain Recent Data (Prevent Overflow)
#         price_history = price_history[-BOLLINGER_WINDOW:]
#         highs = highs[-ATR_WINDOW:]
#         lows = lows[-ATR_WINDOW:]
#         closes = closes[-ATR_WINDOW:]

#         # Run indicator calculation in a separate thread
#         threading.Thread(target=process_indicators, daemon=True).start()

#         # Append calculated indicators to message
#         message["UPPER BAND"] = upper_band
#         message["LOWER BAND"] = lower_band
#         message["ATR"] = atr_value
#         message["exchange_timestamp"] = datetime.datetime.fromtimestamp(
#             message.get("exchange_timestamp", 0) / 1000
#         ).strftime('%Y-%m-%d %H:%M:%S')

#         # Print Data
#         print("Ticks:", message)

#         # Append Data to CSV File
#         with open(csv_path, mode='a', newline='') as file:
#             writer = csv.DictWriter(file, fieldnames=message.keys())
#             if file.tell() == 0:  # Write Header If File is Empty
#                 writer.writeheader()
#             writer.writerow(message)

#     except Exception as e:
#         print(f" Data Processing Error: {e}")

# # WebSocket: Open Connection
# def on_open(wsapp):
#     print(" WebSocket Connection Opened")
#     sws.subscribe("stream_1", 3, token_list)  # Subscription mode 3 as example

# # WebSocket: Handle Errors
# def on_error(wsapp, error):
#     print(f" WebSocket Error: {error}")
#     if 'Timeout' in str(error):
#         print(" Timeout detected, reconnecting...")
#         reconnect()

# # WebSocket: Handle Closure
# def on_close(wsapp, close_status_code, close_msg):
#     print(f" WebSocket Closed [Code: {close_status_code}] - {close_msg}")
#     reconnect()

# # Reconnection Logic
# def reconnect():
#     """Handles WebSocket Reconnection with Limits"""
#     global sws, retry_count

#     if retry_count >= MAX_RETRIES:
#         print(" Max retries reached. Stopping reconnection attempts.")
#         return

#     print(f" Attempting to Reconnect... (Attempt {retry_count+1})")
#     retry_count += 1

#     try:
#         sws.close()
#         time.sleep(2)

#         # Reinitialize WebSocket
#         sws = SmartWebSocketV2(data["data"]["jwtToken"], API_KEY, CLIENT_ID, feed_token)
#         sws.on_open = on_open
#         sws.on_data = on_data
#         sws.on_error = on_error
#         sws.on_close = on_close

#         sws.connect()
#     except Exception as e:
#         print(f" Reconnection Failed: {e}")
#         time.sleep(5)
#         reconnect()

# # Assign WebSocket Callbacks
# sws.on_open = on_open
# sws.on_data = on_data
# sws.on_error = on_error
# sws.on_close = on_close

# # Start WebSocket Connection
# try:
#     sws.connect()
# except Exception as e:
#     print(f" Initial Connection Failed: {e}")
#     reconnect()

# import time
# import datetime
# import csv
# import threading
# import numpy as np
# from SmartApi.smartWebSocketV2 import SmartWebSocketV2
# from SmartApi import SmartConnect
# from pyotp import TOTP

# # SmartAPI Setup
# API_KEY = "4GznkDiG"
# CLIENT_ID = "R103352"
# PIN = 7020
# TOTP_SECRET = "RV62S7GJBGHGWKRAYSQ6SRTPVM"

# obj = SmartConnect(API_KEY)
# data = obj.generateSession(CLIENT_ID, PIN, TOTP(TOTP_SECRET).now())
# feed_token = obj.getfeedToken()

# # Define token list for the stocks
# token_list = [
#     {"exchangeType": 1, "tokens": ["25"]},  # ADANIENT
#     {"exchangeType": 1, "tokens": ["4306"]},  # SHRIRAMFIN
#     {"exchangeType": 1, "tokens": ["14977"]},  # POWERGRID
#     {"exchangeType": 1, "tokens": ["15083"]},  # ADANIPORTS
#     {"exchangeType": 1, "tokens": ["5258"]},  # INDUSINDBK
#     # {"exchangeType": 1, "tokens": ["26009"]},  # BANKNIFTY

# ]

# # CSV File Setup
# filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".csv"
# csv_path = rf'D:\Angel_Smart_Api\{filename}'

# # WebSocket Initialization
# sws = SmartWebSocketV2(data["data"]["jwtToken"], API_KEY, CLIENT_ID, feed_token)

# # Historical Data Storage (For Tick-Based Buffer)
# price_history = []
# highs = []
# lows = []
# closes = []

# # Indicator Parameters
# BOLLINGER_WINDOW = 20
# ATR_WINDOW = 14
# EMA_SHORT_PERIOD = 12
# EMA_LONG_PERIOD = 26
# RSI_PERIOD = 14

# # Global Variables for Indicators
# upper_band, lower_band, atr_value = None, None, None
# ema_short, ema_long, rsi_value = None, None, None

# # Function: Exponential Moving Average (EMA)
# def calculate_ema(prices, period):
#     """Calculate EMA using a list of prices."""
#     if len(prices) < period:
#         return None
#     return np.round(np.mean(prices[-period:]), 2)  # Simple EMA Calculation

# # Function: RSI Calculation
# def calculate_rsi(prices, period=14):
#     """Calculate Relative Strength Index (RSI)."""
#     if len(prices) < period + 1:
#         return None
#     deltas = np.diff(prices)
#     gains = np.where(deltas > 0, deltas, 0)
#     losses = np.where(deltas < 0, -deltas, 0)
#     avg_gain = np.mean(gains[-period:])
#     avg_loss = np.mean(losses[-period:])
#     if avg_loss == 0:
#         return 100  # Avoid division by zero
#     rs = avg_gain / avg_loss
#     return np.round(100 - (100 / (1 + rs)), 2)

# # Function: Bollinger Bands Calculation
# def calculate_bollinger_bands(prices, window=20):
#     if len(prices) < window:
#         return None, None
#     sma = np.mean(prices[-window:])
#     std = np.std(prices[-window:])
#     return sma + (2 * std), sma - (2 * std)

# # Function: ATR Calculation
# def calculate_atr(highs, lows, closes, window=14):
#     if len(highs) < window:
#         return None
#     tr_values = [
#         max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
#         for i in range(1, len(highs))
#     ]
#     return np.mean(tr_values[-window:])

# # Function: Process Indicators in Separate Thread
# def process_indicators():
#     global upper_band, lower_band, atr_value, ema_short, ema_long, rsi_value
    
#     if len(price_history) >= BOLLINGER_WINDOW:
#         upper_band, lower_band = calculate_bollinger_bands(price_history)
    
#     if len(highs) >= ATR_WINDOW:
#         atr_value = calculate_atr(highs, lows, closes)
    
#     ema_short = calculate_ema(closes, EMA_SHORT_PERIOD)
#     ema_long = calculate_ema(closes, EMA_LONG_PERIOD)
#     rsi_value = calculate_rsi(closes, RSI_PERIOD)

# # WebSocket: Data Handling
# def on_data(wsapp, message):
#     global price_history, highs, lows, closes
    
#     try:
#         last_price = message['last_traded_price']
#         high_price = message['high_price_of_the_day']
#         low_price = message['low_price_of_the_day']
        
#         price_history.append(last_price)
#         highs.append(high_price)
#         lows.append(low_price)
#         closes.append(last_price)
        
#         price_history = price_history[-BOLLINGER_WINDOW:]
#         highs = highs[-ATR_WINDOW:]
#         lows = lows[-ATR_WINDOW:]
#         closes = closes[-EMA_LONG_PERIOD:]
        
#         threading.Thread(target=process_indicators, daemon=True).start()
        
#         message.update({
#             "UPPER BAND": upper_band,
#             "LOWER BAND": lower_band,
#             "ATR": atr_value,
#             "EMA SHORT": ema_short,
#             "EMA LONG": ema_long,
#             "RSI": rsi_value,
#             "exchange_timestamp": datetime.datetime.fromtimestamp(
#                 message.get("exchange_timestamp", 0) / 1000
#             ).strftime('%Y-%m-%d %H:%M:%S')
#         })
        
#         print("Ticks:", message)
        
#         with open(csv_path, mode='a', newline='') as file:
#             writer = csv.DictWriter(file, fieldnames=message.keys())
#             if file.tell() == 0:
#                 writer.writeheader()
#             writer.writerow(message)
    
#     except Exception as e:
#         print(f"Data Processing Error: {e}")

# # WebSocket Callbacks
# sws.on_open = lambda wsapp: sws.subscribe("stream_1", 3, token_list)
# sws.on_data = on_data
# sws.on_error = lambda wsapp, error: print(f"WebSocket Error: {error}")
# sws.on_close = lambda wsapp, close_status_code, close_msg: print(f"WebSocket Closed: {close_status_code} - {close_msg}")

# # Start WebSocket Connection
# try:
#     sws.connect()
# except Exception as e:
#     print(f"Initial Connection Failed: {e}")
import time
import datetime
import csv
import threading
import numpy as np
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from SmartApi import SmartConnect
from pyotp import TOTP
import pandas as pd

# SmartAPI Setup
API_KEY = "4GznkDiG"
CLIENT_ID = "R103352"
PIN = 7020
TOTP_SECRET = "RV62S7GJBGHGWKRAYSQ6SRTPVM"

obj = SmartConnect(API_KEY)
data = obj.generateSession(CLIENT_ID, PIN, TOTP(TOTP_SECRET).now())
feed_token = obj.getfeedToken()

# Define token list for the stocks
token_list = [
    {"exchangeType": 1, "tokens": ["25"]},  # ADANIENT
    {"exchangeType": 1, "tokens": ["4306"]},  # SHRIRAMFIN
    {"exchangeType": 1, "tokens": ["14977"]},  # POWERGRID
    {"exchangeType": 1, "tokens": ["15083"]},  # ADANIPORTS
    {"exchangeType": 1, "tokens": ["5258"]},  # INDUSINDBK
    # {"exchangeType": 1, "tokens": ["26009"]},  # BANKNIFTY

]

# CSV File Setup
filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".csv"
csv_path = rf'C:\ALGOTRADING_PROJECT\{filename}'

# WebSocket Initialization
sws = SmartWebSocketV2(data["data"]["jwtToken"], API_KEY, CLIENT_ID, feed_token)
# Data Storage
data_df = pd.DataFrame()
lock = threading.Lock()

# Function to check if the current time is within market hours (9:15 AM - 3:30 PM)
def is_market_open():
    now = datetime.datetime.now()
    return (now.hour == 9 and now.minute >= 15) or (9 < now.hour < 15) or (now.hour == 15 and now.minute <= 30)
# Historical Data Storage (For Tick-Based Buffer)
price_history = []
highs = []
lows = []
closes = []

# Indicator Parameters
BOLLINGER_WINDOW = 20
ATR_WINDOW = 14
EMA_SHORT_PERIOD = 12
EMA_LONG_PERIOD = 26
RSI_PERIOD = 14

# Global Variables for Indicators
upper_band, lower_band, atr_value = None, None, None
ema_short, ema_long, rsi_value = None, None, None

# Function: Exponential Moving Average (EMA)
def calculate_ema(prices, period):
    """Calculate EMA using a list of prices."""
    if len(prices) < period:
        return None
    return np.round(np.mean(prices[-period:]), 2)  # Simple EMA Calculation

# Function: RSI Calculation
def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index (RSI)."""
    if len(prices) < period + 1:
        return None
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100  # Avoid division by zero
    rs = avg_gain / avg_loss
    return np.round(100 - (100 / (1 + rs)), 2)

# Function: Bollinger Bands Calculation
def calculate_bollinger_bands(prices, window=20):
    if len(prices) < window:
        return None, None
    sma = np.mean(prices[-window:])
    std = np.std(prices[-window:])
    return sma + (2 * std), sma - (2 * std)

# Function: ATR Calculation
def calculate_atr(highs, lows, closes, window=14):
    if len(highs) < window:
        return None
    tr_values = [
        max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        for i in range(1, len(highs))
    ]
    return np.mean(tr_values[-window:])

# Function: Process Indicators in Separate Thread
def process_indicators():
    global upper_band, lower_band, atr_value, ema_short, ema_long, rsi_value
    
    if len(price_history) >= BOLLINGER_WINDOW:
        upper_band, lower_band = calculate_bollinger_bands(price_history)
    
    if len(highs) >= ATR_WINDOW:
        atr_value = calculate_atr(highs, lows, closes)
    
    ema_short = calculate_ema(closes, EMA_SHORT_PERIOD)
    ema_long = calculate_ema(closes, EMA_LONG_PERIOD)
    rsi_value = calculate_rsi(closes, RSI_PERIOD)

# Function to save DataFrame at 3:30 PM
def save_dataframe():
    global data_df
    while True:
        now = datetime.datetime.now()
        if now.hour == 15 and now.minute == 30:  # 3:30 PM
            filename = f"C:/ALGOTRADING_PROJECT/{now.strftime('%Y%m%d-%H%M%S')}.csv"
            with lock:
                if not data_df.empty:
                    data_df.to_csv(filename, index=False)
                    print(f"Data saved to {filename}")
                    data_df = pd.DataFrame()  # Clear DataFrame after saving
            time.sleep(60)  # Avoid multiple saves in the same minute
        time.sleep(10)  # Check every 10 seconds

# WebSocket: Data Handling
def on_data(wsapp, message):
    global data_df,price_history, highs, lows, closes
    
    try:
        now = datetime.datetime.now()
        if not is_market_open():
            return  # Ignore data outside market hours
    
        last_price = message['last_traded_price']
        high_price = message['high_price_of_the_day']
        low_price = message['low_price_of_the_day']
        
        price_history.append(last_price)
        highs.append(high_price)
        lows.append(low_price)
        closes.append(last_price)
        
        price_history = price_history[-BOLLINGER_WINDOW:]
        highs = highs[-ATR_WINDOW:]
        lows = lows[-ATR_WINDOW:]
        closes = closes[-EMA_LONG_PERIOD:]
        
        threading.Thread(target=process_indicators, daemon=True).start()
        
        message.update({
            "UPPER BAND": upper_band,
            "LOWER BAND": lower_band,
            "ATR": atr_value,
            "EMA SHORT": ema_short,
            "EMA LONG": ema_long,
            "RSI": rsi_value,
            "exchange_timestamp": datetime.datetime.fromtimestamp(
                message.get("exchange_timestamp", 0) / 1000
            ).strftime('%Y-%m-%d %H:%M:%S')
        })
        # Store data in DataFrame safely using a lock
        with lock:
            temp_df = pd.DataFrame([message])
            data_df = pd.concat([data_df, temp_df], ignore_index=True)

        
        print("Ticks:", message)
        
        with open(csv_path, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=message.keys())
            if file.tell() == 0:
                writer.writeheader()
            writer.writerow(message)
    
    except Exception as e:
        print(f"Data Processing Error: {e}")

# WebSocket Callbacks
sws.on_open = lambda wsapp: sws.subscribe("stream_1", 3, token_list)
sws.on_data = on_data
sws.on_error = lambda wsapp, error: print(f"WebSocket Error: {error}")
sws.on_close = lambda wsapp, close_status_code, close_msg: print(f"WebSocket Closed: {close_status_code} - {close_msg}")

# Start WebSocket Connection
try:
    sws.connect()
    threading.Thread(target=save_dataframe, daemon=True).start()
except Exception as e:
    print(f"Initial Connection Failed: {e}")

