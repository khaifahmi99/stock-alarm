from bs4 import BeautifulSoup
import requests

'''
Retrieve the current price of the ticker.
This is done by crawling the web
'''
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
