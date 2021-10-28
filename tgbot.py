# Python Modules
import os
import json
import logging

# For telegram api
# pip install python-telegram-bot --upgrade
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, \
    CallbackQueryHandler, TypeHandler, ConversationHandler

# Local Modules
from Broker.Broker import Broker
from User.User import User

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


def get_stock_by_msg(stocks_name):
    if len(stocks_name) == 1:
        stock = stocks_name[0]
        return check_stock(stock)
    elif len(stocks_name):
        stocks = []
        for stock in stocks_name:
            stock.append(check_stock(stock))
        return stocks


def main_handler(update: Update, context: CallbackContext):
    msg = update.message.text.lower()
    if "избранное" in msg or "избранного" in msg or "сохранить" in msg or "добавить" in msg or "удалить" in msg or "убрать" in msg or "очистить" in msg:
        user = User(str(update.effective_user.id))
        if "сохранить" in msg or "добавить" in msg:
            filter_words = ["избранное", "сохранить", "в", "добавить"]
            stocks_name = msg.split(" ")
            stocks_name = list(filter(lambda word: word not in filter_words, stocks_name))
            stocks = get_stock_by_msg(stocks_name)
            if stocks:
                logger.info("stocks")
                logger.info(stocks)
                logger.info(isinstance(stocks, list))
                logger.info(len(stocks))
                if isinstance(stocks, list) and len(stocks) > 1:
                    for stock_name in stocks_name:
                        res = get_stock_state(stock_name)
                        if type(res) == str:
                            update.message.reply_text(res)
                        else:
                            update.message.reply_text('Уточни что вы имели ввиду:', reply_markup=res)
                            logger.info("add")
                            return "add"
                else:
                    stock = stocks
                    logger.info("stock")
                    logger.info(stock)
                    favorite = user.get_favorite_stock(stock.get('name'))
                    if favorite:
                        update.message.reply_text("Инструмент " + str(stock.get('name')) + " уже в избранном")
                    else:
                        user.add_favorite(stock)
                        user.save()
                        update.message.reply_text("Инструмент " + str(stock.get('name')) + " добавлен в избранное")

            else:
                pass

        elif "удалить" in msg or "убрать" in msg:
            filter_words = ["избранного", "удалить", "из", "убрать"]
            stocks_name = msg.split(" ")
            stocks_name = list(filter(lambda word: word not in filter_words, stocks_name))
            stocks = get_stock_by_msg(stocks_name)
            if stocks:
                if isinstance(stocks, list) and len(stocks) > 1:
                    for stock_name in stocks_name:
                        res = get_stock_state(stock_name)
                        if type(res) == str:
                            update.message.reply_text(res)
                        else:
                            update.message.reply_text('Уточни что вы имели ввиду:', reply_markup=res)
                            logger.info("delete")
                            return "delete"
                else:
                    stock = stocks
                    if user.del_favorite_stock(stock.get('name')):
                        user.save()
                        update.message.reply_text("Инструмент " + str(stock.get('name')) + " удалён из избранного")
                    else:
                        update.message.reply_text("Инструмента " + str(stock.get('name')) + " нет в избранном")

        elif "избранное" in msg or "избранного" in msg:
            if user.empty_favorites():
                update.message.reply_text("Избранное пусто")
            else:
                for stock in user.get_favorites():
                    res = get_stock_state(stock["name"])
                    update.message.reply_text(res)
        elif "очистить" in msg:
            user.clear_favorites()
            user.save()
            update.message.reply_text("Избранное очищено")
    elif "изменения" in msg:
        user = User(str(update.effective_user.id))
    else:
        res = get_stock_state(msg)
        if type(res) == str:
            update.message.reply_text(res)
        else:
            update.message.reply_text('Уточни что вы имели ввиду:', reply_markup=res)
    return "main"


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
            stocks = []
            for stock in _stock['stocks']:
                stock = stock.to_dict()
                candles = broker.get_profit_stat(stock, {'days': 1, 'hours': 18}, interval='day')
                stock['price'] = candles[0].c
                broker.set_candles(stock, {'days': 365, 'hours': 0}, interval='day')
                best_price = broker.get_best_current_price()[-1]
                stock['best_price'] = best_price
                stocks.append(stock)
            return stocks
    else:
        return False


def stock_back_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    res = get_stock_state(query.data)

    query.edit_message_text(res)

    return "main"


def stock_add_back_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    stock = query.data
    user = User(str(update.effective_user.id))
    favorite = user.get_favorite_stock(stock)
    if favorite:
        query.edit_message_text("Инструмент " + str(stock) + " уже в избранном")
    else:
        stock = check_stock(stock)
        user.add_favorite(stock)
        user.save()
        query.edit_message_text("Инструмент " + str(stock.get('name')) + " добавлен в избранное")

    return "main"


def stock_delete_back_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    stock = query.data
    user = User(str(update.effective_user.id))
    if user.del_favorite_stock(stock):
        user.save()
        query.edit_message_text("Инструмент " + str(stock) + " удалён из избранного")
    else:
        query.edit_message_text("Инструмента " + str(stock) + " нет в избранном")

    return "main"


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
            res_text = stock.get('name') + "\n\n" + \
                       "Current price: " + str(broker.candles[-1].c) + "\n\n" + \
                       "Best price: " + str(round(best_price, 2)) + "\n\n" + \
                       "Profit: " + str(round(round(best_price, 2) - broker.candles[-1].c, 2)) + " (" + str(
                round(((round(best_price, 2) / broker.candles[-1].c) - 1) * 100, 2)) + "%)"
            return res_text
        elif "stocks" in _stock:
            names = [stock.to_dict().get('name') for stock in _stock['stocks']]
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
    dispatcher.add_handler(CommandHandler("help", help_command))
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.text & ~Filters.command, main_handler)],
        states={
            "main": [
                CallbackQueryHandler(stock_back_handler),
                MessageHandler(Filters.text & ~Filters.command, main_handler)
            ],
            "add": [
                CallbackQueryHandler(stock_add_back_handler)
            ],
            "delete": [
                CallbackQueryHandler(stock_delete_back_handler)
            ],
        },
        fallbacks=[CommandHandler("start", start)]
    )
    dispatcher.add_handler(conv_handler)

    # dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, main_handler))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
