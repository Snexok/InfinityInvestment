# Python Modules
import os
import json
import logging

# For telegram api
# pip install python-telegram-bot --upgrade
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, \
    CallbackQueryHandler, TypeHandler

# Local Nodule
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


def get_stock(update: Update, context: CallbackContext) -> None:
    res = get_stock_state(update.message.text)
    msg = update.message.text.lower()
    if "избранное" in msg or "избранного" in msg:
        id = str(update.effective_user.id)
        f = open(id + ".json", 'r')
        user = json.load(f)
        logger.info(user)
        if "сохранить" in msg or "добавить" in msg:
            stocks_name = msg.split(" ")
            stocks_name = list(filter(lambda word: word not in ["избранное", "сохранить", "в", "добавить"], stocks_name))
            for stock in stocks_name:
                if stock not in user:
                    stock = check_stock(stock)
                    logger.info(stock)
                    if stock:
                        user['favorites'].append({'name': stock['name'], 'price': stock['price'], 'best_price': stock['best_price']})
                        update.message.reply_text("Инструмент " + str(stock) + " добавлен в избранное")
            f.close()
            f = open(id + ".json", "w")
            json.dump(user, f)
        elif "удалить" in msg or "убрать" in msg:
            stocks_name = msg.split(" ")
            stocks_name = list(
                filter(lambda word: word not in ["избранного", "удалить", "из", "убрать"], stocks_name))
            for stock in stocks_name:
                if stock in user:
                    pass
                else:
                    stock = check_stock(stock)
                    logger.info(stock)
                    if stock:
                        favorite = filter(lambda favorite: favorite["name"] == stock, user['favorites'])[0]
                        user['favorites'].remove(favorite)
                        update.message.reply_text("Инструмент " + str(stock) + " удалён из избранного")
            f.close()
            f = open(id + ".json", "w")
            json.dump(user, f)
        else:
            for stock in user['favorites']:
                res = get_stock_state(stock["name"])
                update.message.reply_text(res)
        f.close()
    elif "изменения" in msg:
        id = str(update.effective_user.id)
        f = open(id + ".json", 'r')
        user = json.load(f)
        logger.info(user)
    else:
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
            return stock
        elif "stocks" in _stock:
            return False
    else:
        return False


def get_stock_back(update: Update, context: CallbackContext) -> None:
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

def track_users(update: Update, context: CallbackContext) -> None:
    """Store the user id of the incoming update, if any."""
    logger.info(update.effective_user.id)
    id = str(update.effective_user.id)
    if not os.path.isfile("users_data/"+id+".json"):
        f = open("users_data/"+id+".json", "a")
        f.write('{"id": '+id+'}')
        f.close()
    # if context.user_data.get("name") is None:
    #     context.user_data["name"] = update.message.text

def get_config():
    file = open("config/config.config").read()
    config = eval(file)
    return config

def main() -> None:
    config = get_config()
    updater = Updater(config['tokens']['telegram'])

    dispatcher = updater.dispatcher

    dispatcher.add_handler(TypeHandler(Update, track_users), group=-1)
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(get_stock_back))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, get_stock))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
