import logging
from decimal import *
# project
import broker_adapter
import feed_adapter

class GridBrokerWorker(object):

    def __init__(self, account, interval, base_url, application, token):
        self.__account = account
        self.__interval = interval
        self.__base_url = base_url
        self.__application = application
        self.__token = token

        self.__logger = logging.getLogger('http-broker')

        # init objects
        self.__broker = broker_adapter.BrokerAdapter(self.grid_callback, self.__account,
                                                     self.__interval, self.__base_url,
                                                     self.__application, self.__token)
        self.__broker.start()

        # pnl
        self.__cash = self.dec(0)
        self.__position = self.dec(0)

    # fck the float
    @staticmethod
    def dec(value):
        return Decimal(str(value))

    def __process_order(self, order):
        state = order['orderState']
        if state['status'] == 'filled':
            filled = sum(self.dec(fill['quantity']) for fill in state['fills'])
            avg_price = sum(self.dec(fill['price']) for fill in state['fills']) / filled
            self.__logger.info('Order {} filled with average price {}'.format(order['id'], avg_price))
            # update cash/pnl/whatever
            change = (-1 if order['orderParameters']['side'] == 'sell' else 1) * filled
            self.__position += change
            self.__cash +=  avg_price * change
            self.__logger.info('Cash {}, position {}'.format(self.__cash, self.__position))
        elif state['status'] in ('cancelled', 'rejected'):
            self.__logger.info('Order {} {}'.format(order['id'], state['status']))
        # process updates
        self.__broker.remove_order(order['id'])

    def grid_callback(self, orders):
        for order in orders:
            self.__logger.debug('Received order update {}'.format(order))
            if order['orderState']['status'] in ('created', 'pending', 'accepted', 'placing'):
                continue
            # calculate
            self.__process_order(order)

    def run(self, instrument, quantity, grid):
        feed = feed_adapter.FeedAdapter(instrument, self.__base_url,
                                        self.__application, self.__token)
        # subscribe on quotes
        old_mid = None
        for quote in feed.run():
            mid = (self.dec(quote['bid']) + self.dec(quote['ask'])) / self.dec(2)
            # first run
            if old_mid is None:
                old_mid = mid
                continue
            # logic
            if abs(old_mid - mid) < grid:
                continue
            side = 'sell' if mid - old_mid > 0.0 else 'buy'
            self.__logger.debug('Grid triggered at {} {} (previous {})'.format(mid, side, old_mid))
            order_id = self.__broker.place_limit(instrument, side, quantity, float(mid))

            # process order
            if order_id is None:
                self.__logger.error('Unexpected error')
                continue
            # error occurs
            if not isinstance(order_id, str):
                self.__logger.error('Unexpected error: {}'.format(order_id))
                continue
            # we placed order
            self.__logger.info('New order {}'.format(order_id))
            self.__broker.add_order(order_id)
            old_mid = mid
