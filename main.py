import os
import time
import json
import resend
from dotenv import load_dotenv
load_dotenv()
import asyncio
from prisma import Prisma

from ticker.api import get_prices

RESEND_API_KEY = os.environ['RESEND_API_KEY']
PRIMARY_RECEPIENT = os.environ['PRIMARY_RECEPIENT']

DEBUG_RECEPIENT = os.environ['DEBUG_RECEPIENT']

DATABASE_URL = os.environ['DATABASE_URL']


def parse_watchlist():
    file_path = './watchlist.json'
    with open(file_path) as f:
        data = json.load(f)
        
    watchlist = []
    for item in data['watchlist']:
        watchlist.append(item)

    return watchlist

def send_email(lower_items, upper_items):
    body = ''
    if len(lower_items) > 0:
        body += "<p>The following stocks have dropped below the threshold:</p>"
        body += "<ul>"
        for item in lower_items:
            body += "<li>{} ({}) - {}/{} threshold met</li>".format(item['symbol'], item['price'], len(item['thresholds_reached']), len(item['thresholds_configured']))
        body += "</ul>"
        body += "</hr>"
    if len(upper_items) > 0:
        body += "<p>These stocks have increased above the threshold:</p>"
        body += "<ul>"
        for item in upper_items:
            body += "<li>{} ({}) - {}/{} threshold met</li>".format(item['symbol'], item['price'], len(item['thresholds_reached']), len(item['thresholds_configured']))
        body += "</ul>"
        body += "</hr>"

    body += "<br />"
    body += "<br />"
    body += "<p>This email was sent automatically by the Stock Price Alert App.</p>"
    body += "<p>Thank you for using the Stock Price Alert App.</p>"
    body += "<p>Thank you!</p>"
    body += "<p>The Stock Price Alert App Team</p>"

    params = {
        "from": "MarketNotification <app-market-notification@resend.dev>",
        "to": [PRIMARY_RECEPIENT],
        "subject": "Threshold Reached",
        "html": body,
    }

    email = resend.Emails.send(params)
    print(email)

def send_debug_email(errors):
    body = "<p>The following stocks have encountered errors:</p>"
    body += "<ul>"
    for item in errors:
        body += "<li>{} ({})</li>".format(item['symbol'], item['error'])
    body += "</ul>"
    body += "</hr>"
    body += "<p>You are notified because you are included in the DEBUG RECEPIENT.</p>"

    params = {
        "from": "[DEV] MarketNotification <dev-market-notification@resend.dev>",
        "to": [DEBUG_RECEPIENT],
        "subject": "Error Encountered",
        "html": body,
    }

    email = resend.Emails.send(params)
    print(email)

async def open_database():
    if DATABASE_URL is None:
        print('[WARN] Database config not set')
        return None

    db = Prisma()
    await db.connect()

    print('[DB] Connected to database')
    return db

async def save_price(db, symbol, price):
    if db is None:
        return None

    try:
        await db.stock.create({
            'symbol': symbol,
            'price': price
        })
    except Exception as e:
        print(str(e))
        print(f'[DB] Error saving price for [{symbol}] to database')
        return False

    print(f'[DB] Saved price for [{symbol}] to database')
    return True


async def close_database(db):
    if db is None:
        return false

    await db.disconnect()
    print('[DB] Disconnected from database')
    return True

async def main() -> None:
    resend.api_key = RESEND_API_KEY
    timestamp_iso = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp_iso}] Stock Price Alert')
    watchlist = parse_watchlist()

    upper_selected = []
    lower_selected = []
    errors = []

    metadata = []

    db = await open_database()

    symbols = [item['symbol'] for item in watchlist]
    prices = get_prices(symbols)

    for item in watchlist:
        symbol = item['symbol'].upper()
        price = prices[symbol]
        try:
            if price is not None:
                print(f'[{symbol}] Price: ${price}')

                await save_price(db, symbol, price)

                upper_thresholds = item['thresholds']['upper']
                lower_thresholds = item['thresholds']['lower']
                
                print(f'[{symbol} (${price})] Checking price change (lower)')
                lower_threshold_count = len(lower_thresholds)
                if lower_threshold_count > 0:
                    threshold_reached = []
                    for threshold in lower_thresholds:
                        if price <= threshold:
                            print(f'Price has dropped below threshold (${threshold})')
                            threshold_reached.append(threshold)
                        else:
                            print(f'Above threshold (${threshold}), ignoring...')
                    if len(threshold_reached) > 0:
                        lower_selected.append({
                            'symbol': symbol,
                            'price': price,
                            'thresholds_reached': threshold_reached,
                            'thresholds_configured': lower_thresholds,
                        })

                print(f'[{symbol} (${price})] Checking price change (upper)')
                upper_threshold_count = len(upper_thresholds)
                if len(upper_thresholds) > 0:
                    threshold_reached = []
                    for threshold in upper_thresholds:
                        if price >= threshold:
                            print(f'Price has risen above threshold (${threshold})')
                            threshold_reached.append(threshold)
                        else:
                            print(f'Below threshold (${threshold}), ignoring...')
                    if len(threshold_reached) > 0:
                        upper_selected.append({
                            'symbol': symbol,
                            'price': price,
                            'thresholds_reached': threshold_reached,
                            'thresholds_configured': upper_thresholds,
                        })

                print('---------------------------------------------------------------')

                metadata.append({
                    'code': symbol,
                    'currentPrice': price,
                    'thresholds': {
                        'upper': upper_thresholds,
                        'lower': lower_thresholds,
                    }
                })
            else:
                print(f'[{symbol}] Error occurred in getting price change. Please ensure the stock symbol entered is correct')
                errors.append({ 'symbol': symbol, 'error': 'Parsing Error' })
            
        except Exception as e:
            errors.append({ 'symbol': symbol, 'error': 'Internal Error', stack: str(e) })

        time.sleep(5)

    await close_database(db)

    if len(metadata) > 0:
        with open('metadata.json', 'w') as f:
            json.dump(metadata, f)

    if len(lower_selected) > 0 or len(upper_selected) > 0:
        print('Sending email...')
        send_email(lower_selected, upper_selected)
    else:
        print('No stocks reached the threshold')

    if len(errors) > 0:
        print('[ERROR] Sending debug email...')
        send_debug_email(errors)
        print('[FIN] Fail')
        raise Exception('Error(s) found')

    print('[FIN] Success')

if __name__ == '__main__':
    asyncio.run(main())