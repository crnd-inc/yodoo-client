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

    def tearDown(self):
        self._client['yodoo.client.auth.log'].search_records([]).unlink()
        self._client['ir.config_parameter'].set_param(
            'yodoo_client.yodoo_allow_admin_logins', True)

    def test_01_controller_odoo_infrastructure_saas_auth(self):
        # test correct request
        response = requests.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('"uid": 1,', response.text)

    def test_011_controller_odoo_infrastructure_saas_auth(self):
        # test when remote admin is disabled client db
        self._client['ir.config_parameter'].set_param(
            'yodoo_client.yodoo_allow_admin_logins', False)

        response = requests.get(self.url)
        self.assertEqual(response.status_code, 403)

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
        response = requests.get(self.url)
        self.assertEqual(response.status_code, 200)

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

        self.assertEqual(response.status_code, 403)

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

        self.assertEqual(response.status_code, 403)

    def test_07_controller_odoo_infrastructure_saas_auth(self):
        # check auth true login true password
        cl = Client(host=self._odoo_host,
                    dbname=self._db_name,
                    port=self._odoo_port,
                    user='admin',
                    pwd='admin')
        self.assertEqual(cl.uid, 2)

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

    def test_07_controller_odoo_infrastructure_saas_auth_specific_user(self):
        cl_admin = Client(host=self._odoo_host,
                          dbname=self._db_name,
                          port=self._odoo_port,
                          user='admin',
                          pwd='admin')
        test_r_user = cl_admin['res.users'].create_record({
            'name': 'My test user',
            'login': 'my-test-user',
        })
        response = requests.post(
            self._url,
            data=dict(
                self._data,
                user_uuid='my-user-id',
                user_id=test_r_user.id))
        data = response.json()

        # Check that correct row created in client auth table
        OdooInfrastructureClientAuth = self._client[
            'odoo.infrastructure.client.auth']
        temp_rows = OdooInfrastructureClientAuth.search_records(
            [('token_temp', '=', data['token_temp'])]
        )
        self.assertEqual(len(temp_rows), 1)
        self.assertEqual(temp_rows[0].user_uuid, 'my-user-id')
        self.assertEqual(temp_rows[0].user_id, test_r_user.id)

        # check auth true login true password
        cl = Client(host=self._odoo_host,
                    dbname=self._db_name,
                    port=self._odoo_port,
                    user=data['token_user'],
                    pwd=data['token_password'])
        self.assertEqual(cl.uid, test_r_user.id)

    def test_08_controller_odoo_infrastructure_saas_auth(self):
        # check request if temp record does not exist
        AuthLog = self._client['yodoo.client.auth.log']

        # Install module mail for this test. This is needed to check if user
        # can view partner record.
        self._client['ir.module.module'].search_records(
            [('name', '=', 'mail')]
        ).button_immediate_install()

        session = requests.Session()

        response = session.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.url, self.create_url('/web'))

        response = session.get(
            self.create_url('/mail/view?model=res.partner&res_id=1'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.url.startswith(self.create_url('/web/login')))
        self.assertTrue(
            response.url.startswith(self.create_url('/web#')))

        log_entry = AuthLog.search_records([])
        self.assertEqual(len(log_entry), 1)
        log_entry.action_expire()

        response = session.get(
            self.create_url('/mail/view?model=res.partner&res_id=1'))
        self.assertTrue(
            response.url.startswith(self.create_url('/web/login')),
            "Expected response url starts with '/web/login', got %s" % (
                response.url))

    def test_09_controller_odoo_infrastructure_saas_auth(self):
        AuthLog = self._client['yodoo.client.auth.log']
        ResConfigSettings = self._client['res.config.settings']

        session = requests.Session()

        response = session.get(self.url)
        self.assertEqual(response.status_code, 200)

        log_entry = AuthLog.search_records([])
        self.assertEqual(len(log_entry), 1)

        response = session.get(
            self.create_url('/mail/view?model=res.partner&res_id=1'),
            allow_redirects=True)
        self.assertFalse(
            response.url.startswith(self.create_url('/web/login')))
        self.assertTrue(response.url.startswith(self.create_url('/web#')), "Wrong response url: %s" % response.url)

        # Deny access for remote admins
        self.assertTrue(
            self._client['ir.config_parameter'].get_param(
                'yodoo_client.yodoo_allow_admin_logins'))
        ResConfigSettings.create_record(
            dict(
                ResConfigSettings.default_get(
                    list(ResConfigSettings.columns_info.keys())),
                yodoo_allow_admin_logins=False)
        ).execute()
        self.assertFalse(
            self._client['ir.config_parameter'].get_param(
                'yodoo_client.yodoo_allow_admin_logins'))

        log_entry = AuthLog.search_records([])
        self.assertEqual(len(log_entry), 1)
        self.assertEqual(log_entry[0].login_state, 'expired')

        response = session.get(self.url)
        self.assertEqual(response.status_code, 403)

        response = session.get(
            self.create_url('/mail/view?model=res.partner&res_id=1'))
        self.assertTrue(
            response.url.startswith(self.create_url('/web/login')),
            "Expected response url starts with '/web/login', got %s" % (
                response.url))


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

    def test_02_controller_odoo_infrastructure_saas_client_version(self):
        # test incorrect request with bad token_hash
        data = dict(self._version_data, token_hash='abracadabra')

        response = requests.post(self._version_url, data)
        self.assertEqual(response.status_code, 403)
