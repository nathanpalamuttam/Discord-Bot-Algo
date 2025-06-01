
import sys
import time
import types
import os
from dotenv import load_dotenv
import os
import discord
import asyncio
import random
import asyncio
import time
from datetime import datetime, timedelta, timezone
import pytz

import robin_stocks.robinhood as r
import pyotp
import robin_stocks.robinhood as r
import json

#
load_dotenv() 
sys.modules['audioop'] = types.ModuleType('audioop')


username = 'natepal04@gmail.com'
password = '^U3KbVfcH2$tb2s0'
print("Attempting to log in...")

# 1. Initial login attempt. 
#    - If your account *requires* 2FA and you pass 'by_sms=True', you’ll get an SMS with a code.
#    - If your account does NOT require 2FA, login should succeed immediately.
login_response = r.login(
    username=username,
    password=password,
    expiresIn=86400,      # Token validity (in seconds)
    scope='internal',     
    by_sms=True,          # Set to True to request code via SMS; False if you prefer email code
    store_session=False   # Set to True to save session in a pickle file
)

print("Login Response (Debug):", json.dumps(login_response, indent=4))

# 2. Check if the response indicates MFA is required
if login_response.get('mfa_required'):
    print("2FA is required. Please enter the code you received (SMS or email).")
    mfa_code = input("Enter the MFA code: ").strip()
    
    # 3. Attempt to log in again, passing the MFA code
    challenge_response = r.login(
        username=username,
        password=password,
        mfa_code=mfa_code,
        expiresIn=86400,
        scope='internal',
        store_session=False
    )
    
    print("Challenge Response (Debug):", json.dumps(challenge_response, indent=4))
    
    if 'access_token' in challenge_response:
        print("✅ Login successful with MFA!")
    else:
        print("❌ Login failed. Please check your MFA code or account settings.")
    
else:
    # No MFA required or the token was granted immediately
    if 'access_token' in login_response:
        print("✅ Login successful (no MFA required).")
    else:
        print("❌ Login failed. Please check your credentials or account settings.")

# import logging

# logging.basicConfig(level=logging.DEBUG)
# try:
#     username = 'natepal04@gmail.com'
#     password = '^U3KbVfcH2$tb2s0'
#     login = r.login(username, password, mfa_code='554246', store_session=False)
#     print("Logged in successfully!")
# except Exception as e:
#     print(f"Error: {e}")
# def login_to_robinhood():
#     username = 'natepal04@gmail.com'
#     password = '^U3KbVfcH2$tb2s0'
#     #totp = pyotp.TOTP('').now()
#     login = r.login(username, password, mfa_code = '008909',store_session=True)
#     # status = challenge_response.get("status")
#     # if status == "validated":
#     #     print("MFA validated successfully.")
#     # else:
#     #     print(f"Unexpected response: {challenge_response}")
#     #     raise Exception("Failed to validate MFA.")

#     return login


def buy_stock_dollar_amount(symbol, dollar_amount):
    try:
        quote = r.stocks.get_latest_price(symbol, includeExtendedHours=True)
        current_price = float(quote[0])
        shares_to_buy = round(dollar_amount / current_price, 8)
        result = r.orders.order_buy_fractional_by_price(
            symbol=symbol,
            amountInDollars=dollar_amount,
            timeInForce='gfd',
            extendedHours=False ,
        )
        print("Order Response:", result)
        print(f"Successfully placed an order for {shares_to_buy:.4f} shares of {symbol}.")
        return result
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    

#login_to_robinhood()

USER_TOKEN = os.environ.get("DISCORD_TOKEN")
TARGET_CHANNEL_ID = 1277335126493233234
import discord
import asyncio
import random
from datetime import datetime, time
import robin_stocks.robinhood as r

class SelfBot(discord.Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        account_info = r.profiles.load_account_profile()
        account_type = account_info.get('type', 'unknown')
        print("ADSFJLASD;FJDKSALFJDSAKL;")
        print(account_type)
        self.last_message_id = None

    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")
        self.loop.create_task(self.wait_until_market_open())  # Wait until 9:30 AM before running

    async def wait_until_market_open(self):
        while True:
            now = datetime.now()
            market_open = datetime.combine(now.date(), time(9, 30))  # 9:30 AM today
            market_close = datetime.combine(now.date(), time(17, 0))  # 5:00 PM today

            if market_open <= now < market_close:
                print("✅ Market is open. Starting message monitoring...")
                self.loop.create_task(self.check_mentions())  # START CHECKING MESSAGES
                return  # Exit function, bot is now working

            # Market is closed, schedule the next check
            next_open = market_open + timedelta(days=1) if now >= market_close else market_open
            sleep_duration = (next_open - now).total_seconds()
            print(f"⏳ Market closed. Sleeping for {sleep_duration // 3600:.0f} hours and {(sleep_duration % 3600) // 60:.0f} minutes.")
            
            await asyncio.sleep(sleep_duration)  # Sleep once until market opens

    async def check_mentions(self):
        while True:
            now = datetime.now().time()
            market_close = time(17, 0)  # 5:00 PM

            if now >= market_close:
                print("❌ Market closed. Stopping message monitoring.")
                return  # Stop checking messages

            # Fetch channel
            try:
                channel = await self.fetch_channel(TARGET_CHANNEL_ID)
                if not channel:
                    print(f"❌ Channel with ID {TARGET_CHANNEL_ID} not found.")
                    await asyncio.sleep(30)
                    continue
            except Exception as e:
                print(f"❌ Error fetching channel: {e}")
                await asyncio.sleep(30)
                continue

            try:
                async for message in channel.history(limit=1):
                    if self.last_message_id == message.id:
                        print("same message")
                        break  # Skip if it's the same message
                    print(f"📩 Last Message: {message.clean_content}")
                    message_time = message.created_at.replace(tzinfo=timezone.utc)
                    current_time = datetime.now(timezone.utc)

                    # Calculate the time difference
                    time_diff = (current_time - message_time).total_seconds()

                    ##UNDO##
                    # if time_diff > 120:
                    #     print(f"⏳ Skipping message (too old): {message.clean_content} ({time_diff // 60:.0f} min ago)")
                    #     continue


                    if message.embeds:
                        embed = message.embeds[0]
                        print(f"📝 Embed Title: {embed.title}")

                        # Extract text and check validity
                        title = embed.title.strip("*")
                        print("****")
                        print(title)
                        tList = title.split()
                        tList = "SPY 02/03 700.0C at .5"
                        tList = tList.split()
                        if not tList:
                            print("❌ Message format error: Empty title.")
                            continue

                        # Handling "Securing" (EXIT OPTION TRADE)
                        if tList[0] == "Securing" and len(tList) > 3:
                            symbol = tList[3]  # Stock symbol
                            option_id, quantity = None, None

                            open_positions = r.options.get_open_option_positions()
                            if open_positions:
                                for position in open_positions:
                                    if position["chain_symbol"] == symbol and float(position["quantity"]) > 0:
                                        option_id = position["option_id"]
                                        quantity = int(float(position["quantity"]))  # Convert to integer
                                        break

                            if option_id and quantity:
                                option_market_data = r.options.get_option_market_data(option_id)
                                market_price = float(option_market_data.get("mark_price", 0))  # Fetch market price

                                if market_price > 0:
                                    sell_response = r.options.order_sell_to_close(
                                        option_id=option_id,
                                        quantity=quantity,
                                        price=market_price,
                                        time_in_force="gfd"
                                    )
                                    print("✅ Sell Order Placed:", sell_response)
                                else:
                                    print("❌ Failed to retrieve valid market price.")
                            else:
                                print(f"❌ No open positions found for {symbol}.")
                            continue
                        if len(tList) < 3:
                            print("❌ Invalid message format. Skipping...")
                            continue
                        
                        stock_symbol = tList[0]  
                        putCall = tList[2][-1]   # 'C' for Call or 'P' for Put
                        strike = tList[2][:-1]   # Strike price without the 'C' or 'P'
                        input_date = tList[1]    # Expiration date in MM/DD format
                        try:
                            prem = float(tList[-1])
                        except ValueError:
                            print("❌ Invalid premium format.")
                            continue
                        try:
                            expiration_date = datetime.strptime(f"{input_date}/2025", "%m/%d/%Y")
                            formatted_date = expiration_date.strftime("%Y-%m-%d")
                        except ValueError:
                            print("❌ Invalid expiration date format.")
                            continue
                        
                        # Fetch valid options
                        option_data = r.options.find_options_by_specific_profitability(
                            inputSymbols=stock_symbol,
                            expirationDate=formatted_date,
                            strikePrice=strike,
                            optionType="call" if putCall == 'C' else 'put'
                        )
                        print(option_data)
                        # Filter options by premium
                        desired_premium = prem
                        filtered_options = [
                            option for option in option_data 
                            if float(option.get('adjusted_mark_price', 0)) <= desired_premium
                        ]

                        # Extract option IDs
                        option_ids = [option['id'] for option in filtered_options]
                        account = r.profiles.load_account_profile()
                        print("Buying Power:", account.get('buying_power'))
                        print("Cash Available:", account.get('cash'))
                        print("Margin Available:", account.get('margin_available'))
                        print("Overnight Buying Power:", account.get('overnight_buying_power'))
                        if option_ids:
                            limit_price = prem  # Slightly increase bid for execution
                            print(option_ids)
                            response = r.orders.order_buy_option_limit(
                                positionEffect="open",  # 'open' to open a new position
                                creditOrDebit="debit",  # Buying an option is a debit transaction
                                price=limit_price,      # The price you want to pay per contract
                                symbol=stock_symbol,    # Underlying stock symbol
                                quantity=1,             # Number of contracts to buy
                                expirationDate=formatted_date,  # Option expiration date (YYYY-MM-DD)
                                strike=strike,          # Strike price of the option
                                optionType="call" if putCall == 'C' else "put",  # Option type
                                timeInForce='gfd',
                                account_number='641599238'    # 'gfd' (Good for Day) or 'gtc' (Good Till Canceled)
                            )
                            print("✅ Buy Order Placed:", response)

                            #print("✅ Buy Order Placed:", response)
                        else:
                            print(f"❌ No matching options found for {stock_symbol}.")

                    # Update last processed message ID
                    self.last_message_id = message.id

            except Exception as e:
                print(f"❌ Error fetching messages: {e}")

            await asyncio.sleep(random.randint(30, 60))  # Continue checking messages

# Run the bot
client = SelfBot()
client.run(USER_TOKEN)  # Replace with actual token
