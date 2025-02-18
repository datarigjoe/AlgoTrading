# import ast
# import os
# import datetime
# import csv
# import pandas as pd
# import numpy as np
# from pyotp import TOTP
# from SmartApi import SmartConnect
# from SmartApi.smartWebSocketV2 import SmartWebSocketV2

# # API and WebSocket setup
# key_path = r"C:\ALGOTRADING_PROJECT\OldDataTesting"

# # Indicator Parameters
# # -----------------------------------------------

# EMA_SHORT_PERIOD = 9  # Short-term EMA
# EMA_LONG_PERIOD = 21  # Long-term EMA
# BOLLINGER_PERIOD = 20  # Bollinger Bands period
# BOLLINGER_STD_DEV = 2  # Standard deviation for Bollinger Bands
# RSI_PERIOD = 14  # RSI period
# PROFIT_THRESHOLD=.4
# # Trade Settings
# COOLDOWN_PERIOD = datetime.timedelta(seconds=180)  # Cooldown between trades
# MIN_HOLD_TIME = datetime.timedelta(minutes=3)  # Minimum holding time before selling
# # TRADE_CLOSE_TIME = datetime.time(15, 5)  # Hard stop for trades at 3:05 PM
# # TRADE_CLOSE_START = datetime.time(15, 4)  # Start force-selling at 3:04 PM

# # Data Buffers
# last_traded_price_data = {}  # Stores historical last_traded_price data per token
# trade_positions = {}  # Active trades
# trade_cooldowns = {}  # Cooldowns to prevent quick re-trading---

# def calculate_ema(last_traded_prices, period):
#     """Calculate Exponential Moving Average (EMA)."""
#     return pd.Series(last_traded_prices).ewm(span=period, adjust=False).mean().iloc[-1] if len(last_traded_prices) >= period else None

# def calculate_bollinger_bands(last_traded_prices, period, std_dev):
#     """Calculate Bollinger Bands (Upper and Lower)."""
#     if len(last_traded_prices) < period:
#         return None, None
#     rolling_mean = pd.Series(last_traded_prices).rolling(window=period).mean()
#     rolling_std = pd.Series(last_traded_prices).rolling(window=period).std()
#     upper_band = rolling_mean.iloc[-1] + (rolling_std.iloc[-1] * std_dev)
#     lower_band = rolling_mean.iloc[-1] - (rolling_std.iloc[-1] * std_dev)
#     return upper_band, lower_band

# def calculate_rsi(last_traded_prices, period=RSI_PERIOD):
#     """Calculate Relative Strength Index (RSI)."""
#     if len(last_traded_prices) < period:
#         return None
#     delta = pd.Series(last_traded_prices).diff()
#     gain = delta.where(delta > 0, 0).rolling(window=period).mean()
#     loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
#     rs = gain / loss
#     return 100 - (100 / (1 + rs)).iloc[-1]

# def calculate_percentage_difference(entry_last_traded_price, current_last_traded_price):
#     """Calculate percentage difference between two last_traded_prices."""
#     return ((current_last_traded_price - entry_last_traded_price) / entry_last_traded_price) * 100

# # def get_profit_threshold(timestamp):
# #     """Dynamically adjust profit threshold based on market time."""
# #     market_open_time = datetime.time(9, 15)
# #     high_profit_time = datetime.time(9, 45)
# #     return 0.6 if market_open_time <= timestamp.time() <= high_profit_time else 0.4

# def log_trade(timestamp, token, trade_type, last_traded_price):
#     csv_file = os.path.join(key_path, f"bollinger_ema_trades_TestingOldData_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv")
#     file_exists = os.path.isfile(csv_file)
#     with open(csv_file, mode='a', newline='') as file:
#         writer = csv.writer(file)
#         if not file_exists:
#             writer.writerow(["Timestamp", "Token", "Entry/Exit", "last_traded_price"])
#         writer.writerow([timestamp, token, trade_type, last_traded_price])

# # Trade Decision Logic
# # -----------------------------------------------
# # Trade Decision Function
# def decide_trade(token, prices, timestamp, backtest=True):
#     global trade_positions, trade_cooldowns
    
#     if len(prices) < max(EMA_LONG_PERIOD, BOLLINGER_PERIOD, RSI_PERIOD):
#         return  # Not enough data
    
#     data = pd.DataFrame(prices, columns=['last_traded_price'])
    
#     # Calculate Indicators
#     data['ema_short'] = calculate_ema(data['last_traded_price'], EMA_SHORT_PERIOD)
#     data['ema_long'] = calculate_ema(data['last_traded_price'], EMA_LONG_PERIOD)
#     data['rsi'] = calculate_rsi(data['last_traded_price'], RSI_PERIOD)
#     data['sma'], data['upper_bb'], data['lower_bb'] = calculate_bollinger_bands(data['last_traded_price'], BOLLINGER_PERIOD,BOLLINGER_STD_DEV)
    
#     current_price = data.iloc[-1]['last_traded_price']
#     ema_short = data.iloc[-1]['ema_short']
#     ema_long = data.iloc[-1]['ema_long']
#     rsi = data.iloc[-1]['rsi']
#     lower_bb = data.iloc[-1]['lower_bb']
#     upper_bb = data.iloc[-1]['upper_bb']
    
#     # Cooldown check (Disabled in Backtesting)
#     if not backtest and token in trade_cooldowns and timestamp < trade_cooldowns[token]:
#         return
    
#     # BUY Condition
#     if (ema_short > ema_long and current_price < lower_bb and rsi < 30 and token not in trade_positions):
#         trade_positions[token] = {'buy_price': current_price, 'buy_time': timestamp}
#         trade_cooldowns[token] = timestamp + COOLDOWN_PERIOD
#         # print(f"[BUY] {token} at {current_price} on {timestamp}")
#         return
    
#     # SELL Condition
#     if token in trade_positions:
#         buy_info = trade_positions[token]
#         if (timestamp - buy_info['buy_time'] >= MIN_HOLD_TIME and 
#             (current_price >= buy_info['buy_price'] * PROFIT_THRESHOLD or
#              ema_short < ema_long or
#              current_price > upper_bb or
#              rsi > 70)):
#             # print(f"[SELL] {token} at {current_price} on {timestamp} (Bought at {buy_info['buy_price']})")
#             del trade_positions[token]
#             trade_cooldowns[token] = timestamp + COOLDOWN_PERIOD
# # -----------------------------------------------

# # def process_json_string(json_str):
# #     """
# #     Tries to parse a string that is in JSON or Python literal format.
# #     Returns the parsed object if successful; otherwise, returns None.
# #     """
# #     try:
# #         # Attempt to parse assuming valid JSON format.
# #         # If keys use single quotes instead of double quotes,
# #         # this will fail, so we'll try ast.literal_eval as a fallback.
# #         return ast.literal_eval(json_str)
# #     except (ValueError, SyntaxError):
# #         return None

# # def read_csv_and_trade(csv_filepath):
# #     """
# #     Reads a CSV file from a local folder and passes the data to the decide_trade function.
    
# #     Parameters:
# #         csv_filepath (str): The full path to the CSV file.
    
# #     Returns:
# #         str: The trade decision based on the CSV data.
# #     """
# #     try:
# #         # Read the CSV file into a pandas DataFrame.
# #         data = pd.read_csv(csv_filepath)
# #         print(f"CSV data loaded successfully from: {csv_filepath}")
# #         data['exchange_timestamp'] = pd.to_datetime(data['exchange_timestamp'])
# #         data = data.sort_values(by='exchange_timestamp')
# #         data = data[(data['token'] == 694)&
# #                 (data['exchange_timestamp'].dt.time >= pd.to_datetime('9:15:00').time()) & 
# #                 (data['exchange_timestamp'].dt.time <= pd.to_datetime('11:40:00').time())]
# #         prices = []
# #         timestamps = []
    
# #         for i, row in data.iterrows():
# #             prices.append(row['last_traded_price'])
# #             timestamps.append(row['exchange_timestamp'])
        
    
# #         for i, (index, row) in enumerate(data.iterrows()):
# #             if i >= 10:
# #                 print("\nReached 10 iterations. Exiting loop.")
# #                 # break
# #             print(f"\nRow {index}:")
# #             # for column, value in row.items():
               
# #             #         # Check if the value is a string that might contain JSON data.
# #             #     if isinstance(value, str):
# #             #             # Try to process the string as JSON/Python literal.
# #             #             parsed_value = process_json_string(value)
# #             #             if parsed_value is not None:
# #             #                 print(f"  {column} (parsed from JSON):")
# #             #                 # If the parsed value is iterable (list or dict), iterate through it.
# #             #                 if isinstance(parsed_value, list):
# #             #                     for idx, item in enumerate(parsed_value):
# #             #                         print(f"    Item {idx}: {item}")
# #             #                 elif isinstance(parsed_value, dict):
# #             #                     for key, val in parsed_value.items():
# #             #                         print(f"    {key}: {val}")
# #             #                 else:
# #             #                     # If it's not a list or dict, just print it.
# #             #                     print(f"    {parsed_value}")
# #             #                 continue  # Skip printing the original string since we've parsed it.
# #             #              # Default printing if no JSON conversion is done.
# #                         # print(f"  {column}: {value}")


# #         # Pass the data to the decide_trade function.
            
# #         if i >= max(EMA_LONG_PERIOD, BOLLINGER_PERIOD, RSI_PERIOD):
# #             decision=decide_trade(row['token'], prices, row['exchange_timestamp'], backtest=True)

#     # except FileNotFoundError:
#     #     raise FileNotFoundError(f"CSV file not found at the path: {csv_filepath}")
#     # except pd.errors.ParserError as e:
#     #     raise ValueError(f"Error parsing CSV file: {e}")
#     # except Exception as e:
#     #     raise RuntimeError(f"An error occurred while processing the CSV file: {e}")


# def read_csv_and_trade(csv_filepath):
#     """
#     Reads a CSV file from a local folder and passes the data to the decide_trade function.

#     Parameters:
#         csv_filepath (str): The full path to the CSV file.

#     Returns:
#         None
#     """
#     try:
#         # Read the CSV file into a pandas DataFrame.
#         data = pd.read_csv(csv_filepath)
#         print(f"CSV data loaded successfully from: {csv_filepath}")

#         # Convert exchange_timestamp to datetime and sort
#         data['exchange_timestamp'] = pd.to_datetime(data['exchange_timestamp'])
#         data = data.sort_values(by='exchange_timestamp')
#         # List of columns to keep
#         columns_to_keep = ['token', 'exchange_timestamp', 'last_traded_price']

#         # Drop all other columns
#         data = data[columns_to_keep]


#         # Initialize price storage
#         prices = []
        
#         # Iterate over each row
#         for i, row in data.iterrows():
#             token = row['token']
#             timestamp = row['exchange_timestamp']
#             last_traded_price = row['last_traded_price']
            
#             # Append the new price
#             prices.append(last_traded_price)

#             # Ensure enough data points before calling `decide_trade`
#             if len(prices) >= max(EMA_LONG_PERIOD, BOLLINGER_PERIOD, RSI_PERIOD):
#                 decide_trade(token, prices, timestamp, backtest=True)
            
#             # Debugging print (Remove after testing)
#             if i < 10:
#                 print(f"Processed row {i}: Token={token}, Price={last_traded_price}, Timestamp={timestamp}")
        
#     except FileNotFoundError:
#         raise FileNotFoundError(f"CSV file not found at the path: {csv_filepath}")
#     except pd.errors.ParserError as e:
#         raise ValueError(f"Error parsing CSV file: {e}")
#     except Exception as e:
#         raise RuntimeError(f"An error occurred while processing the CSV file: {e}")

# def main():

 
#     csv_file_path = r"C:\Users\LENOVO\Downloads\20250210-090040.csv"
    
#     try:
#         # Get the trade decision based on the CSV file's data.
#         trade_decision = read_csv_and_trade(csv_file_path)
#         trade_decision['exchange_timestamp'] = pd.to_datetime(trade_decision['exchange_timestamp'], errors='coerce')
#         print(f"Trade decision based on CSV data: {trade_decision}")
#         # Convert exchange_timestamp to datetime
        
#         csv_file = os.path.join(key_path, f"Trades_OldDataTesting_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv")
#         if not os.path.isfile(csv_file):
#             with open(csv_file, mode='w', newline='') as file:
#                 writer = csv.writer(file)
#                 writer.writerow(["Timestamp", "Token", "Entry/Exit", "last_traded_price"])

#     except Exception as error:
#         print(f"An error occurred: {error}")

# if __name__ == "__main__":
#     main()

import ast
import os
import datetime
import csv
import pandas as pd
import numpy as np


key_path = r"C:\ALGOTRADING_PROJECT\Backtesting"
EMA_SHORT_PERIOD = 9  # Short-term EMA
EMA_LONG_PERIOD = 21  # Long-term EMA
BOLLINGER_PERIOD = 20  # Bollinger Bands period
BOLLINGER_STD_DEV = 2  # Standard deviation for Bollinger Bands
RSI_PERIOD = 14  # RSI period
PROFIT_THRESHOLD = 0.4  # 0.4% profit
COOLDOWN_PERIOD = datetime.timedelta(seconds=180)  # Cooldown between trades
MIN_HOLD_TIME = datetime.timedelta(minutes=3)  # Minimum holding time before selling

# Data Buffers
trade_positions = {}  # Active trades
trade_cooldowns = {}  # Cooldowns to prevent quick re-trading
token_prices = {}  # Stores historical prices per token

# ---------------- Utility Functions ----------------

def calculate_ema(prices, period):
    return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1]

def calculate_bollinger_bands(prices, period, std_dev):
    rolling_mean = pd.Series(prices).rolling(window=period).mean()
    rolling_std = pd.Series(prices).rolling(window=period).std()
    upper_band = rolling_mean + (rolling_std * std_dev)
    lower_band = rolling_mean - (rolling_std * std_dev)
    return upper_band.iloc[-1], lower_band.iloc[-1]

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

# ---------------- Trade Logic ----------------
def log_trade(timestamp, token, action, price):
    csv_file = os.path.join(key_path, f"Trades_OldDataTesting_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv")
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, token, action, price])

def decide_trade(token, prices, timestamp):
    global trade_positions, trade_cooldowns

    if len(prices) < max(EMA_LONG_PERIOD, BOLLINGER_PERIOD):
        return
    
    current_price = prices[-1]
    ema_short = calculate_ema(prices, EMA_SHORT_PERIOD)
    ema_long = calculate_ema(prices, EMA_LONG_PERIOD)
    upper_band, lower_band = calculate_bollinger_bands(prices, BOLLINGER_PERIOD, BOLLINGER_STD_DEV)
    rsi = calculate_rsi(prices)

    if None in [rsi, ema_short, ema_long, upper_band, lower_band]:
        return
    
    last_trade = trade_positions.get(token, {}).get("type", None)

    if token in trade_cooldowns and (timestamp - trade_cooldowns[token]) < COOLDOWN_PERIOD:
        return  

    # Exit Trade
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
    # Enter Trade
    if ema_short > ema_long and current_price <= lower_band and rsi < 30:
        trade_positions[token] = {"entry_price": current_price, "entry_time": timestamp, "type": "BUY"}
        log_trade(timestamp, token, "BUY", current_price)

    elif ema_short < ema_long and current_price >= upper_band and rsi > 70:
        trade_positions[token] = {"entry_price": current_price, "entry_time": timestamp, "type": "SELL"}
        log_trade(timestamp, token, "SELL", current_price)


def read_csv_and_trade(csv_filepath):
    """
    Reads a CSV file and processes trading decisions.
    """
    try:
        data = pd.read_csv(csv_filepath)
        print(f"CSV data loaded successfully from: {csv_filepath}")

        # Convert timestamp and sort
        data['exchange_timestamp'] = pd.to_datetime(data['exchange_timestamp'])
        data = data.sort_values(by='exchange_timestamp')

        # # Initialize price storage for each token
        # for token, group in data.groupby('token'):
        #     token_prices[token] = []
        #     for _, row in group.iterrows():
        #         token_prices[token].append(row['last_traded_price'])
        #         decide_trade(token, token_prices[token], row['exchange_timestamp'])
        for _, row in data.iterrows():
            token = row['token']
            #  Debugging: Print the last processed timestamp
            print(f"Last processed timestamp: {row['exchange_timestamp']}")
            
            if token not in token_prices:
                token_prices[token] = []

            token_prices[token].append(row['last_traded_price'])
            decide_trade(token, token_prices[token], row['exchange_timestamp'])

    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found at the path: {csv_filepath}")
    except pd.errors.ParserError as e:
        raise ValueError(f"Error parsing CSV file: {e}")
    except Exception as e:
        raise RuntimeError(f"An error occurred while processing the CSV file: {e}")

def main():
    csv_file_path = r"C:\Users\LENOVO\Downloads\20250210-090040.csv"
    read_csv_and_trade(csv_file_path)

if __name__ == "__main__":
    main()
