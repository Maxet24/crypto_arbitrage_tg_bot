import json

file = open('temp.json')
binance_prices = json.loads(file)
print(file)