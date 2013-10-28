from __future__ import division
import datetime as dt

import numpy as np
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.DataAccess as da
import QSTK.qstkstudy.EventProfiler as ep
import copy


def find_events(ls_symbols, d_data):
    df_close = d_data['close']

    # Creating an empty dataframe
    df_events = copy.deepcopy(df_close)
    df_events = df_events * np.NAN

    # Time stamps for the event range
    ldt_timestamps = df_close.index

    for s_sym in ls_symbols:
        for i in range(1, len(ldt_timestamps)):

            f_symprice_today = df_close[s_sym].ix[ldt_timestamps[i]]
            f_symprice_yest = df_close[s_sym].ix[ldt_timestamps[i - 1]]

            if f_symprice_today < 7.00 and f_symprice_yest >= 7.00:
                df_events[s_sym].ix[ldt_timestamps[i]] = 1

    return df_events


if __name__ == '__main__':
    dt_start = dt.datetime(2008, 1, 1)
    dt_end = dt.datetime(2009, 12, 31)
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt.timedelta(hours=16))

    dataobj = da.DataAccess('Yahoo')
    ls_symbols = dataobj.get_symbols_from_list('sp5002012')
    # ls_symbols = ls_symbols[:25]
    ls_symbols.append('SPY')

    ls_keys = ['actual_close']

    print "Reading Data"

    ldf_data = dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))

    d_data['close'] = d_data['actual_close']

    d_data['close'] = d_data['close'].fillna(method='ffill')
    d_data['close'] = d_data['close'].fillna(method='bfill')
    d_data['close'] = d_data['close'].fillna(1.0)

    print "Finding Events"

    df_events = find_events(ls_symbols, d_data)

    print "Number of raw events " + str(df_events.sum(0).sum(0))

    print "Creating Study"

    ep.eventprofiler(df_events, d_data, i_lookback=20, i_lookforward=20,
                s_filename='MyEventStudy.pdf', b_market_neutral=True, b_errorbars=True,
                s_market_sym='SPY')
    print "Done"
