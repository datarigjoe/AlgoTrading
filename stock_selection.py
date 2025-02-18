# import pandas as pd
# from datetime import datetime, timedelta

# # Set up connection and API details
# conn = http.client.HTTPSConnection("apiconnect.angelbroking.com")

# # Nifty 50 symbol tokens and corresponding company names
# token_name_dict = {
#     694: 'CIPLA',
#     16675: 'BAJAJFINSV',
#     547: 'BRITANNIA',
#     25: 'ADANIENT',
#     20374: 'COALINDIA',
#     881: 'DRREDDY',
#     11536: 'TCS',
#     1660: 'ITC',
#     5900: 'AXISBANK',
#     317: 'BAJFINANCE',
#     3506: 'TITAN',
#     3045: 'SBIN',
#     4963: 'ICICIBANK',
#     3787: 'WIPRO',
#     1922: 'KOTAKBANK',
#     1348: 'HEROMOTOCO',
#     1333: 'HDFCBANK',
#     3456: 'TATAMOTORS',
#     3499: 'TATASTEEL',
#     5097: 'ZOMATO'
# }

# # Convert tokens to strings for API use
# symbol_tokens = list(map(str, token_name_dict.keys()))

# obj = SmartConnect('4GznkDiG')

# # Generate session using the API key and TOTP
# data = obj.generateSession('R103352', 7020, TOTP('RV62S7GJBGHGWKRAYSQ6SRTPVM').now())

# headers = {
#     'X-PrivateKey': '4GznkDiG',
#     'Accept': 'application/json',
#     'X-SourceID': 'WEB',
#     'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
#     'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
#     'X-MACAddress': 'MAC_ADDRESS',
#     'X-UserType': 'USER',
#     'Authorization': data["data"]["jwtToken"],
#     'Content-Type': 'application/json'
# }

# # Calculate dates for previous 2 or 3 days dynamically
# to_date = datetime.now()
# from_date = to_date - timedelta(days=3)  # For last 3 days data

# # Format dates as strings for API request
# from_date_str = from_date.strftime("%Y-%m-%d %H:%M")
# to_date_str = to_date.strftime("%Y-%m-%d %H:%M")

# # Function to calculate momentum for each stock
# def calculate_momentum(data):
#     data['Price Change'] = data['Close'].pct_change() * 100
#     momentum = data['Price Change'].sum()  # Sum of price changes for momentum calculation
#     return momentum

# # Function to calculate volatility based on ATR (Average True Range)
# def calculate_atr(data, period=14):
#     data['High-Low'] = data['High'] - data['Low']
#     data['High-Close'] = abs(data['High'] - data['Close'].shift(1))
#     data['Low-Close'] = abs(data['Low'] - data['Close'].shift(1))
#     data['True Range'] = data[['High-Low', 'High-Close', 'Low-Close']].max(axis=1)
#     atr = data['True Range'].rolling(window=period).mean()
#     return atr

# # Function to calculate liquidity based on average volume
# def calculate_liquidity(data):
#     liquidity = data['Volume'].mean()  # Average volume for liquidity
#     return liquidity

# # Store momentum scores, ATR values, and liquidity for each stock
# stock_scores = {}

# # Define the column names based on typical stock data structure
# column_names = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']

# # Analyze momentum, ATR, and liquidity for each stock
# for symbol_token in symbol_tokens:
#     payload = {
#         "exchange": "NSE",
#         "symboltoken": symbol_token,
#         "interval": "FIVE_MINUTE",  # Set interval to 5 minutes
#         "fromdate": from_date_str,
#         "todate": to_date_str
#     }

#     while True:
#         try:
#             # Send POST request to fetch historical data
#             conn.request("POST", "/rest/secure/angelbroking/historical/v1/getCandleData", json.dumps(payload), headers)
#             res = conn.getresponse()
#             response_data = res.read().decode("utf-8")
#             json_data = json.loads(response_data)

#             # Print the raw response data to check its structure
#             print(json_data)  # Debugging line to inspect response data

#             # Check if the data key is available in the response
#             if 'data' not in json_data:
#                 print(f"No data found for symbol token {symbol_token}.")
#                 break

#             # Prepare the data for analysis
#             data = pd.DataFrame(json_data['data'])

#             # Check if the data needs columns
#             if data.empty:
#                 print(f"No data available for symbol {symbol_token}.")
#                 break

#             # Assign column names manually if missing
#             data.columns = column_names

#             # Check if timestamp column exists, otherwise create it
#             if 'Timestamp' not in data.columns:
#                 print(f"Timestamp column is missing for {symbol_token}.")
#                 break

#             data.set_index('Timestamp', inplace=True)

#             # Calculate momentum for this stock
#             momentum = calculate_momentum(data)

#             # Calculate ATR for this stock
#             atr = calculate_atr(data)

#             # Calculate liquidity for this stock
#             liquidity = calculate_liquidity(data)

#             # Store all calculated values
#             stock_scores[symbol_token] = {
#                 'momentum': momentum,
#                 'atr': atr.iloc[-1],  # Use the latest ATR value
#                 'liquidity': liquidity
#             }

#             print(f"Token: {symbol_token} - Momentum: {momentum} - ATR: {atr.iloc[-1]} - Liquidity: {liquidity}")
#             print("------------------------------------------")
#             break
#         except Exception as e:
#             print(f"Exception: {e}")
#             print("Retrying after 3 seconds...")  # Delay to 3 seconds in case of failure
#             time.sleep(3)

# # After fetching the data for all stocks, sort by momentum, ATR, and liquidity
# sorted_stocks = sorted(stock_scores.items(), key=lambda x: (x[1]['momentum'], x[1]['atr'], x[1]['liquidity']), reverse=True)

# # Select top 5 stocks based on momentum, ATR, and liquidity
# top_5_stocks = sorted_stocks[:5]

# # Print the top 5 stocks with their company names
# print("Top 5 stocks based on momentum, ATR, and liquidity:")
# for stock in top_5_stocks:
#     token = int(stock[0])  # Convert token to integer to match dictionary keys
#     company_name = token_name_dict.get(token, "Unknown")
#     print(f"Company: {company_name}, Token: {stock[0]}, Momentum: {stock[1]['momentum']}, ATR: {stock[1]['atr']}, Liquidity: {stock[1]['liquidity']}")

# # Close the connection after data fetching is completed
# conn.close()
import http.client
from SmartApi import SmartConnect
from pyotp import TOTP
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set up connection and API details
conn = http.client.HTTPSConnection("apiconnect.angelbroking.com")

# Nifty 50 symbol tokens and corresponding company names
# Nifty 50 symbol tokens and corresponding company names
token_name_dict = {
    11532: 'ULTRACEMCO',
    10604: 'BHARTIARTL',
    11536: 'TCS',
    11630: 'NTPC',
    11723: 'JSWSTEEL',
    10999: 'MARUTI',
    11483: 'LT',
    1232: 'GRASIM',
    1363: 'HINDALCO',
    1394: 'HINDUNILVR',
    1660: 'ITC',
    16669: 'BAJAJ-AUTO',
    157: 'APOLLOHOSP',
    20374: 'COALINDIA',
    1964: 'TRENT',
    1594: 'INFY',
    16675: 'BAJAJFINSV',
    21808: 'SBILIFE',
    2475: 'ONGC',
    1922: 'KOTAKBANK',
    1333: 'HDFCBANK',
    13538: 'TECHM',
    3499: 'TATASTEEL',
    15083: 'ADANIPORTS',
    467: 'HDFCLIFE',
    17963: 'NESTLEIND',
    3456: 'TATAMOTORS',
    910: 'EICHERMOT',
    2031: 'M&M',
    14977: 'POWERGRID',
    881: 'DRREDDY',
    5900: 'AXISBANK',
    1348: 'HEROMOTOCO',
    236: 'ASIANPAINT',
    317: 'BAJFINANCE',
    3351: 'SUNPHARMA',
    3432: 'TATACONSUM',
    25: 'ADANIENT',
    694: 'CIPLA',
    2885: 'RELIANCE',
    383: 'BEL',
    4963: 'ICICIBANK',
    526: 'BPCL',
    547: 'BRITANNIA',
    3787: 'WIPRO',
    4306: 'SHRIRAMFIN',
    5258: 'INDUSINDBK',
    7229: 'HCLTECH',
    3045: 'SBIN',
    3506: 'TITAN'
}

# Convert tokens to strings for API use
symbol_tokens = list(map(str, token_name_dict.keys()))

obj = SmartConnect('4GznkDiG')

# Generate session using the API key and TOTP
data = obj.generateSession('R103352', 7020, TOTP('RV62S7GJBGHGWKRAYSQ6SRTPVM').now())

headers = {
    'X-PrivateKey': '4GznkDiG',
    'Accept': 'application/json',
    'X-SourceID': 'WEB',
    'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
    'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
    'X-MACAddress': 'MAC_ADDRESS',
    'X-UserType': 'USER',
    'Authorization': data["data"]["jwtToken"],
    'Content-Type': 'application/json'
}

# Calculate dates for previous 2 or 3 days dynamically
to_date = datetime.now()
from_date = to_date - timedelta(days=3)  # For last 3 days data

# Format dates as strings for API request
from_date_str = from_date.strftime("%Y-%m-%d %H:%M")
to_date_str = to_date.strftime("%Y-%m-%d %H:%M")

# Function to calculate momentum for each stock
def calculate_momentum(data):
    data['Price Change'] = data['Close'].pct_change() * 100
    momentum = data['Price Change'].sum()  # Sum of price changes for momentum calculation
    return momentum

# Function to calculate volatility based on ATR (Average True Range)
def calculate_atr(data, period=14):
    data['High-Low'] = data['High'] - data['Low']
    data['High-Close'] = abs(data['High'] - data['Close'].shift(1))
    data['Low-Close'] = abs(data['Low'] - data['Close'].shift(1))
    data['True Range'] = data[['High-Low', 'High-Close', 'Low-Close']].max(axis=1)
    atr = data['True Range'].rolling(window=period).mean()
    return atr

# Function to calculate liquidity based on average volume
def calculate_liquidity(data):
    liquidity = data['Volume'].mean()  # Average volume for liquidity
    return liquidity

# Function to calculate Bollinger Bands
def calculate_bollinger_bands(data, period=20):
    data['SMA'] = data['Close'].rolling(window=period).mean()
    data['STD'] = data['Close'].rolling(window=period).std()
    data['Upper Band'] = data['SMA'] + (2 * data['STD'])
    data['Lower Band'] = data['SMA'] - (2 * data['STD'])
    return data

# Store momentum scores, ATR values, liquidity, and Bollinger Band widths for each stock
stock_scores = {}

# Define the column names based on typical stock data structure
column_names = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']

# Analyze momentum, ATR, liquidity, and Bollinger Bands for each stock
for symbol_token in symbol_tokens:
    payload = {
        "exchange": "NSE",
        "symboltoken": symbol_token,
        "interval": "FIVE_MINUTE",  # Set interval to 5 minutes
        "fromdate": from_date_str,
        "todate": to_date_str
    }

    while True:
        try:
            # Send POST request to fetch historical data
            conn.request("POST", "/rest/secure/angelbroking/historical/v1/getCandleData", json.dumps(payload), headers)
            res = conn.getresponse()
            response_data = res.read().decode("utf-8")
            json_data = json.loads(response_data)

            # Print the raw response data to check its structure
            print(json_data)  # Debugging line to inspect response data

            # Check if the data key is available in the response
            if 'data' not in json_data:
                print(f"No data found for symbol token {symbol_token}.")
                break

            # Prepare the data for analysis
            data = pd.DataFrame(json_data['data'])

            # Check if the data needs columns
            if data.empty:
                print(f"No data available for symbol {symbol_token}.")
                break

            # Assign column names manually if missing
            data.columns = column_names

            # Check if timestamp column exists, otherwise create it
            if 'Timestamp' not in data.columns:
                print(f"Timestamp column is missing for {symbol_token}.")
                break

            data.set_index('Timestamp', inplace=True)

            # Calculate momentum for this stock
            momentum = calculate_momentum(data)

            # Calculate ATR for this stock
            atr = calculate_atr(data)

            # Calculate liquidity for this stock
            liquidity = calculate_liquidity(data)

            # Calculate Bollinger Bands for this stock
            data = calculate_bollinger_bands(data)

            # Calculate Bollinger Band width (upper - lower)
            bollinger_band_width = (data['Upper Band'] - data['Lower Band']).mean()

            # Store all calculated values
            stock_scores[symbol_token] = {
                'momentum': momentum,
                'atr': atr.iloc[-1],  # Use the latest ATR value
                'liquidity': liquidity,
                'bollinger_band_width': bollinger_band_width
            }

            print(f"Token: {symbol_token} - Momentum: {momentum} - ATR: {atr.iloc[-1]} - Liquidity: {liquidity} - Bollinger Band Width: {bollinger_band_width}")
            print("------------------------------------------")
            break
        except Exception as e:
            print(f"Exception: {e}")
            print("Retrying after 3 seconds...")  # Delay to 3 seconds in case of failure
            time.sleep(3)

# After fetching the data for all stocks, sort by momentum, ATR, liquidity, and Bollinger Band width
sorted_stocks = sorted(stock_scores.items(), key=lambda x: (x[1]['momentum'], x[1]['atr'], x[1]['liquidity'], x[1]['bollinger_band_width']), reverse=True)

# Select top 5 stocks based on momentum, ATR, liquidity, and Bollinger Band width
top_5_stocks = sorted_stocks[:5]

# Print the top 5 stocks with their company names
print("Top 5 stocks based on momentum, ATR, liquidity, and Bollinger Band width:")
for stock in top_5_stocks:
    token = int(stock[0])  # Convert token to integer to match dictionary keys
    company_name = token_name_dict.get(token, "Unknown")
    print(f"Company: {company_name}, Token: {stock[0]}, Momentum: {stock[1]['momentum']}, ATR: {stock[1]['atr']}, Liquidity: {stock[1]['liquidity']}, Bollinger Band Width: {stock[1]['bollinger_band_width']}")

# Close the connection after data fetching is completed
conn.close()
