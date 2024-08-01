import yfinance as yf

'''
Retrieve the tickers object.
This is based on the yfinance library
'''
def get_tickers(symbols: list[str]):
    tickers_param = ' '.join(symbols).upper()

    tickers = yf.Tickers(tickers_param)

    return tickers

'''
Retrieve the current price of the tickers.
The response will be a dict of ticker_code/current_price
'''
def get_prices(tickers) -> dict:
    response = {}
    for ticker, data in tickers.tickers.items():
        print(f"[DEBUG]: Retrieving price for {ticker}")
        hist = data.history(period='1d', interval='1m')
        if len(hist) == 0:
            continue

        current_price = hist['Close'].iloc[-1]
        current_price = round(current_price, 2)
        response[ticker] = current_price
        print(f"[DEBUG]:    ${current_price}")

    return response

'''
Retrieve the percentage change of the tickers.
The response will be a dict of ticker_code/percentage_change
Valid range: 0-1
'''
def get_percentage_change(tickers) -> dict:
    response = {}
    for ticker, data in tickers.tickers.items():
        print(f"[DEBUG]: Retrieving price difference for {ticker}")
        hist = data.history(period='5d', interval='1d')
        if len(hist) < 2:
            continue

        current_price = hist['Close'].iloc[-1]
        previous_price = hist['Close'].iloc[-2]

        diff = (current_price - previous_price) / previous_price
        response[ticker] = diff

    return response

def get_recommendations(tickers) -> dict:
    response = {}
    for ticker, data in tickers.tickers.items():
        print(f"[DEBUG]: Retrieving recommendations for {ticker}")
        try:
            recommendations = data.recommendations

            strong_buy = int(recommendations['strongBuy'][0])
            buy = int(recommendations['buy'][0])
            hold = int(recommendations['hold'][0])
            sell = int(recommendations['sell'][0])
            strong_sell = int(recommendations['strongSell'][0])
            
            total_recommendations = strong_buy + buy + hold + sell + strong_sell

            response[ticker] = {
                'strongBuy': strong_buy,
                'buy': buy,
                'hold': hold,
                'sell': sell,
                'strongSell': strong_sell,

                'total': total_recommendations,
            }
        except Exception as e:
            print(f"[ERROR]: Error retrieving recommendations for {ticker}")
            print(str(e))
            response[ticker] = {
                'strongBuy': strong_buy,
                'buy': buy,
                'hold': hold,
                'sell': sell,
                'strongSell': strong_sell,

                'total': total_recommendations,
            }
    return response

