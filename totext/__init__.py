import os
import requests
from flask import Flask

class MiniADSFlask(Flask):
    """ADS Flask worker; used by all the microservice applications.
    This class should be instantiated outside app.py
    """

    def __init__(self, app_name, *args, **kwargs):
        """
        :param: app_name - string, name of the application (can be anything)
        :keyword: local_config - dict, configuration that should be applied
            over the default config (that is loaded from config.py and local_config.py)
        """
        Flask.__init__(self, app_name, *args, **kwargs)

        # HTTP connection pool
        # - The maximum number of retries each connection should attempt: this
        #   applies only to failed DNS lookups, socket connections and connection timeouts,
        #   never to requests where data has made it to the server. By default,
        #   requests does not retry failed connections.
        # http://docs.python-requests.org/en/latest/api/?highlight=max_retries#requests.adapters.HTTPAdapter
        self.client = requests.Session()
        http_adapter = requests.adapters.HTTPAdapter(pool_connections=int(os.environ.get('REQUESTS_POOL_CONNECTIONS', 10)), pool_maxsize=int(os.environ.get('REQUESTS_POOL_MAXSIZE', 1000)), max_retries=int(os.environ.get('REQUESTS_POOL_RETRIES', 3)), pool_block=False)
        self.client.mount('http://', http_adapter)

app = MiniADSFlask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'any random string')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'you-will-never-guess')

from totext import routes
