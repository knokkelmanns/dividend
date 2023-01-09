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
          COMPANY_NAME TEXT NOT NULL, 
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
def get_company_data(dividend_history):
    company_data = dividend_history['Security']

    # print(json.dumps(company_data, indent=1))

    return [dict(company_data)]


paying_companies = []
company_info = []
for ticker in get_stocks_from_file("keka.txt"):
    ticker_history = get_stock_history(ticker)
    paying_companies.extend(get_latest_ticker_dividends(ticker_history))
    company_info.extend(get_company_data(ticker_history))


for dividend in paying_companies:
    ticker = dividend['ticker']
    freq = dividend['PaymentFrequency']
    amount = dividend['DividendAmount']
    declared_date = dividend['DeclaredDate']
    exdividend_date = dividend['ExDate']
    payout_date = dividend['PayDate']

# Inserting data about dividends into a table
    cur.execute("INSERT INTO dividend (TICKER, FREQ, DECLARED, EXDIVIDEND, PAYOUT, AMOUNT) VALUES(%s, %s, "
                "%s, %s, %s, %s)", (ticker, freq, declared_date, exdividend_date, payout_date, amount))
    con.commit()

for data in company_info:
    name = data['Name']
    industry = re.sub(r"(\w)([A-Z])", r"\1 \2", data['Industry'])
    sector = re.sub(r"(\w)([A-Z])", r"\1 \2", data['Sector'])
    # print(name, industry, sector)

# Inserting data about company into a table
    cur.execute("INSERT INTO dividend (COMPANY_NAME, INDUSTRY, SECTOR) VALUES(%s, %s, %s)", (name, industry, sector))
    con.commit()
