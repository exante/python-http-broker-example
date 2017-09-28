import copy
import json
import logging
import requests
import threading
import time
import urllib.parse
from socket import error as SocketError


class FeedAdapter(threading.Thread):
    '''
    EXANTE API feed adapter
    '''

    __headers = {'accept': 'application/x-json-stream'}

    def __init__(self, instrument: str, base_url: str,
                 auth: requests.auth.HTTPBasicAuth):
        '''
        :param instrument: instrument ID
        :param base_url: base API url
        :param auth: basic auth object
        '''
        super(FeedAdapter, self).__init__()
        self.__lock = threading.Lock()
        self.daemon = True

        self.__url = base_url

        self.__auth = auth
        self.__logger = logging.getLogger('http-broker')
        self.__stream_url = '{}/md/1.0/feed/{}'.format(
            self.__url, urllib.parse.quote_plus(instrument))

        self.__quotes = dict()

    @property
    def quotes(self) -> dict:
        '''
        get last received quotes
        :return: quotes as is in API
        '''
        with self.__lock:
            return copy.deepcopy(self.__quotes)

    def __get_stream(self) -> iter:
        '''
        get raw quotes stream
        :return: response line iterator
        '''
        response = requests.get(
            self.__stream_url, auth=self.__auth, stream=True, timeout=60,
            headers=self.__headers)
        return response.iter_lines(chunk_size=1)

    def run(self) -> None:
        '''
        main cycle
        '''
        while True:
            try:
                for item in self.__get_stream():
                    # work block
                    data = json.loads(item.decode('utf8'))
                    self.__logger.debug('Received data {}'.format(data))
                    if 'event' in data:
                        continue
                    with self.__lock:
                        self.__quotes = data
                        yield copy.deepcopy(data)
            except requests.exceptions.Timeout:
                self.__logger.warning('Timeout reached', exc_info=True)
            except requests.exceptions.ChunkedEncodingError:
                self.__logger.warning('Chunk read failed', exc_info=True)
            except requests.ConnectionError:
                self.__logger.warning('Connection error', exc_info=True)
            except SocketError:
                self.__logger.warning('Socket error', exc_info=True)
            time.sleep(60)
