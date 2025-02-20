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

# Generate CSV File Name
csv_filename = f"order_book_{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"

def write_to_csv(orders):
    """Writes order book data to a CSV file, dynamically adjusting field names."""
    if orders:
        # Extract all possible field names dynamically
        fieldnames = set()
        for order in orders:
            fieldnames.update(order.keys())  # Collect all field names dynamically
        
        # Convert set to a sorted list for consistency
        fieldnames = sorted(fieldnames)

        # Write data to CSV
        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(orders)
        
        print(f"✅ Order data saved to {csv_filename}")
    else:
        print("⚠️ No orders found to write to CSV.")

# Process API Response
if res.status == 200:
    response_data = json.loads(data.decode("utf-8"))
    
    if 'data' in response_data and response_data['data']:
        orders = response_data['data']
        write_to_csv(orders)
    else:
        print("⚠️ No order data found in API response.")
else:
    print(f"❌ Error fetching data. Status code: {res.status}")

# Close Connection
conn.close()
