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

def stock_sms_alert_on_price_hike(your_stock_market, your_stock_symbol):
    google_finance_request_url = "https://www.google.com/finance?q={}%3A{}".format(your_stock_market, your_stock_symbol)
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

        return stock_description['current_price']
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

def send_email(items):
    body = "<p>The following stocks have dropped below the threshold:</p>"
    body += "<ul>"
    for item in items:
        body += "<li>{} ({})</li>".format(item['symbol'], item['price'])
    body += "</ul>"
    body += "</hr>"
    body += "<p>These stocks have dropped below the threshold you have set.</p>"
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

selected = []
errors = []

for item in watchlist:
    symbol = item['symbol']
    try:
        price = stock_sms_alert_on_price_hike(item['market'], symbol)
        if price is not None:
            threshold = item['threshold']
            if price <= threshold:
                print(f'[{symbol} (${price})] Price has dropped below threshold (${threshold})')
                selected.append({
                    'symbol': symbol,
                    'price': price,
                })
            else:
                print(f'[{symbol} (${price})] Above threshold (${threshold}), ignoring...')
        else:
            print(f'[{symbol}] Error occurred in getting price change. Please ensure the stock symbol entered is correct')
            errors.append({ 'symbol': symbol, 'error': 'Parsing Error' })
        
    except Exception as e:
        errors.append({ 'symbol': symbol, 'error': 'Internal Error' })

    time.sleep(5)

if len(selected) > 0:
    print('Sending email...')
    send_email(selected)
else:
    print('No stocks reached the threshold')

if len(errors) > 0:
    print('[ERROR] Sending debug email...')
    send_debug_email(errors)

print('---------------------------------------------------------------------------')