import ccxt
import csv
import requests

def fetch_top_cryptocurrencies(limit=500):
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page={limit}&page=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
      
        return [coin['symbol'].upper() for coin in data]
    else:
        print("Failed to fetch data from CoinGecko.")
        return []

def fetch_available_pairs(exchange_id, crypto_symbols):
    exchange_class = getattr(ccxt, exchange_id)()
    exchange_class.load_markets()
    available_pairs = {}

    for symbol in crypto_symbols:
        pairs = [market for market in exchange_class.symbols if symbol in market]
        available_pairs[symbol] = pairs
    return available_pairs

top_crypto_symbols = fetch_top_cryptocurrencies(500)

exchanges = ['coinbasepro', 'binance', 'bitfinex']

exchange_pairs = {exchange: fetch_available_pairs(exchange, top_crypto_symbols) for exchange in exchanges}

with open('crypto_pairs.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Symbol', 'CoinbasePro Pairs', 'Binance Pairs', 'Bitfinex Pairs'])
    
    for symbol in top_crypto_symbols:
        coinbasepro_pairs = ', '.join(exchange_pairs['coinbasepro'].get(symbol, []))
        binance_pairs = ', '.join(exchange_pairs['binance'].get(symbol, []))
        bitfinex_pairs = ', '.join(exchange_pairs['bitfinex'].get(symbol, []))
        writer.writerow([symbol, coinbasepro_pairs, binance_pairs, bitfinex_pairs])

print("Results have been saved to crypto_pairs.csv.")
