import requests

from odoo_rpc_client import Client
from odoo_rpc_client.exceptions import LoginException

from .common import (
    TestOdooInfrastructureClient,
    change_expire,
)


class TestOdooInfrastructureSaasClientDBStatistic(
        TestOdooInfrastructureClient):

    def setUp(self):
        self._db_statistic_url = self.create_url('/saas/client/db/stat')
        self._db_statistic_data = {
            'token_hash': self._hash_token,
            'db': self._client.dbname
        }

    def test_01_controller_odoo_infrastructure_db_statistic(self):
        NoneType = type(None)
        # test correct request
        response = requests.post(
            self._db_statistic_url, self._db_statistic_data)
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['users_internal_count'], 1)
        self.assertEqual(data['users_external_count'], 0)
        self.assertEqual(data['users_total_count'], 1)
        self.assertTrue(isinstance(data['db_storage'], int))
        self.assertTrue(isinstance(data['file_storage'], int))
        self.assertTrue(isinstance(data['login_date'], (str, NoneType)))
        self.assertTrue(
            isinstance(data['login_internal_date'], (str, NoneType)))
        self.assertTrue(isinstance(data['installed_apps_db_count'], int))
        self.assertTrue(isinstance(data['installed_modules_db_count'], int))

    def test_02_controller_odoo_infrastructure_db_statistic(self):
        # test incorrect request with bad token_hash
        data = dict(self._db_statistic_data, token_hash='abracadabra')

        response = requests.post(self._db_statistic_url, data)
        self.assertEqual(response.status_code, 403)

    def test_03_controller_odoo_infrastructure_db_statistic(self):
        # test incorrect request with bad db_name
        data = dict(self._db_statistic_data, db='abracadabra')

        response = requests.post(self._db_statistic_url, data)
        self.assertEqual(response.status_code, 404)


class TestOdooInfrastructureDBModuleInfo(TestOdooInfrastructureClient):
    def setUp(self):
        self._db_info_url = self.create_url('/saas/client/db/module/info')
        self._db_info_data = {
            'token_hash': self._hash_token,
            'db': self._client.dbname
        }

    def test_01_controller_odoo_infrastructure_db_module_info(self):
        NoneType = type(None)
        response = requests.post(
            self._db_info_url, self._db_info_data)
        self.assertEqual(response.status_code, 200)
        modules = response.json()
        for module in modules:
            self.assertTrue(isinstance(module['summary'], str))
            self.assertTrue(isinstance(module['name'], str))
            self.assertTrue(isinstance(module['latest_version'], str))
            self.assertTrue(isinstance(module['application'], bool))
            self.assertTrue(isinstance(module['state'], str))
            self.assertTrue(
                isinstance(module['published_version'], (str, NoneType)))

    def test_02_controller_odoo_infrastructure_db_module_info(self):
        # test incorrect request with bad token_hash
        data = dict(self._db_info_data, token_hash='abracadabra')

        response = requests.post(self._db_info_url, data)
        self.assertEqual(response.status_code, 403)

    def test_03_controller_odoo_infrastructure_db_module_info(self):
        # test incorrect request with bad db_name
        data = dict(self._db_info_data, db='abracadabra')

        response = requests.post(self._db_info_url, data)
        self.assertEqual(response.status_code, 404)


class TestOdooInfrastructureDBUsersInfo(TestOdooInfrastructureClient):
    def setUp(self):
        self._user_info_url = self.create_url('/saas/client/db/users/info')
        self._user_info_data = {
            'token_hash': self._hash_token,
            'db': self._client.dbname
        }

    def test_01_controller_odoo_infrastructure_db_users_info(self):
        response = requests.post(
            self._user_info_url, self._user_info_data)
        self.assertEqual(response.status_code, 200)
        users = response.json()
        for user in users:
            self.assertTrue(isinstance(user['id'], int))
            self.assertTrue(isinstance(user['login'], str))
            self.assertTrue(isinstance(user['partner_id'], int))
            self.assertTrue(isinstance(user['share'], bool))
            self.assertTrue(isinstance(user['write_uid'], int))

    def test_02_controller_odoo_infrastructure_db_users_info(self):
        # test incorrect request with bad token_hash
        data = dict(self._user_info_data, token_hash='abracadabra')

        response = requests.post(self._user_info_url, data)
        self.assertEqual(response.status_code, 403)

    def test_03_controller_odoo_infrastructure_db_users_info(self):
        # test incorrect request with bad db_name
        data = dict(self._user_info_data, db='abracadabra')

        response = requests.post(self._user_info_url, data)
        self.assertEqual(response.status_code, 404)

    def test_04_db_configure_basu_url_ok(self):
        response = requests.post(
            self.create_url('/saas/client/db/configure/base_url'),
            data={
                'token_hash': self._hash_token,
                'db': self._client.dbname,
                'base_url': "http://test.test",
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self._client['ir.config_parameter'].get_param(
                'web.base.url'),
            'http://test.test')
        self.assertEqual(
            self._client['ir.config_parameter'].get_param(
                'mail.catchall.domain'),
            'test.test')

    def test_05_db_configure_basu_url_fail_no_param(self):
        response = requests.post(
            self.create_url('/saas/client/db/configure/base_url'),
            data={
                'token_hash': self._hash_token,
                'db': self._client.dbname,
                'base_url': "",
            })
        self.assertEqual(response.status_code, 400)


class TestOdooInfrastructureCreateDB(TestOdooInfrastructureClient):
    def setUp(self):
        self._create_db_url = self.create_url(
            '/saas/client/db/create')
        self._create_db_data = {
            'token_hash': self._hash_token,
            'dbname': 'test_db',
            'user_login': 'test_user',
            'user_password': 'test_password',
        }

    def test_01_controller_odoo_infrastructure_instance_create_db(self):
        response = requests.post(
            self._create_db_url, self._create_db_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._odoo_instance.services.db.db_exist('test_db'))
        self._odoo_instance.services.db.drop_db(
            self._odoo_admin_pass, 'test_db')
        self.assertFalse(self._odoo_instance.services.db.db_exist('test_db'))

    def test_02_controller_odoo_infrastructure_instance_create_db(self):
        # test incorrect request with bad token_hash
        data = dict(self._create_db_data, token_hash='abracadabra')

        response = requests.post(self._create_db_url, data)
        self.assertEqual(response.status_code, 403)

    def test_03_controller_odoo_infrastructure_instance_create_db(self):
        # test request with existing dbname
        data = dict(self._create_db_data, dbname=self._client.dbname)

        response = requests.post(self._create_db_url, data)
        self.assertEqual(response.status_code, 409)

    def test_04_controller_odoo_infrastructure_instance_create_db(self):
        # test request without dbname
        data = dict(self._create_db_data, dbname=None)

        response = requests.post(self._create_db_url, data)
        self.assertEqual(response.status_code, 400)
