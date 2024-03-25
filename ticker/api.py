import yfinance as yf

'''
Retrieve the current price of the tickers.
This is done by using yfinance
The response will be a dict of ticker_code/current_price
'''
def get_prices(symbols: list[str]) -> dict:
    tickers_param = ' '.join(symbols).upper()

    tickers = yf.Tickers(tickers_param)

    response = {}
    for ticker, data in tickers.tickers.items():
        hist = data.history(period='20m', interval='1m')
        current_price = hist['Close'].iloc[-1]

        current_price = round(current_price, 2)
        response[ticker] = current_price

    return response

    
