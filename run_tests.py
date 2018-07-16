import hashlib
import string
import unittest

from datetime import datetime, timedelta
from random import shuffle
from os import environ
from six.moves.urllib.parse import urlunsplit

import requests

from odoo_rpc_client import Client


def generate_random_string(length):
    letters = list(string.ascii_uppercase +
                   string.ascii_lowercase +
                   string.digits)
    shuffle(letters)
    return ''.join(letters[:length])


def create_url(host, port, query):
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
    return urlunsplit(('http', ':'.join((host, port)), query, '', ''))


def change_expire(expire):
    """Subtracts one hour from expiration:

            :param str expire: string of time with format "%Y-%m-%d %H:%M:%S"
            :return: string of time with format "%Y-%m-%d %H:%M:%S"
            :rtype: str

            For example:
                expire = '2018-07-12 08:07:36'
            returns '2018-07-12 07:07:36'
        """
    return (datetime.strptime(
        expire, "%Y-%m-%d %H:%M:%S") -
            timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")


class TestOdooInfrastructureAuth(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._odoo_instance_token = environ.get('ODOO_INSTANCE_TOKEN', 'qwerty')
        cls._odoo_host = environ.get('ODOO_HOST', 'localhost')
        cls._odoo_port = environ.get('ODOO_PORT', '8069')
        cls._odoo_rpc_protocol = 'json-rpc'
        cls._db_name = generate_random_string(10)
        cls._odoo_instance = Client(cls._odoo_host,
                                    port=int(cls._odoo_port),
                                    protocol=cls._odoo_rpc_protocol)
        cls._client = cls._odoo_instance.services.db.create_db(
            'admin', cls._db_name)
        cls._hash_token = hashlib.sha256(
            cls._odoo_instance_token.encode('utf8')).hexdigest()
        cls._data = {
            'token_hash': cls._hash_token,
            'ttl': 300,
            'db': cls._client.dbname
        }
        cls._url = create_url(
            cls._odoo_host,
            cls._odoo_port,
            '/odoo/infrastructure/auth/'
        )

    @classmethod
    def tearDownClass(cls):
        cls._odoo_instance.services.db.drop_db(
            'admin', cls._db_name)


class TestOdooInfrastructureAuthAuth(TestOdooInfrastructureAuth):
    def setUp(self):
        self.correct_response_keys = {
            'token_password',
            'token_user',
            'expire',
            'temp_url',
            'token_temp'
        }
        self.incorrect_response_keys = {'error'}

    def test_01_controller_odoo_infrastructure_auth(self):
        # test correct request
        response = requests.post(self._url, data=self._data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.json().keys()),
            self.correct_response_keys
        )

    def test_02_controller_odoo_infrastructure_auth(self):
        # test incorrect request with bad token_hash
        data = dict(self._data, token_hash='abracadabra')

        response = requests.post(self._url, data=data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            set(response.json().keys()),
            self.incorrect_response_keys
        )

    def test_03_controller_odoo_infrastructure_auth(self):
        # test incorrect request with bad db_name
        data = dict(self._data, db='abracadabra')

        response = requests.post(self._url, data=data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            set(response.json().keys()),
            self.incorrect_response_keys
        )

    def test_04_controller_odoo_infrastructure_auth(self):
        # test scheduler remove row after expire
        response = requests.post(self._url, data=self._data)
        OdooInfrastructureClientAuth = self._client[
            'odoo.infrastructure.client.auth']

        # check if record exist
        temp_rows = OdooInfrastructureClientAuth.search_records(
            [('token_temp', '=', response.json()['token_temp'])]
        )
        self.assertEqual(len(temp_rows), 1)

        # run scheduler
        OdooInfrastructureClientAuth.scheduler_cleanup_expired_entries()

        # check if record exist still
        temp_rows = OdooInfrastructureClientAuth.search_records(
            [('token_temp', '=', response.json()['token_temp'])]
        )
        self.assertEqual(len(temp_rows), 1)

        # change expire
        temp_rows[0].write({
            'expire': change_expire(temp_rows[0]['expire'])
        })

        # run scheduler
        OdooInfrastructureClientAuth.scheduler_cleanup_expired_entries()

        # check if record does not exist
        temp_rows = OdooInfrastructureClientAuth.search_records(
            [('token_temp', '=', response.json()['token_temp'])]
        )
        self.assertEqual(len(temp_rows), 0)


class TestOdooInfrastructureAuthSaasAuth(TestOdooInfrastructureAuth):
    def setUp(self):
        self.response = requests.post(self._url, data=self._data)
        self.data = self.response.json()
        self.url = create_url(
            self._odoo_host,
            self._odoo_port,
            self.data["temp_url"]
        )

    def test_01_controller_odoo_infrastructure_saas_auth(self):
        # test correct request
        response = requests.get(self.url)
        response_data = response.text.split('\'')

        self.assertEqual(response.status_code, 200)
        self.assertIn('/web', response_data)

    def test_02_controller_odoo_infrastructure_saas_auth(self):
        # test incorrect request (url no base64)
        response = requests.get(self.url[:-1])

        self.assertEqual(response.status_code, 400)

    def test_03_controller_odoo_infrastructure_saas_auth(self):
        # test incorrect request (bad url in base64)
        response = requests.get(self.url[:-1] + 'A')

        self.assertEqual(response.status_code, 403)

    def test_04_controller_odoo_infrastructure_saas_auth(self):
        # check temp record existing
        OdooInfrastructureClientAuth = self._client[
            'odoo.infrastructure.client.auth']
        temp_rows = OdooInfrastructureClientAuth.search_records(
            [('token_temp', '=', self.data['token_temp'])]
        )
        self.assertEqual(len(temp_rows), 1)
        # correct request
        requests.get(self.url)
        # check temp record removed
        temp_rows = OdooInfrastructureClientAuth.search_records(
            [('token_temp', '=', self.data['token_temp'])]
        )
        self.assertEqual(len(temp_rows), 0)

    def test_05_controller_odoo_infrastructure_saas_auth(self):
        # check request if temp record does not exist
        OdooInfrastructureClientAuth = self._client[
            'odoo.infrastructure.client.auth']
        temp_rows = OdooInfrastructureClientAuth.search_records(
            [('token_temp', '=', self.data['token_temp'])]
        )
        self.assertEqual(len(temp_rows), 1)

        temp_rows[0].unlink()
        # correct request
        response = requests.get(self.url)

        self.assertEqual(response.status_code, 404)

    def test_06_controller_odoo_infrastructure_saas_auth(self):
        # check request if expire
        OdooInfrastructureClientAuth = self._client[
            'odoo.infrastructure.client.auth']
        temp_rows = OdooInfrastructureClientAuth.search_records(
            [('token_temp', '=', self.data['token_temp'])]
        )
        self.assertEqual(len(temp_rows), 1)

        temp_rows[0].write({
            'expire': change_expire(temp_rows[0]['expire'])
        })

        response = requests.get(self.url)

        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
