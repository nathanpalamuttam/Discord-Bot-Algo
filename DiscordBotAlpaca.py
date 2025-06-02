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
from write_pipe import write_signal_to_pipe
from dotenv import load_dotenv

load_dotenv()  # load from .env in current dir

USER_TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("API_KEY_DISCORD")
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
TARGET_CHANNEL_ID_2 = 1278034308484956211


class SelfBot(discord.Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_message_map = {}
        self.channel_ids = [TARGET_CHANNEL_ID, TARGET_CHANNEL_ID_2]
        self.channel_id_map = {"Orion": TARGET_CHANNEL_ID_2, "Panda": TARGET_CHANNEL_ID}
        self.channel_name = {TARGET_CHANNEL_ID_2: "Orion", TARGET_CHANNEL_ID: "Panda"}

    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")
        await self.wait_until_market_open()

    async def wait_until_market_open(self):
        print("✅ Market is open. Starting message monitoring...")
        await self.check_mentions()
        return
        while True:
            now = datetime.now()
            market_open = datetime.combine(now.date(), time(9, 30))
            market_close = datetime.combine(now.date(), time(17, 0))

            if market_open <= now < market_close:
                print("✅ Market is open. Starting message monitoring...")
                await self.check_mentions()

            next_open = market_open + timedelta(days=1) if now >= market_close else market_open
            sleep_duration = (next_open - now).total_seconds()
            print(f"⏳ Market closed. Sleeping {sleep_duration/3600:.1f} hours")
            await asyncio.sleep(sleep_duration)

    async def check_mentions(self):
        while True:
            #for channel_id in self.channel_ids:
                channel_id = TARGET_CHANNEL_ID_2
                try:
                    channel = await self.fetch_channel(channel_id)
                    messages = [msg async for msg in channel.history(limit=20)]

                    if channel_id not in self.last_message_map:
                        self.last_message_map[channel_id] = []
                    cnt = 0
                    for msg in reversed(messages):
                        
                        if msg.id not in self.last_message_map[channel_id]:
                            print(f"🔔 New message in {self.channel_name[channel_id]}")
                            if channel_id == self.channel_id_map["Orion"]:
                                parse_orion_embed(msg)
                            print(cnt)
                            cnt += 1
                            # elif channel_id == self.channel_id_map["Panda"]:
                            #     parse_panda(msg)

                    self.last_message_map[channel_id] = [m.id for m in messages]

                except Exception as e:
                    print(f"❌ Error reading channel {channel_id}: {e}")
            #await asyncio.sleep(random.randint(30, 60))
def parse_orion_embed(message):
    try:
        embed = message.embeds[0]
        title = embed.title.lower()

        # Extract all fields into a dictionary
        fields = {field.name.strip(): field.value.strip() for field in embed.fields}

        # NEW POSITION
        if "new position" in title:
            ticker = fields.get("Ticker")
            strike = fields.get("Strike Price", "").replace('$', '')
            exp = fields.get("Expiration Date")
            option_type = fields.get("Option Type", "").lower()
            price = fields.get("Contract Price", "").replace('$', '')
            contracts = fields.get("Contracts", "1")

            print("📥 New Position")
            write_signal_to_pipe({
                "symbol": ticker,
                "strike": strike,
                "expiration": exp,
                "limitPrice": float(price),
                "type": option_type,
                "buy": True
            })

        # POSITION CLOSED
        elif "position closed" in title:
            ticker = fields.get("Ticker")
            strike = fields.get("Strike Price", "").replace('$', '')
            exp = fields.get("Expiration Date")
            option_type = fields.get("Option Type", "").lower()
            price = fields.get("Sold At", "").replace('$', '')
            contracts = fields.get("Contracts", "1")

            print("💔 Position Closed")
            write_signal_to_pipe({
                "symbol": ticker,
                "strike": strike,
                "expiration": exp,
                "limitPrice": float(price),
                "type": option_type,
                "buy": False
            })

        # CONTRACT CHANGE
        elif "contract change" in title:
            ticker = fields.get("Ticker")
            strike = fields.get("Strike Price", "").replace('$', '')
            exp = fields.get("Expiration Date")
            option_type = fields.get("Option Type", "").lower()
            price = fields.get("Contract Price", "").replace('$', '')
            change = fields.get("Change", "").replace("+", "").strip()

            print("\n📊 Parsed Orion Contract Change:")
            print(f"🔹 Ticker: {ticker}")
            print(f"🔹 Strike Price: {strike}")
            print(f"🔹 Expiration Date: {exp}")
            print(f"🔹 Option Type: {option_type}")
            print(f"🔹 Contract Price: {price}")
            print(f"🔹 Contracts Added: {change}")


            print("🔄 Position Update: Added Contracts")
            write_signal_to_pipe({
                "symbol": ticker,
                "strike": strike,
                "expiration": exp,
                "limitPrice": float(price),
                "type": option_type,
                "buy": True,         # Still a buy since it's an add
                "size_add": int(change)
            })
            print("DONE")

        else:
            print("⚠️ Unrecognized Orion embed")
        return
    except Exception as e:
        print(f"❌ Error parsing Orion embed: {e}")


def parse_ravi(msg):
    content = msg.clean_content.replace('*', '')
    print(content)
    symbol, strike, exp, limitPrice, optionType, buy = [None] * 6
    for line in content.split('\n'):
        if "Ticker:" in line:
            symbol = line.split(":")[1].strip().split()[0]
            if "(Call)" in line: optionType = "call"
            elif "(Put)" in line: optionType = "put"
        if "Strike Price:" in line:
            strike = line.split('$')[1].strip()
        if "Expiry:" in line:
            mm, dd, yyyy = line.split(":")[1].strip().split('/')
            exp = f"{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}"
        if "Avg Entry:" in line or "Exit Price:" in line:
            limitPrice = float(line.split('$')[1].strip())
        if "TRADE CLOSED" in line:
            buy = False
        elif "TRADE" in line:
            buy = True

    if None in [symbol, strike, exp, limitPrice, optionType, buy]:
        print("❌ Missing data")
        return

    write_signal_to_pipe({
        "symbol": symbol,
        "strike": strike,
        "expiration": exp,
        "limitPrice": round(limitPrice + 0.1, 2),
        "type": optionType,
        "buy": buy
    })

def parse_panda(msg):
    try:
        data = msg.embeds[0]
        text = data.title.replace("*", "").replace("-", "")
        parts = text.split()
        color = data.color.value

        symbol = strike = exp = limitPrice = optionType = None
        buy = color == 3066993

        for token in parts:
            if '/' in token:
                month, day = token.split('/')
                exp = f"2025-{month.zfill(2)}-{day.zfill(2)}"
            elif token.endswith('C') or token.endswith('P'):
                strike = token[:-1]
                optionType = "call" if token.endswith('C') else "put"
            elif token.startswith('$'):
                limitPrice = round(float(token.strip('$')), 2)
            else:
                # Check if valid symbol
                if not symbol:
                    symbol = token

        if None in [symbol, strike, exp, limitPrice, optionType]:
            print("❌ Missing Panda fields")
            return

        write_signal_to_pipe({
            "symbol": symbol,
            "strike": strike,
            "expiration": exp,
            "limitPrice": round(limitPrice + 0.1, 2),
            "type": optionType,
            "buy": buy
        })

    except Exception as e:
        print(f"❌ Panda parsing failed: {e}")

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


