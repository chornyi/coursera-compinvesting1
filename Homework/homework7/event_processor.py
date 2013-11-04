from __future__ import division
import datetime as dt
import copy

import pandas as pd
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.DataAccess as da
import numpy as np


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

def get_values(dt_start, dt_end, symbol, number_of_periods):
    ls_symbols = [symbol]
    market_data = read_market_data(dt_start, dt_end, ls_symbols)
    market_data['moving_average'] = pd.rolling_mean(market_data, window=number_of_periods)[symbol]
    market_data['moving_std'] = pd.rolling_std(market_data, window=number_of_periods)[symbol]
    market_data['bollinger_value'] = (market_data[symbol] - market_data['moving_average']) / market_data['moving_std']

    market_data = market_data.drop('moving_average', 1)
    market_data = market_data.drop('moving_std', 1)

    market_data.rename(columns={symbol: 'close'}, inplace=True)

    return market_data

def find_events(ls_symbols, d_data):
    # Creating an empty dataframe
    df_events = copy.deepcopy(d_data)
    df_events = df_events * np.NAN

    # Time stamps for the event range
    ldt_timestamps = d_data.index

    for s_sym in ls_symbols:
        for i in range(1, len(ldt_timestamps)):
            f_bollinger_value_today = d_data[s_sym].ix[ldt_timestamps[i]]
            f_bollinger_value_today_market = d_data['SPY'].ix[ldt_timestamps[i]]
            f_bollinger_value_yest = d_data[s_sym].ix[ldt_timestamps[i - 1]]

            if f_bollinger_value_today < -2.00 and f_bollinger_value_yest >= -2.00 and f_bollinger_value_today_market >= 1.20:
                df_events[s_sym].ix[ldt_timestamps[i]] = 1

    return df_events

def get_events(dt_start, dt_end, ls_symbols):
    number_of_periods = 20

    bollinger_values = None

    for symbol in ls_symbols:
        values = get_values(dt_start, dt_end, symbol, number_of_periods)
        if bollinger_values is None:
            bollinger_values = copy.deepcopy(values)
            bollinger_values = bollinger_values * np.NAN
            bollinger_values = bollinger_values.drop('close', 1)
            bollinger_values = bollinger_values.drop('bollinger_value', 1)

        bollinger_values[symbol] = values['bollinger_value']

    bollinger_values['SPY'] = get_values(dt_start, dt_end, 'SPY', number_of_periods)['bollinger_value']

    print 'Bollinger Values (excerpt): ' + '\n' + str(bollinger_values[0: 30]) + '\n'

    print "Finding Events"

    df_events = find_events(ls_symbols, bollinger_values)

    print "Number of raw events " + str(df_events.sum(0).sum(0))

    return df_events