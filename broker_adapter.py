import copy
import logging
import requests
import threading
import time
import urllib.parse

class BrokerAdapter(threading.Thread):

    def __init__(self, callback, account, interval, base_url, application,
                 token):
        super(BrokerAdapter, self).__init__()
        self.__lock = threading.Lock()
        self.daemon = True
        self.__interval = interval

        self.__url = urllib.parse.urljoin(base_url, 'trade/1.0/orders')

        self.__account = account
        self.__auth = requests.auth.HTTPBasicAuth(application, token)
        self.__logger = logging.getLogger('http-broker')

        self.__callback = callback
        self.__orders = dict()

    def state(self, order_id):
        with self.__lock:
            return copy.deepcopy(self.__orders.get(order_id, dict()))

    def order(self, order_id):
        response = requests.get(urllib.parse.urljoin(
            '{}/'.format(self.__url), order_id), auth=self.__auth)
        if response.ok:
            return response.json()
        return dict()

    def place_limit(self, instrument, side, quantity, price):
        response = requests.post(self.__url, json={
            'account': self.__account,
            'duration': 'good_till_cancel',
            'instrument': instrument,
            'orderType': 'limit',
            'quantity': quantity,
            'limitPrice': price,
            'side': side
        }, auth=self.__auth)
        try:
            return response.json()['id']
        except KeyError:
            return response.json()
        except:
            return None

    def run(self):
        while True:
            updated = list()
            with self.__lock:
                ids = self.__orders.keys()
                for order_id in self.__orders:
                    state = self.order(order_id)
                    # check if order was changed
                    if state == self.__orders[order_id]:
                        continue
                    self.__logger.info('Order {} state was changed'.format(order_id))
                    self.__orders[order_id] = state
                    updated.append(copy.deepcopy(state))
            self.__callback(updated)
            time.sleep(self.__interval)

    # orders control
    def add_order(self, order_id):
        with self.__lock:
            if order_id in self.__orders:
                return
            self.__orders[order_id] = dict()

    def remove_order(self, order_id):
        with self.__lock:
            try:
                del self.__orders[order_id]
            except:
                pass
