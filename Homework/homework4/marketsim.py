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


def read_orders(filename):
    orders = pd.read_csv(filename, header=None)

    orders.columns = ['year', 'month', 'day', 'symbol', 'order', 'amount', 'nan']

    dates = orders.apply(lambda row: dt.date(year=row['year'], month=row['month'], day=row['day']), 1)

    orders['date'] = dates

    del orders['year']
    del orders['month']
    del orders['day']
    del orders['nan']

    orders = orders.sort(['date'], ascending=[1])

    orders = orders.set_index('date')

    return orders

def get_start_date(orders):
    return orders.iloc[0].name

def get_end_date(orders):
    return orders.iloc[len (orders.index) - 1].name

def get_symbols(orders):
    return list(set(orders['symbol'].values))

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

def calculate_cash(orders, market_data, initial_amount):
    cash = pd.DataFrame(index=market_data.index)
    cash['amount'] = initial_amount

    for order in orders.iterrows():
        order_day_at16 = dt.datetime.combine(order[0], dt.time()) + dt.timedelta(hours=16)
        order_symbol = order[1]['symbol']
        price = market_data.ix[order_day_at16][order_symbol]
        amount = order[1]['amount']
        value = price * amount

        if (order[1]['order']) == 'Buy':
            value = value * -1

        add_amount_starting_on_day(cash, value, order_day_at16)

    return cash

def add_amount_starting_on_day(cash, amount, start_day):
    for day in cash.iterrows():
        if day[0] >= start_day:
            day[1]['amount'] += amount

def calculate_portfolio(orders, market_data):
    portfolio = pd.DataFrame(index=market_data.index)

    portfolio['amount'] = 0

    holdings = {}

    for day in market_data.iterrows():
        date = day[0].date()

        if date in orders.index:
            order = orders.ix[date]

            if isinstance(order, pd.Series):
                symbol = order['symbol']
                amount = order['amount']
                type = order['order']
                if type == 'Sell':
                    amount = amount * -1

                if not symbol in holdings:
                    holdings[symbol] = 0

                holdings[symbol] += amount

            else:
                for single_order in order.iterrows():
                    symbol = single_order[1]['symbol']
                    amount = single_order[1]['amount']
                    type = single_order[1]['order']
                    if type == 'Sell':
                        amount = amount * -1

                    if not symbol in holdings:
                        holdings[symbol] = 0

                    holdings[symbol] += amount

        # Do the real work
        portfolio_value = 0
        for symbol in holdings:
            amount = holdings[symbol]
            stock_value = day[1][symbol] * amount
            portfolio_value += stock_value

        portfolio.ix[day[0]]['amount'] = portfolio_value

    return portfolio

def add_portfolio_to_cash(portfolio, cash):
    portfolio_plus_cash = pd.DataFrame(index=portfolio.index)

    portfolio_plus_cash['amount'] = 0

    for day in portfolio.iterrows():
        portfolio_amount = day[1]['amount']
        cash_amount = cash.ix[day[0]]['amount']

        portfolio_plus_cash.ix[day[0]] = portfolio_amount + cash_amount

    return portfolio_plus_cash

def plot(portfolio_plus_cash):
    plt.clf()
    plt.plot(portfolio_plus_cash.index, portfolio_plus_cash['amount'])
    plt.legend('$')
    plt.ylabel('Portfolio Value')
    plt.xlabel('Date')
    plt.savefig('plot.pdf', format='pdf')


def calculate_ratios(portfolio_plus_cash, column_name):

    total_return = portfolio_plus_cash.iloc[len (portfolio_plus_cash.index) - 1][column_name] / portfolio_plus_cash.iloc[0][column_name]

    returns = tsu.returnize0(portfolio_plus_cash)

    stats = returns.describe()

    sharpe_ratio = tsu.get_sharpe_ratio(returns.values)[0]
    standard_deviation = stats.ix['std'][column_name]
    average_daily_return = stats.ix['mean'][column_name]

    return total_return, sharpe_ratio, standard_deviation, average_daily_return


def get_amount_on(dataframe, date):
    return dataframe.ix[date]['amount']

def process_orders():
    orders = read_orders('orders.csv')
    print 'Read ORDERS: ' + '\n' + str(orders) + '\n'

    start_date = get_start_date(orders)
    print 'Start date: ' + '\n' + str(start_date) + '\n'

    end_date = get_end_date(orders)
    print 'End date: ' + '\n' + str(end_date) + '\n'

    symbols = get_symbols(orders)
    print 'Symbols: ' + '\n' + str(symbols) + '\n'

    market_data = read_market_data(start_date, end_date, symbols)
    print 'Market Data (excerpt): ' + '\n' + str(market_data[0: 10]) + '\n'

    cash = calculate_cash(orders, market_data, 50000)
    print 'Cash (excerpt): ' + '\n' + str(cash[0: 10]) + '\n'

    portfolio = calculate_portfolio(orders, market_data)
    print 'Portfolio (excerpt): ' + '\n' + str(portfolio[0: 10]) + '\n'

    portfolio_plus_cash = add_portfolio_to_cash(portfolio, cash)
    print 'Portfolio plus cash: ' + '\n' + str(portfolio_plus_cash[0: 10]) + '\n'

    plot(portfolio_plus_cash)

    print '\n' + 'Portfolio Performance'

    total_return, sharpe_ratio, standard_deviation, average_daily_return = calculate_ratios(portfolio_plus_cash, 'amount')
    print 'Sharpe Ratio: ' + str(sharpe_ratio)
    print 'Total return: ' + str(total_return)
    print 'Standard deviation of daily returns: ' + str(standard_deviation)
    print 'Average daily return: ' + str(average_daily_return)

    print  '\n' + 'SPX Performance'

    spx_data = read_market_data(start_date, end_date, ['$SPX'])
    total_return, sharpe_ratio, standard_deviation, average_daily_return = calculate_ratios(spx_data, '$SPX')
    print 'Sharpe Ratio: ' + str(sharpe_ratio)
    print 'Total return: ' + str(total_return)
    print 'Standard deviation of daily returns: ' + str(standard_deviation)
    print 'Average daily return: ' + str(average_daily_return)
    print '\n'

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

            if f_symprice_today < 10.00 and f_symprice_yest >= 10.00:
                df_events[s_sym].ix[ldt_timestamps[i]] = 1

    return df_events

def process_events():
    dt_start = dt.datetime(2008, 1, 1)
    dt_end = dt.datetime(2009, 12, 31)
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt.timedelta(hours=16))

    dataobj = da.DataAccess('Yahoo')
    ls_symbols = dataobj.get_symbols_from_list('sp5002012')

    # Limit number of stocks for testing
    # ls_symbols = ls_symbols[:15]

    # ls_symbols.append('SPY')

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

    print "Writing orders.txt"

    with open('orders.csv', 'w') as orders_file:
        dt_last_day = dt.datetime(2009, 12, 31)

        for event_row in df_events.iterrows():
            index = 0
            for column in df_events.columns:
                if not math.isnan(event_row[1][index]):
                    values = []
                    values.append(event_row[0].year)
                    values.append(event_row[0].month)
                    values.append(event_row[0].day)
                    values.append(column)
                    values.append('Buy')
                    values.append(100)

                    csv_row = ','.join(str(v) for v in values)
                    csv_row = csv_row + ',' + '\n'

                    orders_file.write(csv_row)

                    sell_date = du.getNYSEoffset(event_row[0], 5)
                    if sell_date > dt_last_day:
                        sell_date = dt_last_day

                    values = []
                    values.append(sell_date.year)
                    values.append(sell_date.month)
                    values.append(sell_date.day)
                    values.append(column)
                    values.append('Sell')
                    values.append(100)

                    csv_row = ','.join(str(v) for v in values)
                    csv_row = csv_row + ',' + '\n'

                    orders_file.write(csv_row)

                index = index + 1

    print "Done"

def main():
    process_events()

    process_orders()


if __name__ == '__main__':
    main()