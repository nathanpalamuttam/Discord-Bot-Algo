import discord
import asyncio
import random
import asyncio
import time
from datetime import datetime, timedelta, timezone
import pytz
import requests
import alpaca_trade_api as tradeapi
import json
import os
import discord
import asyncio
import random
from datetime import datetime, time
import os
from dotenv import load_dotenv

load_dotenv()  # load from .env in current dir

USER_TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets"  # Change to live URL if trading real money
api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL)
account = api.get_account()
# print(f"Cash Balance: ${account.cash}")
# print(f"Buying Power: ${account.buying_power}")
# print(f"Equity: ${account.equity}")
# print(f"Initial Margin: ${account.initial_margin}")
# print(f"Maintenance Margin: ${account.maintenance_margin}")
# print(f"Portfolio Value: ${account.portfolio_value}")
# print(f"Currency: {account.currency}")

# try:
#     orders = api.list_orders(status='all', limit=10)  # Get last 10 orders
#     print("\n=== 📝 Recent Orders ===")
#     for order in orders:
#         print(f"Symbol: {order.symbol}")
#         print(f"Side: {order.side}")
#         print(f"Type: {order.type}")
#         print(f"Qty: {order.qty}")
#         print(f"Limit Price: ${float(order.limit_price) if order.limit_price else 'N/A'}")  # Added limit price
#         print(f"Filled Price: ${float(order.filled_avg_price) if order.filled_avg_price else 'N/A'}")  # Added filled price
#         print(f"Status: {order.status}")
#         print(f"Submitted At: {order.submitted_at}")
#         if order.filled_at:
#             print(f"Filled At: {order.filled_at}")
#         print("------------------------")
# except Exception as e:
#     print(f"❌ Error fetching orders: {e}")

# File to store trades
TRADES_FILE = 'current_trades.json'

# Load existing trades from file
try:
    with open(TRADES_FILE, 'r') as f:
        content = f.read().strip()
        if content:  # Check if file has content
            try:
                currTrades = json.loads(content)  # Use json.loads() on the string instead of json.load() on the file
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in file: {e}")
                currTrades = {}
                if os.path.exists(TRADES_FILE):
                    os.rename(TRADES_FILE, f"{TRADES_FILE}.backup")
                with open(TRADES_FILE, 'w') as f:
                    json.dump({}, f)
        else:
            currTrades = {}
except FileNotFoundError:
    currTrades = {}
    with open(TRADES_FILE, 'w') as f:
        json.dump({}, f)

# Helper function to save trades
def save_trades():
    with open(TRADES_FILE, 'w') as f:
        json.dump(currTrades, f)

def get_option(symb, limitPrice, strike, exp, type, buy = True):
    limitPrice = round(limitPrice, 2)
    if not buy:
        try:
            url = f"{BASE_URL}/v2/positions"
            headers = {
                "accept": "application/json",
                "APCA-API-KEY-ID": API_KEY,
                "APCA-API-SECRET-KEY": SECRET_KEY
            }
            response = requests.get(url, headers=headers)
            positions = response.json()
            symbol_positions_tmp = [pos for pos in positions if pos['symbol'] == currTrades[symb]["symbId"]]
            symbol_positions = [pos for pos in positions if pos['symbol'].startswith(symb)]
            if symbol_positions_tmp == symbol_positions:
                print("works")
            if not symbol_positions:
                print(f"❌ No positions found for {symb}. Cancelling sell order.")
                return False
            url = f"{BASE_URL}/v2/orders"
            payload = {
                "symbol": symb,
                "qty": 1,
                "side": "sell",
                "type": "limit",
                "limit_price": limitPrice,
                "time_in_force": "day"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200 or response.status_code == 201:
                print(f"✅ Sell order placed successfully for {symb}")
                if symb in currTrades:
                    del currTrades[symb]
                    save_trades()
                return True
            else:
                print(f"❌ Error placing sell order: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking positions or placing sell order: {e}")
            return False
    
    url = f"{BASE_URL}/v2/options/contracts"
    params = {
        'underlying_symbols': symb,
        'expiration_date': exp, 
    }
    headers = {
        'accept': 'application/json',
        'APCA-API-KEY-ID': API_KEY,
        'APCA-API-SECRET-KEY': SECRET_KEY
    }
    
    # Get the option symbol ID
    symbId = None
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        contracts = response.json().get("option_contracts", [])
        filtered_contracts = [
            c for c in contracts if c.get("strike_price") == strike and c.get("type") == type
        ]
        print(filtered_contracts)
        if filtered_contracts:
            symbId = filtered_contracts[0].get("symbol")
        else:
            print("No matching contracts found.")
            return False
    print("CHECKING OPTION IDS")
    
    # First check existing positions
    try:
        url = f"{BASE_URL}/v2/positions"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            positions = response.json()
            for position in positions:
                if position['symbol'] == symbId:
                    print(f"⚠️ Already have a position in {symbId}")
                    return False
    except Exception as e:
        print(f"❌ Error checking positions: {e}")
    
    # Then check pending orders
    try:
        url = f"{BASE_URL}/v2/orders"
        response = requests.get(url, headers=headers)
        print(response)
        if response.status_code == 200:
            existing_orders = response.json()
            for order in existing_orders:
                print(order['symbol'])
                if order['symbol'] == symbId:
                    print(f"⚠️ Found existing order for {symbId}:")
                    print(f"Status: {order['status']}")
                    print(f"Side: {order['side']}")
                    if order['status'] in ['new', 'filled', 'partially_filled']:
                        print(f"⚠️ Active order already exists. Skipping duplicate order.")
                        return False
    except Exception as e:
        print(f"❌ Error checking existing orders: {e}")
        return False

    #CREATE ORDER
    url = "https://paper-api.alpaca.markets/v2/orders"
    payload = {
        "type": "limit",
        "limit_price": limitPrice,
        "time_in_force": "day",
        "symbol" : symbId,
        "qty": 1,
        "side": "buy" if buy else "sell"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print(response.json())
    if response.status_code == 200 or response.status_code == 201:
        print(f"✅ Order placed successfully for {symb}")
        if buy:
            currTrades[symb] = {"symb": symb, "symbId": symbId, "limitPrice": limitPrice, "strike": strike, "exp": exp, "type": type, "buy": buy}
        else:
            print("deleting")
            del currTrades[symb]
        save_trades()
        return True
    else:
        print(f"❌ Error placing order: {response.text}")
        return False

USER_TOKEN = os.environ.get("DISCORD_TOKEN")
TARGET_CHANNEL_ID = 1277335126493233234
TARGET_CHANNEL_ID_2 = 1282469793177276564


class SelfBot(discord.Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_message_map = {}  # Hashmap to store last two message IDs for each channel
        self.channel_ids = [TARGET_CHANNEL_ID, TARGET_CHANNEL_ID_2]
        self.channel_id_map = {"Ravi": TARGET_CHANNEL_ID_2, "Panda": TARGET_CHANNEL_ID}
        self.channel_name = {TARGET_CHANNEL_ID_2: "Ravi", TARGET_CHANNEL_ID: "Panda"}

    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")
        await self.wait_until_market_open()  # Changed to await instead of create_task

    async def wait_until_market_open(self):
        while True:
            now = datetime.now()
            market_open = datetime.combine(now.date(), time(9, 30))  # 9:30 AM today
            market_close = datetime.combine(now.date(), time(17, 0))  # 5:00 PM today

            if market_open <= now < market_close:
                print("✅ Market is open. Starting message monitoring...")
                await self.check_mentions()
                
            next_open = market_open + timedelta(days=1) if now >= market_close else market_open
            sleep_duration = (next_open - now).total_seconds()
            print(f"⏳ Market closed. Sleeping for {sleep_duration // 3600:.0f} hours and {(sleep_duration % 3600) // 60:.0f} minutes.")
            
            await asyncio.sleep(sleep_duration)  # Sleep once until market opens

    async def check_mentions(self):
        while True:
            for channel_id in self.channel_ids:
                try:
                    channel = await self.fetch_channel(channel_id)
                    messages = []
                    async for message in channel.history(limit=2):
                        messages.append(message)
                    
                    if channel_id not in self.last_message_map:
                        self.last_message_map[channel_id] = []
                        
                    new_message_found = False
                    for message in reversed(messages):
                        if message.id not in self.last_message_map[channel_id]:
                            new_message_found = True
                            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                            print(f"\n🔔 New message found at {timestamp} in channel {self.channel_name[channel_id]}")
                            break
                    
                    if not new_message_found:
                        continue
                        
                    new_message_ids = []
                    processed_ids = set()  # Track which messages we've processed
                    
                    for message in reversed(messages):
                        new_message_ids.append(message.id)
                        
                        # Skip if we've already processed this message
                        if message.id in processed_ids or message.id in self.last_message_map[channel_id]:
                            continue
                            
                        
                        
                        if channel_id == self.channel_id_map["Ravi"]:
                            print("\n" + "="*50)
                            print("🔵 PROCESSING RAVI'S MESSAGE 🔵")
                            print("="*50)
                            parse_Ravi(message)
                            print("="*50 + "\n")
                        elif channel_id == self.channel_id_map["Panda"]:
                            print("\n" + "="*50)
                            print("🟢 PROCESSING PANDA'S MESSAGE 🟢")
                            print("="*50)
                            parsePanda(message)
                            print("="*50 + "\n")
                            
                        processed_ids.add(message.id)  # Mark as processed
                        
                    self.last_message_map[channel_id] = new_message_ids
                    
                except Exception as e:
                    print(f"❌ Error fetching messages from channel {channel_id}: {e}")
                    print(f"Full error details: {str(e)}")

            await asyncio.sleep(random.randint(30, 60))

def parse_Ravi(message):
    symbol = None
    strike = None
    exp = None
    limitPrice = None
    putCall = None
    message = message.clean_content
    print(message)
    message = message.replace('*', '')
    lines = message.split('\n')
    for line in lines:
        if "TRADE" in line:
            if "CLOSED" in line:
                buy = False
            else:
                buy = True
        if "Ticker:" in line:
            symbol = line.split(':')[1].strip().split()[0]
            if "(Call)" in line:
                putCall = "call"
            elif "(Put)" in line:
                putCall = "put"
            print(f"📈 Ticker Symbol: {symbol}")
        elif "Strike Price:" in line:
            strike = line.split('$')[1].strip()
            print(f"🎯 Strike Price: ${strike}")
        elif "Expiry:" in line:
            date_parts = line.split(':')[1].strip().split('/')
            exp = f"{date_parts[2]}-{date_parts[0].zfill(2)}-{date_parts[1].zfill(2)}"
            print(f"📅 Expiration Date: {exp}")
        elif "Avg Entry:" in line or "Exit Price" in line:
            limitPrice = float(line.split('$')[1].strip())
            print(f"💰 Limit Price: ${limitPrice}")
    print(f"📊 Option Type: {putCall}")
    
    
    if None in [symbol, strike, exp, limitPrice, putCall]:
        print("❌ Missing required parameters:")
        print(f"Symbol: {symbol}")
        print(f"Strike: {strike}")
        print(f"Expiration: {exp}")
        print(f"Limit Price: {limitPrice}")
        print(f"Type: {putCall}")
        return
    
    print("\n🔄 Executing get_option with parameters:")
    print(f"Symbol: {symbol}")
    print(f"Limit Price: ${limitPrice + 0.1}")
    print(f"Strike: ${strike}")
    print(f"Expiration: {exp}")
    print(f"Type: {putCall}")
    print(f"Buy: True")

    get_option(
        symb=symbol,
        limitPrice=limitPrice,
        strike=strike,
        exp=exp,
        type=putCall,
        buy=buy
    )
    return

def parsePanda(message):
    symbol = None
    strike = None
    exp_date = None
    limitPrice = None
    putCall = None
    grade = None
    buy = True
    color_value = message.embeds[0].color.value
    if color_value == 3066993:
        print("Green embed!")
        buy = True
    elif color_value == 15158332:
        print("Red embed!")
        buy = False
    else:
        print(f"Other color: {color_value}")

    message = message.embeds[0].title
    print(f"Original message length: {len(message)}")
    
    # Remove all asterisks and dashes
    message = message.replace("*", "").replace("-", "").strip()
    print(f"Cleaned message: {message}")
    
    parts = message.split()
    
    # Parse all parts first
    for i in parts:
        try:
            # Check if it's a valid stock symbol
            url = f"{BASE_URL}/v2/assets/{i}"
            headers = {
                "accept": "application/json",
                "APCA-API-KEY-ID": API_KEY,
                "APCA-API-SECRET-KEY": SECRET_KEY
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                symbol = i
                print(f"📈 Found valid symbol: {symbol}")
                continue
                
            # Check if it's a price (starts with $)
            if '$' in i:
                try:
                    limitPrice = round(float(i.replace('$', '')), 2)
                    print(f"💰 Found price: ${limitPrice}")
                    continue
                except ValueError:
                    pass
                    
            # Check if it's a date (contains /)
            if '/' in i:
                try:
                    date_parts = i.split('/')
                    if len(date_parts) == 2:
                        month, day = date_parts
                        year = "2025"  # Assuming current year
                        exp_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        print(f"📅 Found date: {exp_date}")
                        continue
                except ValueError:
                    pass
                    
            # Check if it's a strike price + option type (ends in C or P)
            if i[-1] in ['C', 'P']:
                try:
                    strike = i[:-1]  # Everything except last character
                    putCall = "call" if i[-1] == 'C' else "put"
                    print(f"🎯 Found strike: ${strike}")
                    print(f"📊 Found option type: {putCall}")
                    continue
                except ValueError:
                    pass
                    
            # Check for grade
            if "GRADE" in i:
                grade_index = i.find("GRADE")
                grade = i[grade_index - 2]  # Get the letter before "GRADE"
                if grade in ['A', 'B']:
                    print(f"📝 Found grade: {grade}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error parsing part {i}: {str(e)}")
            continue
    # If no expiration date found, find the closest valid one
    if exp_date is None and symbol is not None:
        try:
            # Get available expiration dates for this symbol
            url = f"{BASE_URL}/v2/options/contracts"
            params = {
                'underlying_symbols': symbol
            }
            headers = {
                'accept': 'application/json',
                'APCA-API-KEY-ID': API_KEY,
                'APCA-API-SECRET-KEY': SECRET_KEY
            }
            
            response = requests.get(url, headers=headers, params=params)
            print(response)
            if response.status_code == 200:
                contracts = response.json().get("option_contracts", [])
                if contracts:
                    # Get all unique expiration dates
                    exp_dates = sorted(set(c.get("expiration_date") for c in contracts if c.get("expiration_date")))
                    
                    # Find the closest date that's not in the past
                    today = datetime.now().date()
                    future_dates = [d for d in exp_dates if datetime.strptime(d, "%Y-%m-%d").date() >= today]
                    
                    if future_dates:
                        exp_date = future_dates[0]  # Get the closest future date
                        print(f"📅 Found closest expiration date: {exp_date}")
                    else:
                        print("❌ No valid expiration dates found")
                        return False
        except Exception as e:
            print(f"❌ Error finding expiration date: {e}")
            return False
    
    # Validate all required fields
    if None in [symbol, strike, exp_date, limitPrice, putCall]:
        print("❌ Missing required parameters:")
        print(f"Symbol: {symbol}")
        print(f"Strike: {strike}")
        print(f"Expiration: {exp_date}")
        print(f"Limit Price: {limitPrice}")
        print(f"Type: {putCall}")
        return False
        
    print("\n🔄 Executing get_option with parameters:")
    print(f"Symbol: {symbol}")
    print(f"Strike: ${strike}")
    print(f"Expiration: {exp_date}")
    print(f"Limit Price: ${limitPrice}")
    print(f"Type: {putCall}")
    if grade:
        print(f"Grade: {grade}")
    
    get_option(
        symb=symbol,
        limitPrice=limitPrice+.1,
        strike=strike,
        exp=exp_date,
        type=putCall,
        buy=buy
    )
    return True

client = SelfBot()
client.run(USER_TOKEN)



 # tList = "Securing 1/4 of SPY at .2"
                    # tList = tList.split()
                    # if tList[0] == "Securing" and len(tList) > 3:
                    #         symbol = tList[3]
                    #         print(currTrades)
                    #         currentTrade = currTrades[tList[3]]
                    #         print(currentTrade)
                    #         get_option(symbol, currentTrade["limitPrice"], currentTrade["strike"], currentTrade["exp"], currentTrade["type"], buy = False)
                    #           # Stock symbId
                    #         continue
                    # tList = "SPY 02/11 600.0C at .01"
                    # tList = tList.split()
                    # stock_symbol = tList[0]  
                    # putCall = "call" if tList[2][-1] == "C" else "put"   # 'C' for Call or 'P' for Put
                    # # Convert strike price to integer string (e.g., "695.0C" -> "695")
                    # strike = str(int(float(tList[2][:-1])))
                    # input_date = tList[1]
                    # prem = float(tList[-1])
                    # expiration_date = datetime.strptime(f"{input_date}/2025", "%m/%d/%Y")
                    # formatted_date = expiration_date.strftime("%Y-%m-%d")
                    # if not tList:
                    #     print("❌ Message format error: Empty title.")
                    #     continue
                    
                    # get_option(symb = stock_symbol, limitPrice= prem + .1, strike = strike, exp = formatted_date, type = putCall)


