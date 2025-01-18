import asyncio
import ccxt.async_support as ccxt
import json
import datetime
from itertools import *
import time

def load_to_json(data, name):
    jsonString = json.dumps(data)
    jsonFile = open('pairs_ex_swap\\' + name, "w")
    jsonFile.write(jsonString)
    jsonFile.close()

async def get_orderbook(excahnge, symbol):
    orderbook = await excahnge.fetch_order_book(symbol, 20)

    print('GOT', symbol)

    if len(orderbook['asks']) >= 1 and len(orderbook['bids']) >= 1:
        return {
            'symbol': symbol,
            'buy': orderbook['asks'][0],
            'sell': orderbook['bids'][0]
        }
    else:
        return -1


def get_symbols_filtered(excahnge):
    all_symbols = excahnge.symbols
    res = []
    for symbol in all_symbols:
        if ':' not in symbol:
            res.append(symbol)
    return res


def get_pairs_with(name, excahnge):
    print('Getting symbols...')
    symbols = get_symbols_filtered(excahnge)

    res = []
    for symbol in symbols:
        if name == symbol.split('/')[0] or name == symbol.split('/')[1] or name == '':
            res.append(symbol)

    print('Got symbols.')
    return res

async def get_prices_fast_supported(exchange, pairs, only_p2p_pairs = False):
    p2p_assets = ['USDT', 'BUSD', 'BNB', 'ETH', 'SHIB', 'BTC']

    print('Getting prices for ' + exchange.name + '...')

    raw_data = await exchange.fetch_bids_asks(pairs)
    results = []

    for pair in raw_data.keys():
        if not only_p2p_pairs or (pair.split('/')[0] in p2p_assets and pair.split('/')[1] in p2p_assets):
            results.append({
            'symbol': pair,
            'buy': [raw_data[pair]['ask'], -1],
            'sell': [raw_data[pair]['bid'], -1]
        })

    filtered_results = []

    for res in results:
        if res != -1:
            filtered_results.append(res)

    print('Got prices for ' + exchange.name + '.')
    return filtered_results

async def get_prices(exchange, pairs, only_p2p_pairs = False):
    p2p_assets = ['USDT', 'BUSD', 'BNB', 'ETH', 'SHIB', 'BTC']

    print('Getting prices for ' + exchange.name + '...')
    tasks = []

    for pair in pairs:
        if (not only_p2p_pairs or (pair.split('/')[0] in p2p_assets and pair.split('/')[1] in p2p_assets)) and pair.split('/')[0][-2:] != '3S' and \
                pair.split('/')[0][-2:] != '3L' and pair.split('/')[1][-2:] != '3L' and pair.split('/')[1][-2:] != '3S':
            tasks.append(asyncio.create_task(get_orderbook(exchange, pair)))

    results = []

    for task in tasks:
        try:
            results.append(await task)
        except:
            pass

    filtered_results = []

    for res in results:
        if res != -1:
            filtered_results.append(res)

    print('Got prices for ' + exchange.name + '.')
    return filtered_results

def convert_prices(prices):
    price_by_symbol = {}
    for case in prices:
        price_by_symbol[case['symbol']] = {
            'buy': case['buy'],
            'sell': case['sell']
        }
    return price_by_symbol


async def get_prices_ready(binance = ccxt.kucoin()):
    try:
        fast_supported = ['Binance']

        # Create exchanges
        first_ex = binance.name
        binance.throttle.config['maxCapacity'] = 10000
        await binance.load_markets()

        # task = asyncio.create_task(binance.fetch_currencies())
        # currs = await task


        # Get Symbols
        pairs_binance = get_pairs_with('', binance)
        pairs_binance = pairs_binance
        print(f'{first_ex}:{len(pairs_binance)}')

        # Get prices
        if binance.name in fast_supported:
            prices_binance = await get_prices_fast_supported(binance, pairs_binance)
        else:
            prices_binance = await get_prices(binance, pairs_binance)

        price_by_symbol_binance = convert_prices(prices_binance)

        await binance.close()

        return price_by_symbol_binance

    except:
        price_by_symbol_binance = -1

async def get_possibilities(price_by_symbol_binance, price_by_symbol_kucoin, first_ex, second_ex):
    possibilities = []
    try:
        for symbol in price_by_symbol_binance.keys():
            if symbol in price_by_symbol_kucoin and price_by_symbol_binance[symbol]['buy'][0] != 0 and price_by_symbol_binance[symbol]['sell'][0] != 0 and\
                    price_by_symbol_kucoin[symbol]['buy'][0] and price_by_symbol_kucoin[symbol]['sell'][0] != 0:

                if price_by_symbol_binance[symbol]['buy'][0] < price_by_symbol_kucoin[symbol]['sell'][0]:
                    buy_price = price_by_symbol_binance[symbol]['buy'][0]
                    buy_bid = price_by_symbol_binance[symbol]['buy'][1] * buy_price

                    sell_price = price_by_symbol_kucoin[symbol]['sell'][0]
                    sell_bid = price_by_symbol_kucoin[symbol]['sell'][1] * sell_price

                    possibilities.append([sell_price / buy_price * 100, symbol, buy_price, sell_price, first_ex.name, second_ex.name, buy_bid, sell_bid])
                    # print(f"{symbol} on binance buy: {buy_price} sell on kucoin: {sell_price}, profit: {sell_price / buy_price * 100}")

                if price_by_symbol_kucoin[symbol]['buy'][0] < price_by_symbol_binance[symbol]['sell'][0]:
                    buy_price = price_by_symbol_kucoin[symbol]['buy'][0]
                    buy_bid = price_by_symbol_kucoin[symbol]['buy'][1] * buy_price

                    sell_price = price_by_symbol_binance[symbol]['sell'][0]
                    sell_bid = price_by_symbol_binance[symbol]['sell'][1] * sell_price

                    possibilities.append([sell_price / buy_price * 100, symbol, buy_price, sell_price, second_ex.name, first_ex.name, buy_bid, sell_bid])
                    # print(f"{symbol} on kucoin buy: {buy_price} sell on binance: {sell_price}, profit {sell_price / buy_price * 100}")
    except:
        print('Problems in get_possibilities')
        print(first_ex, second_ex)
        print(price_by_symbol_binance)
        print('---------')
        print(price_by_symbol_kucoin)

    possibilities.sort(reverse=True)

    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d %H:%M:%S")

    data = [possibilities, date]

    load_to_json(data, f'{first_ex.name + "_" + second_ex.name}.json')
    for pos in possibilities:
        print(f"{pos[1]} on {pos[4]} buy: {pos[2]} ({pos[6]}) sell on {pos[5]}: {pos[3]} ({pos[7]}), profit: {pos[0]}")


async def loop():
    while True:
        ts = time.time()
        print(ccxt.exchanges)

        # ccxt.binance() 0
        # ccxt.kucoin() 1
        # ccxt.mexc() 2
        # ccxt.kucoin() 3
        # ccxt.bigone() 4
        exchanges = [ccxt.binance(), ccxt.kucoin(), ccxt.mexc(), ccxt.kucoin(), ccxt.bigone(), ccxt.huobi(), ccxt.bybit()]
        print([ex.name for ex in exchanges])

        pairs = []
        for perm in permutations([i for i in range(len(exchanges))], 2):
            pair = [perm[0], perm[1]]
            pair.sort()
            if pair not in pairs:
                pairs.append(pair)
        print(pairs)

        got_prices = []
        tasks = []
        for exchange in exchanges:
            tasks.append(asyncio.create_task(get_prices_ready(exchange)))

        for task in tasks:
            res = await task
            if res != -1:
                got_prices.append(res)

        for pair in pairs:
            await get_possibilities(got_prices[pair[0]], got_prices[pair[1]], exchanges[pair[0]], exchanges[pair[1]])

        print(f'DOONE in {time.time() - ts}')



if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(loop())

def convert_to_readable(spot_prices):
    # spot_prices['USDT'][0]['buy'] == 80.5
    new_format = {}

    for name in spot_prices:
        pair = spot_prices[name]
        first = name.split('/')[0]
        second = name.split('/')[1]

        if first not in new_format:
            new_format[first] = {}
        new_format[first][second] = {
            'buy': pair['buy'],
            'sell': pair['sell'],
        }

        if second not in new_format:
            new_format[second] = {}
        new_format[second][first] = {
            'buy': pair['sell'],
            'sell': pair['buy'],
        }
    return new_format

def convert_coins(s, first, second, spot_prices):

    for name in spot_prices:
        if first == name.split('/')[0] and second == name.split('/')[1]:
            return [s * spot_prices[first + '/' + second]['sell'][0], spot_prices[first + '/' + second]['sell'][0]]
        if first == name.split('/')[1] and second == name.split('/')[0]:
            return [s / spot_prices[second + '/' + first]['buy'][0], spot_prices[second + '/' + first]['buy'][0]]

async def main_copy():

    binance = ccxt.binance({'rateLimit' : 1000})

    # Create exchanges
    first_ex = binance.name
    binance.throttle.config['maxCapacity'] = 10000
    await binance.load_markets()

    # Get Symbols
    pairs_binance = get_pairs_with('', binance)
    pairs_binance = pairs_binance

    print(f'{first_ex}:{len(pairs_binance)}')

    # Get prices
    prices_binance = await get_prices(binance, pairs_binance, True)

    price_by_symbol_binance = convert_prices(prices_binance)

    await binance.close()

    return price_by_symbol_binance