from __future__ import division

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt

import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da

import pandas as pd


def simulate(startdate, enddate, symbols, allocations):
    # We need closing prices so the timestamp should be hours=16.
    dt_timeofday = dt.timedelta(hours=16)

    # Get a list of trading days between the start and the end.
    ldt_timestamps = du.getNYSEdays(startdate, enddate, dt_timeofday)

    # Creating an object of the dataaccess class with Yahoo as the source.
    c_dataobj = da.DataAccess('Yahoo')

    # Keys to be read from the data, it is good to read everything in one go.
    ls_keys = ['close']

    # Reading the data, now d_data is a dictionary with the keys above.
    # Timestamps and symbols are the ones that were specified before.
    data = c_dataobj.get_data(ldt_timestamps, symbols, ls_keys)[0]

    returns = tsu.returnize1(data)

    previous_day = None

    for row in data.iterrows():
        day = row[0]
        series = row[1]
        if previous_day is None:
            for symbol in symbols:
                index = symbols.index(symbol)
                allocation = allocations[index]
                series[symbol] = allocation
        else:
            daily_returns = returns.loc[day]
            for (symbol, price) in series.iteritems():
                series[symbol] = previous_day[symbol] * daily_returns[symbol]

        previous_day = series

    daily_sum = data.apply(lambda row : row[0] + row[1] + row[2] + row[3], 1)

    tsu.returnize0(daily_sum)

    stats = daily_sum.describe()

    std_dr = stats['std']
    mean_dr = stats['mean']
    sharpe = tsu.get_sharpe_ratio(daily_sum.values)

    cumulative_return = 1
    for value in daily_sum:
        value += 1
        cumulative_return = cumulative_return * value

    return std_dr, mean_dr, sharpe, cumulative_return

def calculate_cumulative_return(values):
    result = 1
    for value in values:
        value += 1
        result = result * value

    return result


def optimize(startdate, enddate, symbols):

    percentages = map(lambda v : v / 10, range(11))

    best_sharpe = 0;
    best_allocation = None;

    for stock1 in percentages:
        for stock2 in percentages:
            for stock3 in percentages:
                for stock4 in percentages:
                    if stock1 + stock2 + stock3 + stock4 == 1:
                        allocation = [stock1, stock2, stock3, stock4]
                        vol, daily_ret, sharpe, cum_ret = simulate(startdate, enddate, symbols, allocation)
                        if sharpe > best_sharpe:
                            best_allocation = allocation
                            best_sharpe = sharpe

    return best_allocation


def main():
    startdate = dt.datetime(2011, 1, 1)
    enddate = dt.datetime(2011, 12, 31)
    symbols = ['AAPL', 'GOOG', 'IBM', 'MSFT']

    allocation = optimize(startdate, enddate, symbols)

    vol, daily_ret, sharpe, cum_ret = simulate(startdate, enddate, symbols, allocation)

    print 'Start Date: ' + str(startdate)
    print 'End Date: ' + str(enddate)
    print 'Symbols: ' + str(symbols)

    print 'Sharpe Ratio: ' + str(sharpe)
    print 'Volatility (stdev of daily returns): ' + str(vol)
    print 'Average Daily Return: ' + str(daily_ret)
    print 'Cumulative Return: ' + str(cum_ret)
    print 'Allocation: ' + str(allocation)

if __name__ == '__main__':
    main()