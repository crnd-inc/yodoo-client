import string
import hashlib
import logging
import unittest

from os import environ
from random import shuffle
from datetime import datetime, timedelta
from six.moves.urllib.parse import urlunsplit

from odoo_rpc_client import Client
from odoo_rpc_client.exceptions import LoginException

_logger = logging.getLogger(__name__)


def generate_random_string(length):
    letters = list(string.ascii_uppercase +
                   string.ascii_lowercase +
                   string.digits)
    shuffle(letters)
    return ''.join(letters[:length])


def change_expire(expire):
    """Subtracts one hour from expiration:

            :param str expire: string of time with format "%Y-%m-%d %H:%M:%S"
            :return: string of time with format "%Y-%m-%d %H:%M:%S"
            :rtype: str

            For example:
                expire = '2018-07-12 08:07:36'
            returns '2018-07-12 07:07:36'
        """
    return (
        datetime.strptime(expire, "%Y-%m-%d %H:%M:%S") - timedelta(hours=1)
    ).strftime("%Y-%m-%d %H:%M:%S")


class TestOdooInfrastructureClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._odoo_instance_token = environ.get('ODOO_INSTANCE_TOKEN', 'qwerty')
        cls._odoo_host = environ.get('ODOO_HOST', 'localhost')
        cls._odoo_port = environ.get('ODOO_PORT', '8069')
        cls._odoo_admin_pass = environ.get('ODOO_ADMIN_PASS', 'admin')
        cls._odoo_rpc_protocol = 'json-rpc'
        cls._db_name = generate_random_string(10)
        cls._odoo_instance = Client(cls._odoo_host,
                                    port=int(cls._odoo_port),
                                    protocol=cls._odoo_rpc_protocol)
        cls._client = cls._odoo_instance.services.db.create_db(
            'admin', cls._db_name)
        cls._hash_token = hashlib.sha256(
            cls._odoo_instance_token.encode('utf8')).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls._odoo_instance.services.db.drop_db(
            'admin', cls._db_name)

    def create_url(self, query):
        """Creates url from pieces:

            :param str host: host for url
            :param str port: port for url
            :param str query: query for url
            :return: url
            :rtype: str

            For example:
                host = 'localhost'
                port = 8069
                query = 'odoo/infrastructure/auth/'
            returns 'http://localhost:8069/odoo/infrastructure/auth/'
        """
        host_url = ':'.join((self._odoo_host, self._odoo_port))
        return urlunsplit(('http', host_url, query, '', ''))

