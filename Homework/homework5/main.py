from __future__ import division
import datetime as dt

import pandas as pd
import matplotlib.pyplot as plt
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da
import copy
import numpy as np
import math


def read_market_data(start_date, end_date, symbols):
    # We need closing prices so the timestamp should be hours=16.
    dt_timeofday = dt.timedelta(hours=16)

    # Get a list of trading days between the start and the end.
    ldt_timestamps = du.getNYSEdays(start_date, end_date, dt_timeofday)

    # Creating an object of the dataaccess class with Yahoo as the source.
    c_dataobj = da.DataAccess('Yahoo')

    # Keys to be read from the data, it is good to read everything in one go.
    ls_keys = ['close']

    # Reading the data, now d_data is a dictionary with the keys above.
    # Timestamps and symbols are the ones that were specified before.
    data = c_dataobj.get_data(ldt_timestamps, symbols, ls_keys)[0]

    return data


def plot(market_data, symbol):
    plt.clf()

    fig = plt.figure(1)

    plt.subplot(2, 1, 1)
    plt.plot(market_data.index, market_data['price'])
    plt.plot(market_data.index, market_data['moving_average'])
    plt.plot(market_data.index, market_data['upper_band'])
    plt.plot(market_data.index, market_data['lower_band'])
    plt.fill_between(market_data.index, market_data['lower_band'], market_data['upper_band'], facecolor='lightgray' )
    plt.legend([ 'Price', 'Moving average', 'Upper band', 'Lower band' ], loc=9, prop={ 'size':6 })
    plt.title(symbol)
    plt.ylabel('Price')

    plt.subplot(2, 1, 2)
    plt.plot(market_data.index, market_data['bollinger_value'])
    plt.fill_between(market_data.index, -1, 1, facecolor='lightgray' )
    plt.ylabel('Bollinger Index')

    fig.autofmt_xdate()

    plt.savefig('plot.pdf', format='pdf')

def main():

    dt_start = dt.datetime(2010, 1, 1)
    dt_end = dt.datetime(2010, 12, 31)
    symbol = 'MSFT'
    ls_symbols = [symbol]
    number_of_periods = 20

    market_data = read_market_data(dt_start, dt_end, ls_symbols)

    market_data.rename(columns={symbol: 'price'}, inplace=True)

    market_data['moving_average'] = pd.rolling_mean(market_data, window=number_of_periods)['price']

    market_data['moving_std'] = pd.rolling_std(market_data, window=number_of_periods)['price']

    market_data['upper_band'] = market_data['moving_average'] + market_data['moving_std']

    market_data['lower_band'] = market_data['moving_average'] - market_data['moving_std']

    market_data['bollinger_value'] = (market_data['price'] - market_data['moving_average']) / market_data['moving_std']

    print 'Data (excerpt): ' + '\n' + str(market_data[0: 30]) + '\n'

    plot(market_data, symbol)

    datetime = dt.datetime.strptime('May 21 2010  4:00PM', '%b %d %Y %I:%M%p')
    value = market_data.ix[datetime]['bollinger_value']
    print 'Bollinger value on a date: ' + '\n' + str(value) + '\n'

if __name__ == '__main__':
    main()