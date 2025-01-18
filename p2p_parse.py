import requests
import json
import asyncio

def get_price(asset = 'USDT', type = 'buy', payTypes = ["TinkoffNew"]):
    URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    payload = {
        "fiat": "RUB",
        "page": 1,
        "rows": 20,
        "tradeType": type,
        "asset": asset,
        "countries": [],
        "proMerchantAds": False,
        "publisherType": None,
        "payTypes": payTypes
    }

    response = requests.post(URL, json=payload)

    response = json.loads(response.text)
    bids = response['data']
    # price = response['data'][0]['adv']['price']
    # 'minSingleTransAmount'
    for bid in bids:
        max_amount = float(bid['adv']['maxSingleTransAmount'])
        price = float(bid['adv']['price'])
        if max_amount >= 10000:
            return [price, max_amount, [i['identifier'] for i in bid['adv']['tradeMethods']]]
    return False

if __name__ == "__main__":
    assets = [
        'SHIB', 'USDT', 'BNB', 'BTC', 'ETH'
    ]
    for asset in assets:
        print(asset, get_price(asset, 'buy'), get_price(asset, 'sell'))


