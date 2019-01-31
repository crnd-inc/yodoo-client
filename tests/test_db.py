import six
import requests

from .common import TestOdooInfrastructureClient


class TestClientDBStatistic(TestOdooInfrastructureClient):

    def setUp(self):
        self._db_statistic_url = self.create_url('/saas/client/db/stat')
        self._db_statistic_data = {
            'token_hash': self._hash_token,
            'db': self._client.dbname
        }

    def test_01_controller_db_statistic(self):
        NoneType = type(None)
        # test correct request
        response = requests.post(
            self._db_statistic_url, self._db_statistic_data)
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['users_internal_count'], 1)
        self.assertEqual(data['users_external_count'], 0)
        self.assertEqual(data['users_total_count'], 1)
        self.assertIsInstance(data['db_storage'], int)
        self.assertIsInstance(data['file_storage'], int)
        self.assertIsInstance(
            data['login_date'], (str, NoneType, bool))
        self.assertIsInstance(
            data['login_internal_date'], (str, NoneType, bool))
        self.assertIsInstance(data['installed_apps_db_count'], int)
        self.assertIsInstance(data['installed_modules_db_count'], int)

    def test_02_controller_db_statistic(self):
        # test incorrect request with bad token_hash
        data = dict(self._db_statistic_data, token_hash='abracadabra')

        response = requests.post(self._db_statistic_url, data)
        self.assertEqual(response.status_code, 403)

    def test_03_controller_db_statistic(self):
        # test incorrect request with bad db_name
        data = dict(self._db_statistic_data, db='abracadabra')

        response = requests.post(self._db_statistic_url, data)
        self.assertEqual(response.status_code, 440)


class TestDBModuleInfo(TestOdooInfrastructureClient):
    def setUp(self):
        self._db_info_url = self.create_url('/saas/client/db/module/info')
        self._db_info_data = {
            'token_hash': self._hash_token,
            'db': self._client.dbname
        }

    def test_01_controller_db_module_info(self):
        NoneType = type(None)
        response = requests.post(
            self._db_info_url, self._db_info_data)
        self.assertEqual(response.status_code, 200)
        modules = response.json()
        for module in modules:
            self.assertIsInstance(module['summary'], six.string_types)
            self.assertIsInstance(module['name'], six.string_types)
            self.assertIsInstance(module['latest_version'], six.string_types)
            self.assertIsInstance(module['application'], bool)
            self.assertIsInstance(module['state'], six.string_types)
            self.assertIsInstance(
                module['published_version'], (str, NoneType))

    def test_02_controller_db_module_info(self):
        # test incorrect request with bad token_hash
        data = dict(self._db_info_data, token_hash='abracadabra')

        response = requests.post(self._db_info_url, data)
        self.assertEqual(response.status_code, 403)

    def test_03_controller_db_module_info(self):
        # test incorrect request with bad db_name
        data = dict(self._db_info_data, db='abracadabra')

        response = requests.post(self._db_info_url, data)
        self.assertEqual(response.status_code, 440)


class TestDBUsersInfo(TestOdooInfrastructureClient):
    def setUp(self):
        self._user_info_url = self.create_url('/saas/client/db/users/info')
        self._user_info_data = {
            'token_hash': self._hash_token,
            'db': self._client.dbname
        }

    def test_01_controller_db_users_info(self):
        response = requests.post(
            self._user_info_url, self._user_info_data)
        self.assertEqual(response.status_code, 200)
        users = response.json()
        for user in users:
            self.assertIsInstance(user['id'], int)
            self.assertIsInstance(user['login'], six.string_types)
            self.assertIsInstance(user['partner_id'], int)
            self.assertIsInstance(user['share'], bool)
            self.assertIsInstance(user['write_uid'], int)

    def test_02_controller_db_users_info(self):
        # test incorrect request with bad token_hash
        data = dict(self._user_info_data, token_hash='abracadabra')

        response = requests.post(self._user_info_url, data)
        self.assertEqual(response.status_code, 403)

    def test_03_controller_db_users_info(self):
        # test incorrect request with bad db_name
        data = dict(self._user_info_data, db='abracadabra')

        response = requests.post(self._user_info_url, data)
        self.assertEqual(response.status_code, 440)

    def test_04_db_configure_base_url_ok(self):
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

    def test_05_db_configure_base_url_fail_no_param(self):
        response = requests.post(
            self.create_url('/saas/client/db/configure/base_url'),
            data={
                'token_hash': self._hash_token,
                'db': self._client.dbname,
                'base_url': "",
            })
        self.assertEqual(response.status_code, 400)
