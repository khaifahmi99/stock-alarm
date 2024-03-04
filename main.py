import os
import requests
import time
from bs4 import BeautifulSoup
import json
import resend
from dotenv import load_dotenv
load_dotenv()

RESEND_API_KEY = os.environ['RESEND_API_KEY']
PRIMARY_RECEPIENT = os.environ['PRIMARY_RECEPIENT']

DEBUG_RECEPIENT = os.environ['DEBUG_RECEPIENT']

def parse_price(market, symbol):
    google_finance_request_url = "https://www.google.com/finance?q={}%3A{}".format(market, symbol)
    try:
        open_url = requests.get(google_finance_request_url)
        get_text = open_url.text
        soup = BeautifulSoup(get_text, "html.parser")
        # get the items that describe the stock
        items = soup.find_all("div", {"class": "gyFHrc"})
        # create a dictionary to store the stock description
        stock_description = {}
        # iterate over the items and append them to the dictionary
        for item in items:
            item_description = item.find("div", {"class": "mfs7Fc"}).text
            item_value = item.find("div", {"class": "P6K39c"}).text
            stock_description[item_description] = item_value
        
        stock_description["current_price"] = soup.find("div", {"class": "fxKbKc"}).text

        cleaned_price = stock_description['current_price'].strip('$')
        current_price = float(cleaned_price)

        return current_price
    except Exception as e:
        print(str(e))
        print('Error occurred in getting price change. Please ensure the stock symbol entered is correct')

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
            body += "<li>{} ({}) - {}/{} threshold met</li>".format(lower_items['symbol'], lower_items['price'], len(lower_items['thresholds_reached']), len(lower_items['thresholds_configured']))
        body += "</ul>"
        body += "</hr>"
    if len(upper_items) > 0:
        body += "<p>These stocks have increased above the threshold:</p>"
        body += "<ul>"
        for item in upper_items:
            body += "<li>{} ({}) - {}/{} threshold met</li>".format(upper_items['symbol'], upper_items['price'], len(upper_items['thresholds_reached']), len(upper_items['thresholds_configured']))
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

resend.api_key = RESEND_API_KEY
timestamp_iso = time.strftime('%Y-%m-%d %H:%M:%S')
print(f'[{timestamp_iso}] Stock Price Alert')
watchlist = parse_watchlist()

upper_selected = []
lower_selected = []
errors = []

for item in watchlist:
    symbol = item['symbol']
    try:
        price = parse_price(item['market'], symbol)
        if price is not None:
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
        else:
            print(f'[{symbol}] Error occurred in getting price change. Please ensure the stock symbol entered is correct')
            errors.append({ 'symbol': symbol, 'error': 'Parsing Error' })
        
    except Exception as e:
        errors.append({ 'symbol': symbol, 'error': 'Internal Error' })

    time.sleep(5)

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
