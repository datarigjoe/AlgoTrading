# import json
# import http.client

# def place_order(transaction_type, token, price, jwt_token, api_key):
#     """Places a buy or sell order."""
#     conn = http.client.HTTPSConnection("apiconnect.angelbroking.com")
#     payload = {
#         "variety": "NORMAL",
#         "symboltoken": token,
#         "transactiontype": transaction_type,
#         "exchange": "NSE",
#         "ordertype": "MARKET",
#         "producttype": "INTRADAY",
#         "duration": "DAY",
#         "price": str(price),
#         "squareoff": "0",
#         "stoploss": "0",
#         "quantity": "1"
#     }
#     payload_json = json.dumps(payload)
#     headers = {
#         'Authorization': jwt_token,
#         'Content-Type': 'application/json',
#         'Accept': 'application/json',
#         'X-UserType': 'USER',
#         'X-SourceID': 'WEB',
#         'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
#         'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
#         'X-MACAddress': 'MAC_ADDRESS',
#         'X-PrivateKey': api_key
#     }
#     url = "/rest/secure/angelbroking/order/v1/placeOrder"
#     conn.request("POST", url, payload_json, headers)
#     res = conn.getresponse()
#     response_data = res.read()
#     print(response_data.decode("utf-8"))

import json
import http.client

def place_order(transaction_type, token, price, jwt_token, api_key, client_local_ip, client_public_ip, mac_address):
    """
    Places a buy or sell order using Angel One's API.

    Parameters:
    - transaction_type (str): "BUY" or "SELL"
    - token (str): Stock token (e.g., "5900")
    - price (float): Order price
    - jwt_token (str): Authentication token
    - api_key (str): API key
    - client_local_ip (str): Local IP address of the client
    - client_public_ip (str): Public IP address of the client
    - mac_address (str): MAC address of the client

    Returns:
    - dict: API response as a dictionary
    """
    conn = http.client.HTTPSConnection("apiconnect.angelbroking.com")
    payload = {
        "variety": "NORMAL",
        "symboltoken": token,
        "transactiontype": transaction_type,
        "exchange": "NSE",
        "ordertype": "MARKET",
        "producttype": "INTRADAY",
        "duration": "DAY",
        "price": str(price),
        "squareoff": "0",
        "stoploss": "0",
        "quantity": "1"
    }

    headers = {
        'Authorization': jwt_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': client_local_ip,
        'X-ClientPublicIP': client_public_ip,
        'X-MACAddress': mac_address,
        'X-PrivateKey': api_key
    }

    try:
        conn.request("POST", "/rest/secure/angelbroking/order/v1/placeOrder", json.dumps(payload), headers)
        res = conn.getresponse()
        response_data = res.read().decode("utf-8")
        conn.close()

        response_dict = json.loads(response_data)  # Convert JSON response to dictionary
        return response_dict

    except Exception as e:
        print(f"Error placing order: {e}")
        return {"status": "error", "message": str(e)}
