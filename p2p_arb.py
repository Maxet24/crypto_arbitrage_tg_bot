import p2p_parse
import exch_swaps
import asyncio
import asyncio
import json
import datetime
import time

def load_to_json(data, name):
    jsonString = json.dumps(data)
    jsonFile = open(name, "w")
    jsonFile.write(jsonString)
    jsonFile.close()

def load_p2p_prices(payTypes):
    prices = {}
    assets = ['USDT', 'BUSD', 'BNB', 'ETH', 'SHIB', 'BTC']

    for asset in assets:
        buy = p2p_parse.get_price(asset, 'buy', payTypes)
        sell = p2p_parse.get_price(asset, 'sell', payTypes)
        prices[asset] = {
            'buy': buy,
            'sell': sell
        }
    return prices

async def get_cases(payTypes):
    # file = open('temp.json').readline().replace("'", '"')
    # spot_prices = json.loads(file)
    spot_prices = await exch_swaps.main_copy()

    p2p_prices = load_p2p_prices(payTypes)

    assets = ['USDT', 'BUSD', 'BNB', 'ETH', 'SHIB', 'BTC']

    cases = []
    for asset in assets:
        asset_spot_prices = exch_swaps.convert_to_readable(spot_prices)[asset]
        for second_asset in assets:
            if second_asset in asset_spot_prices:

                buy_methods = p2p_prices[asset]['buy'][2]
                sell_methods = p2p_prices[second_asset]['buy'][2]

                bought_asset_rub = p2p_prices[asset]['buy'][0]

                # Convert asset 1 to asset 1 in quantity of 1
                got_asset_2_for_asset_1, price_to_convert = exch_swaps.convert_coins(1, asset, second_asset, spot_prices)

                # sell asset 2 on p2p
                second_asset_sell_price = p2p_prices[second_asset]['buy'][0]

                # got rub for selling second (without fees)
                sold_second_for_rub = got_asset_2_for_asset_1 * second_asset_sell_price

                # got rub with fees
                sold_second_for_rub_with_fees = sold_second_for_rub * 0.999 * 0.999

                profit = sold_second_for_rub_with_fees / bought_asset_rub * 100 - 100

                case = [profit, asset, second_asset, bought_asset_rub, price_to_convert, second_asset_sell_price, sold_second_for_rub,
                        sold_second_for_rub_with_fees, buy_methods, sell_methods]
                # 0 - profit, 1 - first asset, 2 - second asset, 3 - buy first on p2p for, 4 - convert price, 5 - sell price  second asset
                # 6 - sold second for (without fees), 7 - without fees
                if profit > 0:
                    cases.append(case)
    cases.sort(reverse=True)
    return cases

async def main():
    cases = await get_cases()
    cases.sort(reverse=True)
    for case in cases:
        print('-----------')
        print(f'{case[1]} -> {case[2]}')
        print(f'Buy {case[1]} on P2P for {case[3]}.')
        print(f'{case[8]}')
        print(f'Convert to {case[2]} with price {case[4]}.')
        print(f'Sell {case[2]} on P2P for {case[5]} and get.')
        print(f'{case[9]}')
        print(f'Profit: {case[0]}')
        print('-----------')

async def write_to_db(payTypes):
    cases = await get_cases(payTypes)
    for case in cases:
        print('-----------')
        print(f'{case[1]} -> {case[2]}')
        print(f'Buy {case[1]} on P2P for {case[3]}.')
        print(f'{case[8]}')
        print(f'Convert to {case[2]} with price {case[4]}.')
        print(f'Sell {case[2]} on P2P for {case[5]} and get.')
        print(f'{case[9]}')
        print(f'Profit: {case[0]}')
        print('-----------')

    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d %H:%M:%S")

    data = [cases, date]

    fileName = ''
    if payTypes == ["TinkoffNew"]:
        fileName = f'binance_p2p_tink.json'
    elif payTypes == ["RosBankNew"]:
        fileName = f'binance_p2p_sber.json'
    elif payTypes == ['RosBankNew', 'TinkoffNew']:
        fileName = f'binance_p2p_tink_sber.json'


    load_to_json(data, fileName)


async def loop():
    while True:
        print('Сбер/Тиньк')
        try:
            await write_to_db(["RosBankNew", "TinkoffNew"])
        except:
            print('ХЬСТОН!')

        print('Тинькофф')
        try:
            await write_to_db(["TinkoffNew"])
        except:
            print('ХЬСТОН!')

        print('Сбербанк')
        try:
            await write_to_db(["RosBankNew"])
        except:
            print('ХЬСТОН!')
        time.sleep(10)


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(loop())