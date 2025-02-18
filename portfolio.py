# import http.client
# import json
# from SmartApi import SmartConnect
# from pyotp import TOTP


# conn = http.client.HTTPSConnection("apiconnect.angelbroking.com")
# obj = SmartConnect('4GznkDiG')
# data = obj.generateSession('R103352', 7020, TOTP('RV62S7GJBGHGWKRAYSQ6SRTPVM').now())

# headers = {
#   'Authorization': data["data"]["jwtToken"],
#   'Content-Type': 'application/json',
#   'Accept': 'application/json',
#   'X-UserType': 'USER',
#   'X-SourceID': 'WEB',
#   'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
#   'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
#   'X-MACAddress': 'MAC_ADDRESS',
#   'X-PrivateKey': '4GznkDiG'
# }


# conn.request("GET", "/rest/secure/angelbroking/order/v1/getOrderBook", headers=headers)


# res = conn.getresponse()
# data = res.read()
# # print(data)
# # Check if request was successful (HTTP status code 200)
# if res.status == 200:
    
#     response_data = json.loads(data.decode("utf-8"))
    
#     if 'data' in response_data:
#         orders = response_data['data']

#     for order in orders:
#             variety = order.get('variety', '')
#             ordertype = order.get('ordertype', '')
#             producttype = order.get('producttype', '')
#             duration = order.get('duration', '')
#             price = order.get('price', '')
#             triggerprice = order.get('triggerprice', '')
#             quantity = order.get('quantity', '')
#             stoploss = order.get('stoploss', '')
#             trailingstoploss = order.get('trailingstoploss', '')
#             tradingsymbol = order.get('tradingsymbol', '')
#             transactiontype = order.get('transactiontype', '')
#             exchange = order.get('exchange', '')
#             symboltoken = order.get('symboltoken', '')
#             instrumenttype = order.get('instrumenttype', '')
#             strikeprice = order.get('strikeprice', '')
#             optiontype = order.get('optiontype', '')
#             expirydate = order.get('expirydate', '')
#             lotsize = order.get('lotsize', '')
#             cancelsize = order.get('cancelsize', '')
#             averageprice = order.get('averageprice', '')
#             orderid = order.get('orderid', '')
#             text = order.get('text', '')
#             status = order.get('status', '')
#             orderstatus = order.get('orderstatus', '')
#             updatetime = order.get('updatetime', '')
#             exchtime = order.get('exchtime', '')
            
            
           
# else:
#     print(f"Error fetching data. Status code: {res.status}")

# conn.close()
import http.client
import json
import csv
from datetime import datetime
from SmartApi import SmartConnect
from pyotp import TOTP

# API Credentials
API_KEY = "4GznkDiG"
CLIENT_ID = "R103352"
PIN = 7020
TOTP_SECRET = "RV62S7GJBGHGWKRAYSQ6SRTPVM"

# Initialize API Connection
conn = http.client.HTTPSConnection("apiconnect.angelbroking.com")
obj = SmartConnect(API_KEY)
data = obj.generateSession(CLIENT_ID, PIN, TOTP(TOTP_SECRET).now())

# Request Headers
headers = {
    'Authorization': data["data"]["jwtToken"],
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-UserType': 'USER',
    'X-SourceID': 'WEB',
    'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
    'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
    'X-MACAddress': 'MAC_ADDRESS',
    'X-PrivateKey': API_KEY
}

# Fetch Order Book
conn.request("GET", "/rest/secure/angelbroking/order/v1/getOrderBook", headers=headers)
res = conn.getresponse()
data = res.read()

# CSV File Setup
csv_filename = f"order_book_{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"

def write_to_csv(orders):
    if orders:  # Check if orders is not None or empty
        fieldnames = [
            "variety", "ordertype", "producttype", "duration", "price", "triggerprice", "quantity", "stoploss",
            "trailingstoploss", "tradingsymbol", "transactiontype", "exchange", "symboltoken", "instrumenttype",
            "strikeprice", "optiontype", "expirydate", "lotsize", "averageprice", "orderid", "text",
            "status", "orderstatus", "updatetime", "exchtime"
        ]
        
        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(orders)
        print(f"Order data saved to {csv_filename}")
    else:
        print("No orders to write to CSV.")

# Process Response Data
if res.status == 200:
    response_data = json.loads(data.decode("utf-8"))
    if 'data' in response_data:
        orders = response_data['data']
        if orders:  # Ensure that 'data' contains valid order information
            write_to_csv(orders)
        else:
            print("No order data found in response.")
    else:
        print("No 'data' key found in response.")
else:
    print(f"Error fetching data. Status code: {res.status}")

conn.close()
