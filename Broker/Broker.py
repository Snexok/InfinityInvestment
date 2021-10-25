# Python Modules
import json
from datetime import datetime, timedelta
from statistics import mean

# tinkoff open API
# pip install -i https://test.pypi.org/simple/ --extra-index-url=https://pypi.org/simple/ tinkoff-invest-openapi-client
from openapi_client import openapi

def get_config():
    file = open("config/config.config").read()
    config = eval(file)
    return config

periods_interval = {
    'd': ({'days': 1, 'hours': 0}, 'hour'),
    'w': ({'days': 0, 'hours': 7 * 24}, 'day'),
    'm': ({'days': 30, 'hours': 0}, 'day'),
    'y': ({'days': 365, 'hours': 0}, 'day'),
}

class Broker:
    """docstring"""

    def __init__(self):
        config = get_config()
        token = config['tokens']['tinkoff']
        client = openapi.sandbox_api_client(token)
        client.sandbox.sandbox_register_post()
        client.sandbox.sandbox_clear_post()
        client.sandbox.sandbox_currencies_balance_post(
            sandbox_set_currency_balance_request={"currency": "USD", "balance": 1000})
        self.client = client

    def set_candles(self, stock=None, period=None, interval=None):
        self.candles = self.get_profit_stat(stock, period, interval)

    def get_profit_stat(self, stock, period, interval='day'):
        candles = self.get_market_candles(stock, self.get_last_date(days=period['days'], hours=period['hours']),
                                          self.get_last_date(), interval)
        # Костыль для кейса с выходными
        if interval == 'hour' and period['days'] == 1:
            if len(candles) < 24:
                period['hours'] = 72
                candles = self.get_market_candles(stock,
                                                  self.get_last_date(days=period['days'], hours=period['hours']),
                                                  self.get_last_date(), interval)[-24:]
        return candles

    def get_market_candles(self, stock, start_date, end_date, interval, save=False):
        candles = self.client.market.market_candles_get(stock['figi'], start_date, end_date, interval)
        if save:
            f = open("Candles_" + stock['figi'] + "_" + stock['name'] + ".json", "a")
            f.write(str(candles))
            f.close()
        return candles.payload.candles

    def get_last_date(self, days=0, hours=0):
        date = str((datetime.now() - timedelta(days=days, hours=hours)).strftime("%Y-%m-%dT%H:%M:%S.%f")) + '+03:00'
        return date

    # render
    def get_dygraphs_data(self):
        candles_close = [candle.c for candle in self.candles]
        candles_dates = [candle.time.strftime("%Y-%m-%d %H:%M:%S") for candle in self.candles]
        avg_line = self.avg_line(candles_close)
        dygraphs = ''.join(
            [candles_dates[i] + "," + str(candles_close[i]) + "," + str(avg_line[i]) + "\\n" for i in
             range(len(candles_close))])
        return dygraphs

    # Статистика
    def avg_line(self, _data):
        data = _data.copy()
        _max = max(data)
        _min = min(data)
        _len = len(data)
        _step = (_max - _min) / _len
        return [(_min + _min * 0.115 + _step * i * 0.45) for i in range(_len)]

    def get_best_current_price(self):
        candles_close = [candle.c for candle in self.candles]
        avg_line = self.avg_line(candles_close)
        return avg_line[:-1]

    def get_procent_changes(self):
        data = [candle.c for candle in self.candles]
        data_open = data[0]
        data_close = data[(len(data) - 1)]
        data_max, data_min = (data_close, data_open) if data_close > data_open else (data_open, data_close)
        # Разница в процентах между началом и концом периода
        procent_changes = data_max / data_min * 100 - 100
        procent_changes = procent_changes if data_close > data_open else -procent_changes
        procent_changes = "{:.2f}".format(procent_changes)
        return procent_changes

    def avg_candles_indicators(self, candles):
        cand_stats = {"c": mean([candle.c for candle in candles]),
                      "o": mean([candle.o for candle in candles]),
                      "h": mean([candle.h for candle in candles]),
                      "l": mean([candle.l for candle in candles])}
        return cand_stats

    def get_month_avg_profit(self, stock):
        candles = self.get_profit_stat(stock, {'days': 30, 'hours': 0}, interval='day')
        return self.avg_candles_indicators(candles)['c']

    # Получение списка акций
    def get_stock(self, name):
        name = str(name).lower()

        all_market_stocks = self.get_all_market_stocks().payload.instruments

        stocks = [stock for stock in all_market_stocks if name == stock.name.lower()]

        if len(stocks) == 0:
            stocks = [stock for stock in all_market_stocks if
                      name in stock.name.lower() or name in stock.ticker.lower()]

        stocks = sorted(stocks, key=lambda item: item.name.lower().index(name) if name in item.name.lower() else 0)

        if len(stocks) == 0:
            return False
        elif len(stocks) == 1:
            return {"stock": stocks[0]}
        else:
            return {"stocks": stocks}

    def get_all_market_stocks(self, save=False):
        stocks = self.client.market.market_stocks_get()
        if save:
            f = open("stocks.json", "a")
            f.write(str(stocks))
            f.close()
        return stocks

    def load_best_stocks(self):
        f = open('BestStocks.json', 'r')
        stocks = json.load(f)
        return stocks
