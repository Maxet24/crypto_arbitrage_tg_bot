import time

import telebot
from aiogram import Bot, Dispatcher, executor, types
import json, math
import datetime
from yoomoney import Quickpay, Client
from telebot.apihelper import ApiTelegramException

# Settings
paid_mode = True
TOKEN_YOUMONEY = "TOKEN"
client = Client(TOKEN_YOUMONEY)
TOKEN = "TGTOKEN"
pro_price = 9900


bot = telebot.TeleBot(TOKEN)

def get_paid_users():
    file = open('payments_info.txt')
    db = json.loads(file.readline())
    file.close()
    return db['paid_users']

def round_2(n):
    return math.floor(n * 100) / 100

def round_10(n):
    return math.floor(n * 10**10) / 10**10


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == "/menu":
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Арбитраж внутри Binance (Т-С-М) | Сбербанк/Тинькофф",
                                                callback_data="p2p_swap_sber_tink"))
        keyboard.add(types.InlineKeyboardButton(text="Арбитраж внутри Binance (Т-С-М) | Тинькофф", callback_data="p2p_swap_tink"))
        keyboard.add(types.InlineKeyboardButton(text="Арбитраж внутри Binance (Т-С-М) | Сбербанк", callback_data="p2p_swap_sber"))
        keyboard.add(types.InlineKeyboardButton(text="Межбиржевой арбитраж (без P2P)", callback_data="exchange_swap"))

        desc = "Выберите вид арбитража:\n\n" \
               "'Т-С-М' - в таких связках вы покупаете `Коин 1` на P2P, конвертируете его на споте в `Коин 2` и продаёте `Коин 2` на P2P."

        bot.send_message(message.from_user.id, text=desc, reply_markup=str(keyboard), parse_mode='markdown')
    elif message.text == "/help" or message.text == "/start":
        kb = [
            [
                types.KeyboardButton(text="/menu"),
                types.KeyboardButton(text="/help")
            ]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard = True)
        bot.send_message(message.from_user.id, "Здесь вы увидете самые сочные арбитражные ситуации.\n"
                                               "Сканер работает круглосуточно.\n\n"
                                               "Официальный канал бота: https://t.me/crypto_eye_arb\n\n"
                                               "/menu для перехода в главное меню и выбора категории связок.\n"
                                               "@crypto_eye_arbitrage - тех. поддержка", reply_markup=str(keyboard))
    elif message.text == "/faq":
        bot.send_message(message.from_user.id, "*Только для Межбиржи*\n"
                                               "Почему такие большие спреды? / Как арбитражить, если сети вывода разные?\n"
                                               "\n"
                                               "В этом и заключается работа арбитражника.\n"
                                               "Если вы видите, что комиссия сети высокая, то нужны большие объемы для торговли, чтобы размазать комиссию.\n"
                                               "Если вы видите, что сети разные, то нужно найти "
                                               "какой-то бридж или обменник.\n\n"
                                               "Не спешите кидаться помидорами. Наша команда реально работает по таким связкам и 3 % в день имеет и на том спасибо)\n"
                                               "При этом никакие карты не нужны, поэтому проблем с ФЗ не будет (для межбиржи).")
    else:
        bot.send_message(message.from_user.id, "Я вас не понимаю. Напишите /help.")

def sep_poss(possibilities):
    gran = 100.5
    free = []
    paid = []
    for possibility in possibilities:
        if possibility[1].split('/')[0][-2:] != '3L' and possibility[1].split('/')[1][-2:] != '3L' and\
                possibility[1].split('/')[0][-2:] != '3S' and possibility[1].split('/')[1][-2:] != '3S' and\
                possibility[6] >= 1 and possibility[7] >= 1:
            if 120 > possibility[0] >= gran or paid_mode:
                paid.append(possibility)
            elif gran > possibility[0] > 100.1:
                free.append(possibility)
    return [free, paid]

def sep_cases(cases):
    free = []
    paid = []
    for case in cases:
        if case[0] >= 0.1 or paid_mode:
            paid.append(case)
        elif case[0] >= 0.05:
            free.append(case)
    return [free, paid]

def mix_text(free, paid, is_pro):
    curr_is_free = True
    texts = []
    cnt = 1
    i = 0
    while i < max(len(free), len(paid)):
        pos = []
        if curr_is_free:
            if i < len(free):
                pos = free[i]
        else:
            if i < len(paid):
                pos = paid[i]
            i += 1

        if pos != []:
            text = ''
            if not is_pro and not curr_is_free:
                text += f"*{cnt}*. `****`\n"
            else:
                text += f"*{cnt}*. `{pos[1]}`\n"
            text += f"Купи на {pos[4]} за: {format(pos[2], '.8f')} {pos[1].split('/')[1]}\n"
            # text += f"Объем последнего ордера: {round_2(pos[6])} {pos[1].split("/")[1]}\n"
            text += f"Продай на {pos[5]} за: {format(pos[3], '.8f')} {pos[1].split('/')[1]}\n"
            # text += f"Объем ордеров: {int(pos[8])} {pos[1].split('/')[1]}\n"
            # text += f"Объем последнего ордера: {round_2(pos[7])} {pos[1].split("/")[1]}\n"
            text += f"Спред: {round_2(pos[0] - 100)} %\n\n"
            # text += f"Объем ордеров: {int(pos[9])} {pos[1].split('/')[1]}\n\n"

            texts.append(text)
            cnt += 1

        curr_is_free = not curr_is_free

    return texts

def get_bank_name(bank):
    banks = {
        'RosBankNew': 'СберБанк',
        'TinkoffNew': 'Тинькофф',
        'RaiffeisenBank': 'Райф',
        'HomeCreditBank': 'HomeCreditBank',
        'AkBarsBank': 'AkBarsBank',
    }

    if bank in banks:
        return banks[bank]
    else:
        return bank

def mix_text_p2p_binance(free, paid, is_pro):
    free.sort(reverse=True)
    paid.sort(reverse=True)


    curr_is_free = True
    text = ''
    cnt = 1
    i = 0
    while i < max(len(free), len(paid)):
        pos = []
        if curr_is_free:
            if i < len(free):
                pos = free[i]
        else:
            if i < len(paid):
                pos = paid[i]
            i += 1

        if pos != []:
            if not is_pro and not curr_is_free:
                text += f"*{cnt}*. `****`\n"
            else:
                text += f"*{cnt}*. `{pos[1]}\{pos[2]}`\n"

            if not is_pro and not curr_is_free:
                text += f"Купи за тейкера `****` на P2P по цене: `****` рублей\n"
            else:
                text += f"Купи за тейкера {pos[1]} на P2P по цене: {round_2(pos[3])} рублей\n"
            text += f"Оплата: {', '.join([get_bank_name(i) for i in pos[8]])}\n"

            if not is_pro and not curr_is_free:
                text += f"Конвертируй `****` в `****` по цене: `****`\n"
            else:
                text += f"Конвертируй {pos[1]} в {pos[2]} по цене: {format(pos[4], '.8f')}\n"

            if not is_pro and not curr_is_free:
                text += f"Продай за мейкера `****` на P2P по цене: `****` рублей\n"
            else:
                text += f"Продай за мейкера {pos[2]} на P2P по цене: {round_2(pos[5])} рублей\n"

            text += f"Оплата: {', '.join([get_bank_name(i) for i in pos[9]])}\n"


            text += f"Спред: {round_2(pos[0])} %\n\n"
            cnt += 1

        curr_is_free = not curr_is_free

    return text

def gen_payment_id(userid):
    file = open('payments_info.txt')
    info = json.loads(file.readline())
    file.close()

    last_id = int(info['last_id'])
    new_id = str(last_id + 1)
    info['last_id'] = new_id

    userid = str(userid)
    if userid not in info['transactions_by_userid']:
        info['transactions_by_userid'][userid] = []
    info['transactions_by_userid'][userid].append(new_id)

    jsonString = json.dumps(info)
    jsonFile = open('payments_info.txt', "w")
    jsonFile.write(jsonString)
    jsonFile.close()
    return new_id

@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    try:
        # Big eye
        now = datetime.datetime.now()
        human_readable_time = now.strftime("%Y-%m-%d %H:%M:%S")
        paid_users = get_paid_users()
        is_pro = call.from_user.id in paid_users
        print(f'User: {call.from_user.username} {call.from_user.id}, time {human_readable_time}, pro: {is_pro}, {call.data}')

        if '.' in call.data and call.data.split('.')[0] == 'nop2p':

            ex_pair = call.data.split('.')[1]
            page = int(call.data.split('.')[2])

            file = open(f'pairs_ex_swap\\{ex_pair}.json')


            data = json.loads(file.readline())
            possibilities, date = data
            file.close()


            free, paid = sep_poss(possibilities)
            free = free
            paid = paid


            text = '_В отличие от других сканеров мы показываем цены на покупку/продажу за тейкера. Это значит, что вы сразу можете зайти в сделку._\n\n'
            texts = mix_text(free, paid, is_pro)
            text += f'Доступных связок: {len(texts)}\n\n'
            text += ''.join(texts[page *  18:18 * (page + 1)])
            pages_cnt = math.ceil(len(texts) / 18)


            text += f'Дата обновления: {date}\n'

            keyboard = types.InlineKeyboardMarkup()

            ex_pair = ex_pair.split('_')
            if page > 0:
                keyboard.add(types.InlineKeyboardButton(text=f'Стр. {page + 1 - 1}', callback_data=f'nop2p.{ex_pair[0]}_{ex_pair[1]}.{page - 1}'))
            if page + 1 < pages_cnt:
                keyboard.add(types.InlineKeyboardButton(text=f'Стр. {page + 1 + 1}', callback_data=f'nop2p.{ex_pair[0]}_{ex_pair[1]}.{page + 1}'))

            bot.send_message(call.message.chat.id, text, parse_mode='markdown', reply_markup=str(keyboard))


            # ЗАПЛАТИ ТВАРЬ
            disclaimer = ''
            disclaimer += 'Что за звёздочки у некоторых пар?\n\n'
            disclaimer += 'Наша команда сама работает по этим парам с высоким процентом спреда, поэтому было бы нелогично вот так отдавать эти связки всем подряд.\n' \
                          f'Вы можете получить доступ к ним всего за `{pro_price}` РУБ.\n' \
                          'Сравните цены с конкурентами :)\n'

            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="Купить подписку НАВСЕГДА", callback_data="buy_subscription"))
            bot.send_message(call.message.chat.id, disclaimer, parse_mode='markdown', reply_markup=str(keyboard))

        elif call.data == 'exchange_swap':
            ex_pairs = [
                ['KuCoin', 'MEXC Global'],
                ['KuCoin', 'ByBit'],
                ['MEXC Global', 'Huobi'],
                ['KuCoin', 'MEXC Global'],
                ['Binance', 'KuCoin'],
                ['MEXC Global', 'BigONE'],
                ['MEXC Global', 'ByBit'],
            ]
            keyboard = types.InlineKeyboardMarkup()
            for ex_pair in ex_pairs:
                keyboard.add(types.InlineKeyboardButton(text=f'{ex_pair[0]} <-> {ex_pair[1]}', callback_data=f'nop2p.{ex_pair[0]}_{ex_pair[1]}.0'))

            bot.send_message(call.from_user.id, text="Выберите пару бирж.", reply_markup=str(keyboard))
        elif call.data in ["p2p_swap_tink", "p2p_swap_sber", "p2p_swap_sber_tink"]:
            fileName = ""
            if call.data == "p2p_swap_tink":
                fileName = "binance_p2p_tink.json"
            elif call.data == "p2p_swap_sber":
                fileName = "binance_p2p_sber.json"
            elif call.data == "p2p_swap_sber_tink":
                fileName = "binance_p2p_tink_sber.json"

            file = open(fileName)
            data = json.loads(file.readline())
            cases, date = data
            file.close()

            free, paid = sep_cases(cases)
            text = '_В отличие от других сканеров мы показываем цены на покупку/продажу за тейкера. Это значит, что вы сразу можете зайти в сделку._\n' \
                   'Все комиссии учтены.\n' \
                   'Для доказательства работоспособности бота мы раскрыли некоторые пары, чтобы вы могли проверить их сами.\n\n'
            text += mix_text_p2p_binance(free, paid, is_pro)

            text += f'Дата обновления: {date}\n'

            bot.send_message(call.message.chat.id, text, parse_mode='markdown')

            # ЗАПЛАТИ ТВАРЬ
            disclaimer = ''
            disclaimer += 'Что за звёздочки у некоторых пар?\n\n'
            disclaimer += 'Наша команда сама работает по этим парам с высоким процентом спреда, поэтому было бы нелогично вот так отдавать эти связки всем подряд.\n' \
                          'Вы можете получить доступ к ним всего за `9 900` РУБ.\n' \
                          'Сравните цены с конкурентами :)\n'

            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="Купить подписку НАВСЕГДА", callback_data="buy_subscription"))
            bot.send_message(call.message.chat.id, disclaimer, parse_mode='markdown', reply_markup=str(keyboard))
        elif call.data == "buy_subscription":
            # МЯСОО

            payment_id = str(gen_payment_id(call.from_user.id))
            quickpay = Quickpay(
                receiver="410018807695183",
                quickpay_form="shop",
                targets="Sponsor this project",
                paymentType="SB",
                sum=pro_price,
                label=payment_id
            )

            print(quickpay.redirected_url, payment_id)

            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text='Оплата (ЮMoney)', url=quickpay.redirected_url))
            keyboard.add(types.InlineKeyboardButton(text="Нажать после оплаты", callback_data="check_payment"))
            text = f"*{pro_price}* РУБ\n\n" \
                   "Вы получите:\n" \
                   "- Доступ к связкам с лучшим спредом в разделе межбиржевого арбитража\n" \
                   "- Вечный доступ к связкам P2P внутри Binance\n" \
                   "Срок: *НАВСЕГДА*"
            bot.send_message(call.from_user.id, text, reply_markup=str(keyboard), parse_mode='markdown')

        elif call.data == "check_payment":
            file = open('payments_info.txt')
            db = json.loads(file.readline())
            transactions_by_userid = db['transactions_by_userid']
            file.close()
            if str(call.from_user.id) not in transactions_by_userid:
                bot.send_message(call.from_user.id, 'Вы не завершили оплату.', parse_mode='markdown')

            payments = transactions_by_userid[str(call.from_user.id)]

            for payment_id in payments:
                history = client.operation_history(label=payment_id)
                for operation in history.operations:
                    if operation.status == 'success':
                        # PAID
                        if 'paid_users' not in db:
                            db['paid_users'] = []
                        if call.from_user.id not in db['paid_users']:
                            db['paid_users'].append(call.from_user.id)

                        jsonString = json.dumps(db)
                        jsonFile = open('payments_info.txt', "w")
                        jsonFile.write(jsonString)
                        jsonFile.close()
                        bot.send_message(call.from_user.id,
                                         'Спасибо за покупку.\n'
                                         'Теперь можете пользоваться сервисом без ограничений.',
                                         parse_mode='markdown')
                        return

            bot.send_message(call.from_user.id, 'Вы не завершили оплату.', parse_mode='markdown')
    except:
        print(call.from_user.id, call.from_user.username, ' hacker.')


bot.polling(none_stop=False, interval=0)