import copy
import json
import logging
import requests
import threading
import time
import urllib.parse
from socket import error as SocketError

class FeedAdapter(threading.Thread):

    __headers = {'accept': 'application/x-json-stream'}

    def __init__(self, instrument, base_url, application, token):
        super(FeedAdapter, self).__init__()
        self.__lock = threading.Lock()
        self.daemon = True

        self.__url = base_url

        self.__auth = requests.auth.HTTPBasicAuth(application, token)
        self.__logger = logging.getLogger('http-broker')
        self.__should_run = True
        self.__stream_url = '{}/md/1.0/feed/{}'.format(self.__url,
                                                       urllib.parse.quote_plus(instrument))

        self.__quotes = dict()

    @property
    def quotes(self):
        with self.__lock:
            return copy.deepcopy(self.__quotes)

    def __get_stream(self):
        response = requests.get(self.__stream_url, auth=self.__auth,
                                stream=True, timeout=60, headers=self.__headers)
        return response.iter_lines(chunk_size=1)

    def run(self):
        while self.__should_run:
            try:
                for item in self.__get_stream():
                    # exit on no actions
                    if not self.__should_run:
                        break
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

    def stop(self):
        with self.__lock:
            self.__should_run = False
