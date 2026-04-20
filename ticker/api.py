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

def safe_int(df, column):
    try:
        return int(df[column].iloc[0])
    except (KeyError, IndexError, TypeError, ValueError):
        return 0

'''
Retrieve the 50-day and 200-day moving averages of the tickers.
The response will be a dict of ticker_code/{'ma50': float, 'ma200': float}
'''
def get_moving_averages(tickers) -> dict:
    response = {}
    for ticker, data in tickers.tickers.items():
        print(f"[DEBUG]: Retrieving moving averages for {ticker}")
        try:
            hist = data.history(period='1y', interval='1d')
            closes = hist['Close']

            ma50 = round(float(closes.tail(50).mean()), 2) if len(closes) >= 50 else None
            ma200 = round(float(closes.tail(200).mean()), 2) if len(closes) >= 200 else None

            response[ticker] = {'ma50': ma50, 'ma200': ma200}
        except Exception as e:
            print(f"[ERROR]: Error retrieving moving averages for {ticker}")
            print(str(e))
            response[ticker] = {'ma50': None, 'ma200': None}
    return response

'''
Retrieve the current valuation measures of the tickers.
The response will be a dict of ticker_code/{'marketCap': ..., 'trailingPE': ..., ...}
Only the most recent (current) row of valuation_measures is returned.
'''
def get_valuation_measures(tickers) -> dict:
    response = {}
    for ticker, data in tickers.tickers.items():
        print(f"[DEBUG]: Retrieving valuation measures for {ticker}")
        try:
            vm = data.valuation_measures
            if vm is None or len(vm) == 0:
                raise ValueError("No valuation data")
            current = vm.iloc[-1]

            def safe_val(key):
                try:
                    v = current[key]
                    if v != v:  # NaN check
                        return None
                    return float(v)
                except (KeyError, TypeError):
                    return None

            response[ticker] = {
                'marketCap': safe_val('MarketCap'),
                'trailingPE': safe_val('TrailingPE'),
                'forwardPE': safe_val('ForwardPE'),
                'priceToBook': safe_val('PriceToBook'),
                'evToEbitda': safe_val('EnterprisesToEbitda'),
            }
        except Exception as e:
            print(f"[ERROR]: Error retrieving valuation measures for {ticker}: {e}")
            response[ticker] = {
                'marketCap': None,
                'trailingPE': None,
                'forwardPE': None,
                'priceToBook': None,
                'evToEbitda': None,
            }
    return response

def get_recommendations(tickers) -> dict:
    response = {}
    for ticker, data in tickers.tickers.items():
        print(f"[DEBUG]: Retrieving recommendations for {ticker}")
        try:
            recommendations = data.recommendations

            strong_buy  = safe_int(recommendations, 'strongBuy')
            buy         = safe_int(recommendations, 'buy')
            hold        = safe_int(recommendations, 'hold')
            sell        = safe_int(recommendations, 'sell')
            strong_sell = safe_int(recommendations, 'strongSell')
            
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

