# Python Modules
import os
import json
import logging

# For telegram api
# pip install python-telegram-bot --upgrade
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, \
    CallbackQueryHandler, TypeHandler

# Local Modules
from Broker.Broker import Broker

logger = logging.getLogger(__name__)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Привет, по какой акции ты хочешь получить статистику?")


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def get_user(update):
    id = str(update.effective_user.id)
    f = open("users_data/" + id + ".json", 'r')
    user = json.load(f)
    f.close()
    return user


def save_user(user):
    f = open("users_data/" + str(user['id']) + ".json", "w")
    json.dump(user, f)
    f.close()


def get_stock_by_msg(msg, filter_words):
    stocks_name = msg.split(" ")
    stocks_name = list(filter(lambda word: word not in filter_words, stocks_name))

    if len(stocks_name) == 1:
        stock = stocks_name[0]
        return check_stock(stock)
    elif len(stocks_name):
        stocks = []
        for stock in stocks_name:
            stock.append(check_stock(stock))
        return stocks


def get_favorite(user, stock):
    favorite = list(filter(lambda favorite: favorite["name"].lower() == stock['name'].lower(), user['favorites']))
    favorite = favorite[0] if len(favorite) > 0 else favorite
    return favorite


def main_handler(update: Update, context: CallbackContext) -> None:
    msg = update.message.text.lower()
    if "избранное" in msg or "избранного" in msg:
        user = get_user(update)
        if "сохранить" in msg or "добавить" in msg:
            filter_words = ["избранное", "сохранить", "в", "добавить"]
            stock = get_stock_by_msg(msg, filter_words)
            favorite = get_favorite(user, stock)
            if favorite:
                update.message.reply_text("Инструмент " + str(stock['name']) + " уже в избранном")
            else:
                user['favorites'].append(
                    {'name': stock['name'], 'price': stock['price'], 'best_price': stock['best_price']})
                save_user(user)
                update.message.reply_text("Инструмент " + str(stock['name']) + " добавлен в избранное")
        elif "удалить" in msg or "убрать" in msg:
            filter_words = ["избранного", "удалить", "из", "убрать"]
            stock = get_stock_by_msg(msg, filter_words)
            favorite = get_favorite(user, stock)
            if favorite:
                user['favorites'].remove(favorite)
                save_user(user)
                update.message.reply_text("Инструмент " + str(stock['name']) + " удалён из избранного")
        else:
            if len(user['favorites']) == 0:
                update.message.reply_text("Избранное пусто")
            else:
                for stock in user['favorites']:
                    res = get_stock_state(stock["name"])
                    update.message.reply_text(res)
    elif "изменения" in msg:
        user = get_user(update)
    else:
        res = get_stock_state(update.message.text)
        if type(res) == str:
            update.message.reply_text(res)
        else:
            update.message.reply_text('Уточни что вы имели ввиду:', reply_markup=res)


def check_stock(stock_name):
    broker = Broker()
    _stock = broker.get_stock(stock_name)
    if _stock:
        if "stock" in _stock:
            stock = _stock['stock'].to_dict()
            candles = broker.get_profit_stat(stock, {'days': 1, 'hours': 0}, interval='day')
            stock['price'] = candles[0].c
            broker.set_candles(stock, {'days': 365, 'hours': 0}, interval='day')
            best_price = broker.get_best_current_price()[-1]
            stock['best_price'] = best_price
            return stock
        elif "stocks" in _stock:
            return False
    else:
        return False


def stock_back_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    res = get_stock_state(query.data)

    query.edit_message_text(res)


def get_stock_state(stock_name):
    period = {'days': 365, 'hours': 0}
    interval = 'day'
    broker = Broker()
    _stock = broker.get_stock(stock_name)
    if _stock:
        if "stock" in _stock:
            stock = _stock['stock'].to_dict()
            broker.set_candles(stock, period, interval)
            best_price = broker.get_best_current_price()[-1]
            res_text = stock['name'] + "\n\n" + \
                       "Current price: " + str(broker.candles[-1].c) + "\n\n" + \
                       "Best price: " + str(round(best_price, 2)) + "\n\n" + \
                       "Profit: " + str(round(round(best_price, 2) - broker.candles[-1].c, 2)) + " (" + str(
                round(((round(best_price, 2) / broker.candles[-1].c) - 1) * 100, 2)) + "%)"
            return res_text
        elif "stocks" in _stock:
            names = [stock.to_dict()['name'] for stock in _stock['stocks']]
            keyboard = [[InlineKeyboardButton(name[:30], callback_data=name[:30])] for name in names]

            reply_markup = InlineKeyboardMarkup(keyboard)

            return reply_markup
    else:
        return "Инструментов с таким названием не найдено"


def track_users_handler(update: Update, context: CallbackContext) -> None:
    """Store the user id of the incoming update, if any."""
    id = str(update.effective_user.id)
    if not os.path.isfile("users_data/" + id + ".json"):
        f = open("users_data/" + id + ".json", "a")
        f.write('{"id": ' + id + ', "favorites":[]}')
        f.close()


def get_config():
    file = open("config/config.config").read()
    config = eval(file)
    return config


def main() -> None:
    config = get_config()
    updater = Updater(config['tokens']['telegram'])

    dispatcher = updater.dispatcher

    dispatcher.add_handler(TypeHandler(Update, track_users_handler), group=-1)
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(stock_back_handler))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, main_handler))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
