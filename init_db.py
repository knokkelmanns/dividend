import re
import json
import config
import requests
import psycopg2

# Initiating connection to DB
con = psycopg2.connect(database=config.database,
                       user=config.user,
                       password=config.password,
                       host=config.host,
                       port=config.port)

# Creating a table and setting columns
cur = con.cursor()

cur.execute("""DROP TABLE IF EXISTS dividend;""")
con.commit()

cur.execute("""CREATE TABLE dividend
          (
          ID           SERIAL PRIMARY KEY,
          COMPANY_NAME TEXT, 
          TICKER       TEXT NOT NULL,
          FREQ         TEXT,
          DECLARED     DATE,
          EXDIVIDEND   DATE,
          PAYOUT       DATE,
          AMOUNT       NUMERIC,
          INDUSTRY     TEXT,
          SECTOR       TEXT);""")
con.commit()


# Get full information about ticker
def get_stock_history(ticker):
    url = "https://seekingalpha.com/market_data/xignite_token"

    payload = {}
    headers = {
        'Accept': '*/*',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/79.0.3945.88 Safari/537.36 '
    }

    token = requests.request("GET", url, headers=headers, data=payload).json()

    data_api_url = f"https://globalhistorical.xignite.com/v3/xGlobalHistorical.json/GetCashDividendHistory?" \
                   f"IdentifierType=Symbol&Identifier={ticker}&StartDate=01/01/1800&EndDate=12/31/2025&" \
                   f"IdentifierAsOfDate=&CorporateActionsAdjusted=true&_token={token['_token']}" \
                   f"&_token_userid={token['_token_userid']}"

    dividend_history = requests.request("GET", data_api_url).json()
    # print(data_api_url)
    return dividend_history


def get_stocks_from_file(path):
    with open(path, "r") as file:
        return [stock.strip() for stock in file]


# Get full information about cash
def get_latest_ticker_dividends(dividend_history):
    sorted_dividends = dividend_history['CashDividends']

    # dividends = [dividend for dividend in sorted_dividends]

    sorted_dividends.sort(key=lambda x: (x['PayDate'] is not None, x['PayDate']), reverse=True)

    dividends = [dividend for dividend in sorted_dividends if dividend['PayDate']]

    return [dict(dividend, ticker=dividend_history['Identifier']) for dividend in dividends]


# Get full information about company
def get_dividend_data(tickers):
    dividend_data = {}
    for ticker in tickers:
        ticker_history = get_stock_history(ticker)
        dividends = get_latest_ticker_dividends(ticker_history)
        dividend_data[ticker] = []
        for dividend in dividends:
            data = {
                "Identifier": ticker_history["Identifier"],
                "Name": ticker_history["Security"]["Name"],
                "Sector": re.sub(r"(\w)([A-Z])", r"\1 \2", ticker_history["Security"]["Sector"]),
                "Industry": re.sub(r"(\w)([A-Z])", r"\1 \2", ticker_history["Security"]["Industry"]),
                "Type": dividend["Type"],
                "PaymentFrequency": dividend["PaymentFrequency"],
                "DeclaredDate": dividend["DeclaredDate"],
                # "RecordDate": dividend["RecordDate"],
                "PayDate": dividend["PayDate"],
                "ExDate": dividend["ExDate"],
                "DividendAmount": dividend["DividendAmount"],
            }
            dividend_data[ticker].append(data)
    return dividend_data


tickers = get_stocks_from_file("TICKERS_HERE.txt")
dividend_data = get_dividend_data(tickers)

# print(json.dumps(dividend_data, indent=1))

for ticker, ticker_data in dividend_data.items():
    for data in ticker_data:
        name = data["Name"]
        symbol = data["Identifier"]
        freq = data["PaymentFrequency"]
        declared_date = data["DeclaredDate"]
        exdividend_date = data["ExDate"]
        payout_date = data["PayDate"]
        amount = data["DividendAmount"]
        industry = data["Industry"]
        sector = data["Sector"]
        # dividend_type = data["Type"]
        print(f"{name}, {symbol}, {freq}, {declared_date}, {exdividend_date}, {payout_date}, {amount}, {industry}, "
              f"{sector}")

# Inserting data about dividends into a table
        cur.execute("INSERT INTO dividend (COMPANY_NAME, TICKER, FREQ, DECLARED, EXDIVIDEND, PAYOUT, AMOUNT, INDUSTRY, "
                    "SECTOR) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (name, symbol, freq, declared_date, exdividend_date, payout_date, amount, industry, sector))
        con.commit()
