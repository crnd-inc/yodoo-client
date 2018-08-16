import hashlib
import string
import unittest
import logging

from datetime import datetime, timedelta
from random import shuffle
from os import environ
from six.moves.urllib.parse import urlunsplit

import requests

from odoo_rpc_client import Client
from odoo_rpc_client.exceptions import LoginException

_logger = logging.getLogger(__name__)


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


class TestOdooInfrastructureClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._odoo_instance_token = environ.get('ODOO_INSTANCE_TOKEN', 'qwerty')
        cls._odoo_host = environ.get('ODOO_HOST', 'localhost')
        cls._odoo_port = environ.get('ODOO_PORT', '11069')
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
        cls._version_url = create_url(
            cls._odoo_host,
            cls._odoo_port,
            '/saas/client/version_info'
        )
        cls._version_data = {
            'token_hash': cls._hash_token,
        }
        cls._db_statistic_url = create_url(
            cls._odoo_host,
            cls._odoo_port,
            '/saas/client/db/stat'
        )
        cls._server_slow_statistic_url = create_url(
            cls._odoo_host,
            cls._odoo_port,
            '/saas/client/server/slow/stat'
        )
        cls._server_fast_statistic_url = create_url(
            cls._odoo_host,
            cls._odoo_port,
            '/saas/client/server/fast/stat'
        )

    @classmethod
    def tearDownClass(cls):
        cls._odoo_instance.services.db.drop_db(
            'admin', cls._db_name)


class TestOdooInfrastructureAuthAuth(TestOdooInfrastructureClient):
    def setUp(self):
        self.correct_response_keys = {
            'token_password',
            'token_user',
            'expire',
            'temp_url',
            'token_temp'
        }

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

    def test_03_controller_odoo_infrastructure_auth(self):
        # test incorrect request with bad db_name
        data = dict(self._data, db='abracadabra')

        response = requests.post(self._url, data=data)
        self.assertEqual(response.status_code, 404)

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


class TestOdooInfrastructureAuthSaasAuth(TestOdooInfrastructureClient):
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

    def test_07_controller_odoo_infrastructure_saas_auth(self):
        # check auth true login true password
        cl = Client(host=self._odoo_host,
                    dbname=self._db_name,
                    port=self._odoo_port,
                    user='admin',
                    pwd='admin')
        self.assertEqual(cl.uid, 1)

        # check auth true login false password
        cl = Client(host=self._odoo_host,
                    dbname=self._db_name,
                    port=self._odoo_port,
                    user='admin',
                    pwd='abracadabra')
        with self.assertRaises(LoginException) as le:
            cl.uid
        self.assertIsInstance(le.exception, LoginException)

        # check auth false login true password
        cl = Client(host=self._odoo_host,
                    dbname=self._db_name,
                    port=self._odoo_port,
                    user='abracadabra',
                    pwd='admin')
        with self.assertRaises(LoginException) as le:
            cl.uid
        self.assertIsInstance(le.exception, LoginException)

        # check auth false login false password
        cl = Client(host=self._odoo_host,
                    dbname=self._db_name,
                    port=self._odoo_port,
                    user='abracadabra',
                    pwd='abracadabra')
        with self.assertRaises(LoginException) as le:
            cl.uid
        self.assertIsInstance(le.exception, LoginException)


class TestOdooInfrastructureSaasClientVersionInfo(TestOdooInfrastructureClient):
    def setUp(self):
        self.correct_response_keys = {
            'odoo_version',
            'odoo_version_info',
            'odoo_serie',
            'saas_client_version',
            'saas_client_serie',
            'saas_client_api_version',
            'features_enabled'
        }
        self.correct_features_enabled_keys = {
            'admin_access_url',
            'admin_access_credentials'
        }
        self.incorrect_response_keys = {'error'}

    def test_01_controller_odoo_infrastructure_saas_client_version(self):
        # test correct request
        response = requests.post(self._version_url, self._version_data)
        self.assertEqual(
            set(response.json().keys()),
            self.correct_response_keys
        )

        self.assertEqual(
            set(response.json()['features_enabled'].keys()),
            self.correct_features_enabled_keys
        )

        self.assertEqual(response.status_code, 200)

    def test_02_controller_odoo_infrastructure_saas_client_version(self):
        # test incorrect request with bad token_hash
        data = dict(self._version_data, token_hash='abracadabra')

        response = requests.post(self._version_url, data)
        self.assertEqual(response.status_code, 403)


class TestOdooInfrastructureSaasClientDBStatistic(TestOdooInfrastructureClient):
    def setUp(self):
        self.correct_response_keys = {
            'db_storage',
            'file_storage',
            'total_users',
            'internal_users',
            'external_users'
        }

    def test_01_controller_odoo_infrastructure_db_statistic(self):
        # test correct request
        response = requests.post(self._db_statistic_url, self._data)
        data = response.json()
        self.assertEqual(
            set(data.keys()),
            self.correct_response_keys
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['internal_users'], 1)
        self.assertEqual(data['external_users'], 0)
        self.assertEqual(data['total_users'], 1)

    def test_02_controller_odoo_infrastructure_db_statistic(self):
        # test incorrect request with bad token_hash
        data = dict(self._data, token_hash='abracadabra')

        response = requests.post(self._db_statistic_url, data)
        self.assertEqual(response.status_code, 403)

    def test_03_controller_odoo_infrastructure_db_statistic(self):
        # test incorrect request with bad db_name
        data = dict(self._data, db='abracadabra')

        response = requests.post(self._db_statistic_url, data)
        self.assertEqual(response.status_code, 404)


class TestOdooInfrastructureSaasClientServerSlowStatistic(
        TestOdooInfrastructureClient):
    def setUp(self):
        self.correct_response_keys = {
            'used_disc_space',
            'free_disc_space',
            'total_disc_space',
            'os_name',
            'os_machine',
            'os_version',
            'os_node',
            'database_count'
        }

    def test_01_controller_odoo_infrastructure_server_slow_statistic(self):
        # test correct request
        response = requests.post(self._server_slow_statistic_url, self._data)
        self.assertEqual(
            set(response.json().keys()),
            self.correct_response_keys
        )


class TestOdooInfrastructureSaasClientServerFastStatistic(
        TestOdooInfrastructureClient):
    def setUp(self):
        self.correct_response_keys = {
            'cpu_load_average',
            'cpu_us',
            'cpu_sy',
            'cpu_id',
            'cpu_ni',
            'cpu_wa',
            'cpu_hi',
            'cpu_si',
            'cpu_st',
            'mem_total',
            'mem_free',
            'mem_used',
            'mem_buffers',
            'mem_available',
            'swap_total',
            'swap_free',
            'swap_used'
        }

    def test_01_controller_odoo_infrastructure_server_fast_statistic(self):
        # test correct request
        response = requests.post(self._server_fast_statistic_url, self._data)
        print(response.json())
        self.assertEqual(
            set(response.json().keys()),
            self.correct_response_keys
        )


if __name__ == '__main__':
    unittest.main()
