from __future__ import division
import datetime as dt

import QSTK.qstkutil.DataAccess as da
import event_processor
import marketsim


def main():
    dt_start = dt.datetime(2008, 1, 1)
    dt_end = dt.datetime(2009, 12, 31)
    dataobj = da.DataAccess('Yahoo')
    ls_symbols = dataobj.get_symbols_from_list('sp5002012')
    #ls_symbols = ls_symbols[:25]

    events = event_processor.get_events(dt_start, dt_end, ls_symbols)

    marketsim.process_events(events, 5, 100, dt_end)
    marketsim.process_orders(100000)


if __name__ == '__main__':
    main()