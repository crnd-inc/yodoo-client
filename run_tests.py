import requests
import hashlib
import string
import unittest

from datetime import datetime, timedelta
from random import shuffle
from os import environ
from urllib.parse import urlunsplit
from odoo_rpc_client import Client


def generate_random_string(length):
    letters = list(string.ascii_uppercase +
                   string.ascii_lowercase +
                   string.digits)
    shuffle(letters)
    return ''.join(letters[:length])


class TestOdooInfrastructureAuth(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._odoo_instance_token = environ.get('ODOO_INSTANCE_TOKEN', 'qwerty')
        cls._odoo_db_host = environ.get('ODOO_DB_HOST', 'localhost')
        cls._odoo_db_user = environ.get('ODOO_DB_USER', 'odoo')
        cls._odoo_db_password = environ.get('ODOO_DB_PASSWORD', 'odoo')
        cls._odoo_db_port = environ.get('ODOO_DB_PORT', '8069')
        cls._db_name = generate_random_string(10)
        cls._odoo_instance = Client(cls._odoo_db_host)
        cls._client = cls._odoo_instance.services.db.create_db('admin', cls._db_name)
        cls._hash_token = hashlib.sha256(
            cls._odoo_instance_token.encode('utf8')).hexdigest()
        cls._url = urlunsplit(
            ('http',
             ':'.join((cls._odoo_db_host, cls._odoo_db_port)),
             '/odoo/infrastructure/auth/',
             '',
             '')
        )
        cls._data = {
            'odoo_infrastructure_token': cls._hash_token,
            'ttl': 300,
            'db': cls._client.dbname
        }

    @classmethod
    def tearDownClass(cls):
        cls._odoo_instance.services.db.drop_db('admin', cls._db_name)


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

        # test incorrect request with bad odoo_infrastructure_token
        data = self._data.copy()
        data.update({
            'odoo_infrastructure_token': 'abracadabra'
        })

        response = requests.post(self._url, data=data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            set(response.json().keys()),
            self.incorrect_response_keys
        )

    def test_03_controller_odoo_infrastructure_auth(self):

        # test incorrect request with bad db_name
        data = self._data.copy()
        data.update({
            'db': 'abracadabra'
        })

        response = requests.post(self._url, data=data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            set(response.json().keys()),
            self.incorrect_response_keys
        )

    def test_04_controller_odoo_infrastructure_auth(self):

        # test scheduler remove row after expire
        response = requests.post(self._url, data=self._data)
        OdooInfrastructureClientAuth = self._client['odoo.infrastructure.client.auth']

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
        temp_rows[0].write({'expire':
                                (datetime.strptime(
                                    temp_rows[0]['expire'], "%Y-%m-%d %H:%M:%S") -
                                 timedelta(hours=1)
                                 ).strftime("%Y-%m-%d %H:%M:%S")})

        # run scheduler
        OdooInfrastructureClientAuth.scheduler_cleanup_expired_entries()

        # check if record does not exist
        temp_rows = OdooInfrastructureClientAuth.search_records(
            [('token_temp', '=', response.json()['token_temp'])]
        )
        self.assertEqual(len(temp_rows), 0)


class TestOdooInfrastructureAuthSaasAuth(TestOdooInfrastructureAuth):
    def setUp(self):
        pass






def suite():
    _suite = unittest.TestSuite()
    _suite.addTest(TestOdooInfrastructureAuthAuth('test_01_controller_odoo_infrastructure_auth'))
    _suite.addTest(TestOdooInfrastructureAuthAuth('test_02_controller_odoo_infrastructure_auth'))
    _suite.addTest(TestOdooInfrastructureAuthAuth('test_03_controller_odoo_infrastructure_auth'))
    _suite.addTest(TestOdooInfrastructureAuthAuth('test_04_controller_odoo_infrastructure_auth'))
    return _suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
