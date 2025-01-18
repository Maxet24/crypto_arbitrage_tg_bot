import asyncio
import ccxt.async_support as ccxt
import json
import datetime

def load_to_json(data, name):
    jsonString = json.dumps(data)
    jsonFile = open(name, "w")
    jsonFile.write(jsonString)
    jsonFile.close()

async def get_orderbook(excahnge, symbol):
    orderbook = await excahnge.fetch_order_book(symbol, 20)

    print('GOT', symbol)

    if len(orderbook['asks']) >= 1 and len(orderbook['bids']) >= 1:
        return {
            'symbol': symbol,
            'buy': orderbook['asks'][0],
            'sell': orderbook['bids'][0],
            'orderbook': orderbook,
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

async def get_prices(exchange, pairs, only_p2p_pairs = False):
    p2p_assets = ['USDT', 'BUSD', 'BNB', 'ETH', 'SHIB', 'BTC']

    print('Getting prices for ' + exchange.name + '...')
    tasks = []

    for pair in pairs:
        if not only_p2p_pairs or (pair.split('/')[0] in p2p_assets and pair.split('/')[1] in p2p_assets):
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
        volume = 0
        for order in case['orderbook']['bids']:
            volume += order[0] * order[1]
        for order in case['orderbook']['asks']:
            volume += order[0] * order[1]

        price_by_symbol[case['symbol']] = {
            'buy': case['buy'],
            'sell': case['sell'],
            'volume': volume,
        }
    return price_by_symbol


async def main(binance = ccxt.kucoin(), kucoin = ccxt.mexc()):
    print(ccxt.exchanges)
    # Create exchanges
    first_ex = binance.name
    binance.throttle.config['maxCapacity'] = 10000
    await binance.load_markets()

    second_ex = kucoin.name
    kucoin.throttle.config['maxCapacity'] = 10000
    await kucoin.load_markets()

    # task = asyncio.create_task(binance.fetch_currencies())
    # currs = await task


    # Get Symbols
    pairs_binance = get_pairs_with('', binance)
    pairs_binance = pairs_binance

    pairs_kucoin = get_pairs_with('', kucoin)
    pairs_kucoin = pairs_kucoin
    print(f'{first_ex}:{len(pairs_binance)}')
    print(f'{second_ex}:{len(pairs_kucoin)}')


    # Get prices
    prices_binance = await get_prices(binance, pairs_binance)
    prices_kucoin = await get_prices(kucoin, pairs_kucoin)

    price_by_symbol_binance = convert_prices(prices_binance)
    price_by_symbol_kucoin = convert_prices(prices_kucoin)

    # print(price_by_symbol_binance)

    possibilities = []
    for symbol in price_by_symbol_binance.keys():
        if symbol in price_by_symbol_kucoin:
            if price_by_symbol_binance[symbol]['buy'] < price_by_symbol_kucoin[symbol]['sell']:
                buy_price = price_by_symbol_binance[symbol]['buy'][0]
                buy_bid = price_by_symbol_binance[symbol]['buy'][1] * buy_price
                volume_binance = price_by_symbol_binance[symbol]['volume']

                sell_price = price_by_symbol_kucoin[symbol]['sell'][0]
                sell_bid = price_by_symbol_kucoin[symbol]['sell'][1] * sell_price
                volume_kucoin = price_by_symbol_kucoin[symbol]['volume']

                possibilities.append([sell_price / buy_price * 100, symbol, buy_price, sell_price, first_ex, second_ex, buy_bid, sell_bid, volume_binance, volume_kucoin])
                # print(f"{symbol} on binance buy: {buy_price} sell on kucoin: {sell_price}, profit: {sell_price / buy_price * 100}")

            if price_by_symbol_kucoin[symbol]['buy'] < price_by_symbol_binance[symbol]['sell']:
                buy_price = price_by_symbol_kucoin[symbol]['buy'][0]
                buy_bid = price_by_symbol_kucoin[symbol]['buy'][1] * buy_price
                volume_kucoin = price_by_symbol_kucoin[symbol]['volume']

                sell_price = price_by_symbol_binance[symbol]['sell'][0]
                sell_bid = price_by_symbol_binance[symbol]['sell'][1] * sell_price
                volume_binance = price_by_symbol_binance[symbol]['volume']

                possibilities.append([sell_price / buy_price * 100, symbol, buy_price, sell_price, second_ex, first_ex, buy_bid, sell_bid, volume_kucoin, volume_binance])
                # print(f"{symbol} on kucoin buy: {buy_price} sell on binance: {sell_price}, profit {sell_price / buy_price * 100}")

    possibilities.sort(reverse=True)

    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d %H:%M:%S")

    data = [possibilities, date]

    load_to_json(data, f'{binance.name + "_" + kucoin.name}.json')
    for pos in possibilities:
        print(f"{pos[1]} on {pos[4]} buy: {pos[2]} ({pos[6]}) sell on {pos[5]}: {pos[3]} ({pos[7]}), profit: {pos[0]}, volume{possibilities[8]}")

    await binance.close()
    await kucoin.close()

async def loop():
    while True:
        pairs = [
            [ccxt.kucoin(), ccxt.mexc()],
            [ccxt.bigone(), ccxt.mexc()],
            [ccxt.binance(), ccxt.kucoin()],
            [ccxt.binance(), ccxt.mexc()],
        ]
        # [ccxt.binance({'rateLimit' : 1000}), ccxt.kucoin()],
        for pair in pairs:

            await main(pair[0], pair[1])

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