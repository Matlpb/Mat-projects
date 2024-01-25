import alpaca_trade_api as alpaca_api
import websockets
import json
import os
import asyncio
import requests

# Alpaca API credentials
alpaca_api_url = "https://paper-api.alpaca.markets"
openAI_api_key = 
alpaca_api_key = 
alpaca_api_secret = 

# Alpaca API initialization
api = alpaca_api.REST(alpaca_api_key, alpaca_api_secret, base_url='https://paper-api.alpaca.markets')

async def on_message(ws, message):
    print("Message is", message)

    current_event = json.loads(message)[0]
    
    if current_event['T'] == "n":
        company_impact = 0
        api_gpt = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "respond only with a number between 1-100 detailing the impact of the headline"},
                {"role": "user", "content": "Given the headline '" + current_event['headline'] + "', show me a number from 1-100 detailing the impact of this headline. "}
            ]
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": "Bearer " + openAI_api_key},
            json=api_gpt
        )

        if response.status_code == 200:
            data = response.json()
            print(data)

            message_content = data['choices'][0]['message']['content']
            print(message_content)

            company_impact = int(message_content)
            ticker_symbol = current_event['symbols'][0]

            # Determine the quantity to buy based on the company_impact
            if company_impact >= 80:
                quantity_to_buy = 2
            else:
                quantity_to_buy = 1

            # Buy or sell based on the company_impact
            if company_impact >= 70:
                # Buy stock
                account_info = api.get_account()
                if float(account_info.cash) > 0:
                    order = api.submit_order(
                        symbol=ticker_symbol,
                        qty=quantity_to_buy,
                        side='buy',
                        type='market',
                        time_in_force='day'
                    )
                    print(f"Buy order submitted for {ticker_symbol}")
                    print(f"Order ID: {order.id}")
                    print(f"Order Type: {order.type}")
                    print(f"Order Side: {order.side}")
                    print(f"Order Qty: {order.qty}")
                    print(f"Order Filled Qty: {order.filled_qty}")
                    print(f"Order Status: {order.status}")
                    print(f"Order Created At: {order.created_at}")
                else:
                    print("Insufficient funds to place a buy order.")
            elif company_impact <= 30:
                # Sell all shares
                positions = api.list_positions()
                for position in positions:
                    if position.symbol == ticker_symbol:
                        api.close_position(ticker_symbol)
                        print(f"Sold all shares for {ticker_symbol}")
                        break

        else:
            print(f'HTTP error! Status: {response.status_code}')
            print(response.text)

async def connect():
    async with websockets.connect("wss://stream.data.alpaca.markets/v1beta1/news") as ws:
        auth_msg = {
            "action": "auth",
            "key": alpaca_api_key,
            "secret": alpaca_api_secret
        }

        await ws.send(json.dumps(auth_msg))  # Log in

        sub_msg = {
            "action": "subscribe",
            "news": ['*']
        }

        await ws.send(json.dumps(sub_msg))

        while True:
            message = await ws.recv()
            await on_message(ws, message)

asyncio.run(connect())
