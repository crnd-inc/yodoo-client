import requests
import six

from odoo_rpc_client import Client
from odoo_rpc_client.exceptions import LoginException

from .common import (
    TestOdooInfrastructureClient,
    change_expire,
)


class TestClientAuth(TestOdooInfrastructureClient):

    def setUp(self):
        self._url = self.create_url('/saas/client/auth/')
        self._data = {
            'token_hash': self._hash_token,
            'ttl': 300,
            'db': self._client.dbname
        }

    def test_01_controller_odoo_infrastructure_auth(self):
        # test correct request
        response = requests.post(self._url, data=self._data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data['token_password'], six.string_types)
        self.assertIsInstance(data['token_user'], six.string_types)
        self.assertIsInstance(data['expire'], six.string_types)
        self.assertIsInstance(data['temp_url'], six.string_types)
        self.assertIsInstance(data['token_temp'], six.string_types)

    def test_02_controller_odoo_infrastructure_auth(self):
        # test incorrect request with bad token_hash
        data = dict(self._data, token_hash='abracadabra')

        response = requests.post(self._url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_03_controller_odoo_infrastructure_auth(self):
        # test incorrect request with bad db_name
        data = dict(self._data, db='abracadabra')

        response = requests.post(self._url, data=data)
        self.assertEqual(response.status_code, 440)

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


class TestClientAuthAdminLogin(TestOdooInfrastructureClient):

    def setUp(self):
        self._data = {
            'token_hash': self._hash_token,
            'ttl': 300,
            'db': self._client.dbname
        }
        self._url = self.create_url('/saas/client/auth/')
        self.response = requests.post(self._url, data=self._data)
        self.data = self.response.json()
        self.url = self.create_url(self.data["temp_url"])

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


class TestClientVersionInfo(TestOdooInfrastructureClient):

    def setUp(self):
        self.incorrect_response_keys = {'error'}
        self._version_url = self.create_url('/saas/client/version_info')
        self._version_data = {
            'token_hash': self._hash_token,
        }

    def test_01_controller_odoo_infrastructure_saas_client_version(self):
        # test correct request
        response = requests.post(self._version_url, self._version_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data['odoo_version'], six.string_types)
        self.assertIsInstance(data['odoo_version_info'], list)
        self.assertIsInstance(data['odoo_serie'], six.string_types)
        self.assertIsInstance(data['saas_client_version'], six.string_types)
        self.assertIsInstance(data['saas_client_serie'], six.string_types)
        self.assertIsInstance(data['saas_client_api_version'], int)
        self.assertIsInstance(data['features_enabled'], dict)
        features_enabled = data['features_enabled']
        self.assertIsInstance(features_enabled['admin_access_url'], bool)
        self.assertIsInstance(
            features_enabled['admin_access_credentials'], bool)

    def test_02_controller_odoo_infrastructure_saas_client_version(self):
        # test incorrect request with bad token_hash
        data = dict(self._version_data, token_hash='abracadabra')

        response = requests.post(self._version_url, data)
        self.assertEqual(response.status_code, 403)
