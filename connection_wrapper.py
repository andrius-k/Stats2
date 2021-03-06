import http.client
import logging
import os
import json


class ConnectionWrapper():
    """
    Wrapper class to re-use existing connection
    """
    def __init__(self, host):
        self.connection = None
        self.connection_attempts = 3
        self.host_url = host.replace('https://', '').replace('http://', '')
        self.cert_file = os.getenv('USERCRT', None)
        self.key_file = os.getenv('USERKEY', None)
        self.logger = logging.getLogger('logger')

    def init_connection(self, url):
        if self.cert_file is None or self.key_file is None:
            raise Exception('Missing USERCRT or USERKEY environment variables')
            return None

        return http.client.HTTPSConnection(url,
                                           port=443,
                                           cert_file=self.cert_file,
                                           key_file=self.key_file)

    def refresh_connection(self, url):
        self.logger.info('Refreshing connection')
        self.connection = self.init_connection(url)

    def api(self, method, url, data):
        if not self.connection:
            self.refresh_connection(self.host_url)

        url = url.replace('#', '%23')
        # this way saves time for creating connection per every request
        for i in range(self.connection_attempts):
            try:
                self.connection.request(method, url, json.dumps(data) if data else None, headers={"Accept": "application/json"})
                response = self.connection.getresponse()
                if response.status != 200:
                    logger = logging.getLogger('logger')
                    logger.info("Problems (%d) with [%s] %s: %s" % (response.status, method, url, response.read()))
                    return None

                return response.read()
            # except http.client.BadStatusLine:
            #     raise RuntimeError('Something is really wrong')
            except Exception as ex:
                self.logger.error('Exception while doing [%s] to %s: %s' % (method, url, str(ex)))
                # most likely connection terminated
                self.refresh_connection(self.host_url)

        self.logger.error('Connection wrapper failed after %d attempts' % (self.__MAX_CONNECTION_ATTEMPTS))
        return None
