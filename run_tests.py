import requests
import hashlib
import string
import unittest

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

    @classmethod
    def tearDownClass(cls):
        cls._odoo_instance.services.db.drop_db('admin', cls._db_name)

    def setUp(self):
        self.data = {
            'odoo_infrastructure_token': self._hash_token,
            'ttl': 300,
            'db': self._client.dbname
        }

    def test_01_controller_odoo_infrastructure_auth(self):
        print('1')

        # test correct request

        response = requests.post(self._url, data=self.data)
        self.assertEqual(response.status_code, 200)

    def test_02_controller_odoo_infrastructure_auth(self):
        print('2')

        # test incorrect request with bad odoo_infrastructure_token

        data = self.data.copy().update({
            'odoo_infrastructure_token': 'abracadabra'
        })

        response = requests.post(self._url, data=data)
        print(response)
        #self.assertEqual(response.status_code, 404)


        #response = requests.post(self._url, data=data)
        #self.assertEqual(response.status_code, 200)
#
        #data.update({
        #    'odoo_infrastructure_token': 'abracadabra'
        #})
#
        #response = requests.post(self._url, data=data)
        #self.assertEqual(response.status_code, 404)
#
        #data.update({
        #    'odoo_infrastructure_token': self._hash_token,
        #    'db': 'abracadabra'
        #})
#
        #response = requests.post(self._url, data=data)
        #self.assertEqual(response.status_code, 404)

def suite():
    _suite = unittest.TestSuite()
    _suite.addTest(TestOdooInfrastructureAuth('test_01_controller_odoo_infrastructure_auth'))
    _suite.addTest(TestOdooInfrastructureAuth('test_02_controller_odoo_infrastructure_auth'))
    return _suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
