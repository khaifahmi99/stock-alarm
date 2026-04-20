import os
import time
import json
import resend
from dotenv import load_dotenv
load_dotenv()
import asyncio
from prisma import Prisma
import argparse

from ticker.api import get_prices, get_tickers, get_recommendations, get_percentage_change, get_moving_averages, get_valuation_measures

RESEND_API_KEY = os.environ['RESEND_API_KEY']
PRIMARY_RECEPIENT = os.environ['PRIMARY_RECEPIENT']

DEBUG_RECEPIENT = os.environ['DEBUG_RECEPIENT']

DATABASE_URL = os.environ['DATABASE_URL']


def parse_watchlist(file_path):
    try:
        with open(file_path) as f:
            data = json.load(f)
            
        watchlist = []
        for item in data['watchlist']:
            watchlist.append(item)

        return watchlist
    except Exception as e:
        print(f'[ERROR] Error parsing watchlist: {e}')
        return []

def build_stock_table(items):
    table = '<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">'
    table += '<thead><tr><th>Ticker</th><th>Price</th><th>Threshold Cross</th><th>MA50</th><th>MA50 Value</th><th>MA200</th><th>MA200 Value</th><th>Mkt Cap</th><th>Trailing P/E</th><th>Forward P/E</th><th>P/B</th><th>EV/EBITDA</th></tr></thead>'
    table += '<tbody>'
    for item in items:
        price = item['price']
        ma50 = item.get('ma50')
        ma200 = item.get('ma200')
        ma50_arrow = '🔼' if ma50 is not None and price > ma50 else '🔻'
        ma200_arrow = '🔼' if ma200 is not None and price > ma200 else '🔻'
        ma50_value = ma50 if ma50 is not None else 'N/A'
        ma200_value = ma200 if ma200 is not None else 'N/A'
        threshold_cross = '{}/{}'.format(len(item['thresholds_reached']), len(item['thresholds_configured']))
        ticker_link = '<a href="https://finance.yahoo.com/quote/{}" target="_blank">{}</a>'.format(item['symbol'], item['symbol'])
        vm = item.get('valuation', {}) or {}
        table += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
            ticker_link, price, threshold_cross, ma50_arrow, ma50_value, ma200_arrow, ma200_value,
            vm.get('marketCap') or 'N/A',
            vm.get('trailingPE') or 'N/A',
            vm.get('forwardPE') or 'N/A',
            vm.get('priceToBook') or 'N/A',
            vm.get('evToEbitda') or 'N/A',
        )
    table += '</tbody></table>'
    return table

def send_email(lower_items, upper_items, skip = False):
    if skip:
        print('[DEBUG] Skipping send_email(skip = True)')
        return

    body = ''
    if len(lower_items) > 0:
        body += "<p>The following stocks have dropped below the threshold:</p>"
        body += build_stock_table(lower_items)
        body += "<br />"
    if len(upper_items) > 0:
        body += "<p>These stocks have increased above the threshold:</p>"
        body += build_stock_table(upper_items)
        body += "<br />"

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

def send_debug_email(errors, skip = False):
    if skip:
        print('[DEBUG] Skipping send_debug_email(skip = True)')
        return
    
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

async def open_database(skip = False):
    if skip:
        print('[DEBUG] Skipping open_database(skip = True)')
        return None

    if DATABASE_URL is None:
        print('[WARN] Database config not set')
        return None

    db = Prisma()
    await db.connect()

    print('[DB] Connected to database')
    return db

async def save_ticker(db, symbol, price, recommendations, percentage_change, ma50, ma200, skip = False):
    if skip:
        print('[DEBUG] Skipping save_ticker(skip = True)')
        return None

    if db is None:
        return None

    try:
        await db.stock.create({
            'symbol': symbol,
            'price': price,
            'percentageChange': percentage_change,

            'strongBuy': recommendations['strongBuy'],
            'buy': recommendations['buy'],
            'hold': recommendations['hold'],
            'sell': recommendations['sell'],
            'strongSell': recommendations['strongSell'],
            'total': recommendations['total'],

            'ma50': ma50,
            'ma200': ma200,
        })
    except Exception as e:
        print(str(e))
        print(f'[DB] Error saving ticker for [{symbol}] to database')
        return False

    print(f'[DB] Saved ticker for [{symbol}] to database')
    return True

async def close_database(db, skip = False):
    if skip:
        print('[DEBUG] Skipping close_database(skip = True)')
        return False

    if db is None:
        return False

    await db.disconnect()
    print('[DB] Disconnected from database')
    return True

async def main(file_path, skip = False) -> None:
    if skip:
        print('[INFO] "Skip" token found')
    print(f"[INFO] Input File: {file_path}")
    print("")

    resend.api_key = RESEND_API_KEY
    timestamp_iso = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp_iso}] Stock Price Alert')
    watchlist = parse_watchlist(file_path)

    upper_selected = []
    lower_selected = []
    errors = []

    metadata = []

    db = await open_database(skip = skip)
    symbols = [item['symbol'] for item in watchlist]

    tickers = get_tickers(symbols)

    prices = get_prices(tickers)
    recommendation_list = get_recommendations(tickers)
    percentage_changes = get_percentage_change(tickers)
    moving_averages = get_moving_averages(tickers)
    valuation_measures = get_valuation_measures(tickers)

    for item in watchlist:
        symbol = item['symbol'].upper()
        price = prices[symbol]
        percentage_change = percentage_changes[symbol]

        recommendations = recommendation_list[symbol]
        ma50 = moving_averages[symbol]['ma50']
        ma200 = moving_averages[symbol]['ma200']
        valuation = valuation_measures.get(symbol)
        try:
            if price is not None:
                print(f'[{symbol}] Price: ${price}, Change (%): {percentage_change * 100}')

                await save_ticker(db, symbol, price, recommendations, percentage_change, ma50, ma200, skip = skip)

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
                            'ma50': ma50,
                            'ma200': ma200,
                            'valuation': valuation,
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
                            'ma50': ma50,
                            'ma200': ma200,
                            'valuation': valuation,
                        })

                print('---------------------------------------------------------------')

                metadata.append({
                    'code': symbol,
                    'currentPrice': price,
                    'thresholds': {
                        'upper': upper_thresholds,
                        'lower': lower_thresholds,
                    },
                    'recommendations': recommendations
                })
            else:
                print(f'[{symbol}] Error occurred in getting price change. Please ensure the stock symbol entered is correct')
                errors.append({ 'symbol': symbol, 'error': 'Parsing Error' })
            
        except Exception as e:
            errors.append({ 'symbol': symbol, 'error': 'Internal Error', stack: str(e) })

        time.sleep(5)

    await close_database(db, skip = skip)

    if len(metadata) > 0 and not skip:
        with open('metadata.json', 'w') as f:
            json.dump(metadata, f)

    if len(lower_selected) > 0 or len(upper_selected) > 0:
        print('Sending email...')
        lower_selected.sort(key=lambda x: len(x['thresholds_reached']) / len(x['thresholds_configured']), reverse=True)
        upper_selected.sort(key=lambda x: len(x['thresholds_reached']) / len(x['thresholds_configured']), reverse=True)
        send_email(lower_selected, upper_selected, skip = skip)
    else:
        print('No stocks reached the threshold')

    if len(errors) > 0:
        print('[ERROR] Sending debug email...')
        send_debug_email(errors, skip = skip)
        print('[FIN] Fail')
        raise Exception('Error(s) found')

    print('[FIN] Success')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A program that parse the stock data based on the provided list')

    parser.add_argument('file_path', type=str, help='The file path of the stocklist')
    parser.add_argument('skip_token', type=bool, nargs='?', default=False, help='The skip token (optional). Default to False')

    args = parser.parse_args()

    asyncio.run(main(args.file_path, skip = args.skip_token))
