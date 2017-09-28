import copy
import logging
import requests
import threading
import time
import urllib.parse
from typing import Callable


class BrokerAdapter(threading.Thread):
    '''
    EXANTE API broker adapter
    '''

    def __init__(self, callback: Callable[[dict], None], account: str,
                 interval: int, base_url: str,
                 auth: requests.auth.HTTPBasicAuth):
        '''
        :param callback: OSR callback function
        :param account: account ID
        :param interval: interval for OSR in seconds
        :param base_url: base API url
        :param auth: basic auth object
        '''
        super(BrokerAdapter, self).__init__()
        self.__lock = threading.Lock()
        self.daemon = True
        self.__interval = interval

        self.__url = urllib.parse.urljoin(base_url, 'trade/1.0/orders')

        self.__account = account
        self.__auth = auth
        self.__logger = logging.getLogger('http-broker')

        self.__callback = callback
        self.__orders = dict()

    @property
    def orders(self) -> list:
        '''
        get stored order IDs
        :return: list of IDs
        '''
        with self.__lock:
            return copy.deepcopy(list(self.__orders.keys()))

    @property
    def state(self, order_id: str) -> dict:
        '''
        stored order state
        :param order_id: order ID
        :return: order state dictionary as is in API
        '''
        with self.__lock:
            return copy.deepcopy(self.__orders.get(order_id, dict()))

    def order(self, order_id: str) -> dict:
        '''
        get order information from API
        :param order_id: order ID
        :return: order state dictionary as is in API
        '''
        response = requests.get(urllib.parse.urljoin(
            '{}/'.format(self.__url), order_id), auth=self.__auth)
        if response.ok:
            return response.json()
        return dict()

    def place_limit(self, instrument: str, side: str, quantity: int,
                    price: float, duration: str='good_till_cancel') -> dict:
        '''
        :param instrument: instrument ID
        :param side: order side, buy or sell
        :param quantity: order quantity
        :param price: limit price
        :param duration: order duration
        '''
        response = requests.post(self.__url, json={
            'account': self.__account,
            'duration': duration,
            'instrument': instrument,
            'orderType': 'limit',
            'quantity': quantity,
            'limitPrice': price,
            'side': side
        }, auth=self.__auth)
        try:
            return response.json()['id']
        except KeyError:
            self.__logger.warning('Could not place order', exc_info=True)
            return response.json()
        except Exception:
            self.__logger.warning(
                'Unexpected error occurs while placing order', exc_info=True)
            return dict()

    def run(self) -> None:
        '''
        order status watcher
        '''
        while True:
            updated = list()
            with self.__lock:
                for order_id in self.__orders:
                    state = self.order(order_id)
                    # check if order was changed
                    if state == self.__orders[order_id]:
                        continue
                    self.__logger.info('Order {} state was changed'.format(
                        order_id))
                    self.__orders[order_id] = state
                    updated.append(copy.deepcopy(state))
            # call callback function
            self.__callback(updated)
            time.sleep(self.__interval)

    # orders control
    def add_order(self, order_id: str) -> None:
        '''
        add order to watcher
        :param order_id: order ID to watch
        '''
        with self.__lock:
            if order_id in self.__orders:
                return
            self.__orders[order_id] = dict()

    def remove_order(self, order_id: str) -> None:
        '''
        remove order from watcher
        :param order_id: order ID to watch
        '''
        with self.__lock:
            try:
                del self.__orders[order_id]
            except KeyError:
                pass
