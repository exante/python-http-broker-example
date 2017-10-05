#
# Copyright (c) 2017 EXANTE
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#

import decimal
import logging
import requests
# project
from libs import broker_adapter
from libs import feed_adapter


class GridBrokerWorker(object):
    '''
    main worker class
    '''

    def __init__(self, account: str, interval: str, base_url: str,
                 application: str, token: str):
        '''
        :param account: account ID
        :param interval: order status request interval in seconds
        :param base_url: base API url
        :param application: application ID
        :param token: auth token
        '''
        self.__account = account
        self.__interval = interval
        self.__base_url = base_url
        self.__auth = requests.auth.HTTPBasicAuth(application, token)

        self.__logger = logging.getLogger('http-broker')

        # init objects
        self.__broker = broker_adapter.BrokerAdapter(
            self.grid_callback, self.__account, self.__interval,
            self.__base_url, self.__auth)
        self.__broker.start()

        # pnl
        self.__cash = self.dec(0)
        self.__position = self.dec(0)

    # fck the float
    @staticmethod
    def dec(value) -> decimal.Decimal:
        '''
        number to decimal convertions
        :param value: value convertable to decimal
        :return: coverted value
        '''
        return decimal.Decimal(str(value))

    def __process_order(self, order: dict) -> None:
        '''
        process terminated order
        :param order: api order object
        '''
        state = order['orderState']
        params = order['orderParameters']
        if state['status'] == 'filled':
            filled = sum(self.dec(fill['quantity']) for fill in state['fills'])
            avg_price = sum(
                self.dec(fill['price']) for fill in state['fills']) / filled
            self.__logger.info('Order {} filled with average price {}'.format(
                order['id'], avg_price))
            # update cash/pnl/whatever
            change = (-1 if params['side'] == 'sell' else 1) * filled
            self.__position += change
            self.__cash += avg_price * change
            self.__logger.info('Cash {}, position {}'.format(
                self.__cash, self.__position))
        elif state['status'] in ('cancelled', 'rejected'):
            self.__logger.info('Order {} {}'.format(
                order['id'], state['status']))
        # remove from watcher
        self.__broker.remove_order(order['id'])

    def grid_callback(self, orders: list) -> None:
        '''
        callback method to process order updates
        :param orders: list of orders objects
        '''
        for order in orders:
            self.__logger.debug('Received order update {}'.format(order))
            if order['orderState']['status'] in ('created', 'pending',
                                                 'accepted', 'placing'):
                continue
            # calculate
            self.__process_order(order)

    def run(self, instrument, quantity, grid) -> None:
        '''
        main cycle
        :param instrument: instrument ID
        :param quantity: orders quantity
        :param grid: tick grid size
        '''
        feed = feed_adapter.FeedAdapter(instrument, self.__base_url,
                                        self.__auth)
        # subscribe on quotes
        old_mid = None
        for quote in feed.run():
            mid = (self.dec(quote['bid']) + self.dec(quote['ask'])) / 2
            # first run
            if old_mid is None:
                old_mid = mid
                continue
            # main logic
            if abs(old_mid - mid) < grid:
                continue
            side = 'sell' if mid - old_mid > 0 else 'buy'
            self.__logger.debug('Grid triggered at {} {} (previous {})'.format(
                mid, side, old_mid))
            order_id = self.__broker.place_limit(
                instrument, side, str(quantity), str(mid))

            # process order
            if order_id is None:
                self.__logger.error('Unexpected error')
                continue
            # server error
            if not isinstance(order_id, str):
                self.__logger.error('Unexpected error: {}'.format(order_id))
                continue
            # we placed order
            self.__logger.info('New limit order {} ({} {} @ {})'.format(
                order_id, side, quantity, mid))
            self.__broker.add_order(order_id)
            old_mid = mid
