import six
import json
import requests

from .common import TestOdooInfrastructureClient

ADMIN_USER_ID = 2


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


class TestDBUsersConfigureBasics(TestOdooInfrastructureClient):

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

    def test_10_db_configure_mail(self):
        response = requests.post(
            self.create_url('/saas/client/db/configure/mail'),
            data={
                'token_hash': self._hash_token,
                'db': self._client.dbname,
                'incoming': json.dumps({
                    'host': 'in.test.com',
                    'user': 'in-test-user',
                    'password': 'in-test-password',
                }),
                'outgoing': json.dumps({
                    'host': 'out.test.com',
                    'user': 'out-test-user',
                    'password': 'out-test-password',
                }),
            })
        self.assertEqual(response.status_code, 200)

        incoming_srv = self._client.ref('yodoo_client.yodoo_incoming_mail')
        self.assertEqual(incoming_srv.name, 'Yodoo Incoming Mail')
        self.assertEqual(incoming_srv.type, 'imap')
        self.assertEqual(incoming_srv.is_ssl, True)
        self.assertEqual(incoming_srv.port, 993)
        self.assertEqual(incoming_srv.server, 'in.test.com')
        self.assertEqual(incoming_srv.user, 'in-test-user')
        self.assertEqual(incoming_srv.password, 'in-test-password')
        self.assertEqual(incoming_srv.active, True)
        self.assertEqual(incoming_srv.state, 'draft')

        outgoing_srv = self._client.ref('yodoo_client.yodoo_outgoing_mail')
        self.assertEqual(outgoing_srv.name, 'Yodoo Outgoing Mail')
        self.assertEqual(outgoing_srv.smtp_encryption, 'starttls')
        self.assertEqual(outgoing_srv.smtp_port, 587)
        self.assertEqual(outgoing_srv.smtp_host, 'out.test.com')
        self.assertEqual(outgoing_srv.smtp_user, 'out-test-user')
        self.assertEqual(outgoing_srv.smtp_pass, 'out-test-password')
        self.assertEqual(outgoing_srv.active, True)

        response = requests.post(
            self.create_url('/saas/client/db/configure/mail/delete'),
            data={
                'token_hash': self._hash_token,
                'db': self._client.dbname,
            })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self._client.ref('yodoo_client.yodoo_incoming_mail'))
        self.assertFalse(self._client.ref('yodoo_client.yodoo_outgoing_mail'))

    def test_10_db_configure_mail_fail_test_connection(self):
        response = requests.post(
            self.create_url('/saas/client/db/configure/mail'),
            data={
                'token_hash': self._hash_token,
                'db': self._client.dbname,
                'incoming': json.dumps({
                    'host': 'in.test.com',
                    'user': 'in-test-user',
                    'password': 'in-test-password',
                }),
                'outgoing': json.dumps({
                    'host': 'out.test.com',
                    'user': 'out-test-user',
                    'password': 'out-test-password',
                }),
                'test_and_confirm': True,
            })
        self.assertEqual(response.status_code, 500)

    def test_10_db_configure_mail_delete_unexisting(self):
        response = requests.post(
            self.create_url('/saas/client/db/configure/mail/delete'),
            data={
                'token_hash': self._hash_token,
                'db': self._client.dbname,
            })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self._client.ref('yodoo_client.yodoo_incoming_mail'))
        self.assertFalse(self._client.ref('yodoo_client.yodoo_outgoing_mail'))


class TestDBConfigureDB(TestOdooInfrastructureClient):
    @classmethod
    def setUpClass(cls):
        super(TestDBConfigureDB, cls).setUpClass()
        cls._new_admin_rec = cls._client['res.users'].create({
            'name': 'Test Admin',
            'login': 'test-admin',
            'password': 'test-admin',
            'groups_id': [
                (4, cls._client.ref('base.group_system').id),
            ],
        })
        cls._new_admin_cl = cls._client.login(
            cls._db_name, 'test-admin', 'test-admin')

    def setUp(self):
        super(TestDBConfigureDB, self).setUp()

        self._new_admin_cl['res.users'].write([ADMIN_USER_ID], {
            'login': 'admin',
            'password': 'admin',
        })

    def test_15_db_configure_db_ok(self):
        self.assertEqual(
            self._client['res.users'].browse(ADMIN_USER_ID).login, 'admin')

        response = requests.post(
            self.create_url('/saas/client/db/configure/db'),
            data={
                'token_hash': self._hash_token,
                'db': self._client.dbname,
                'company_website': "http://test.test",
                'company_name': "My Company 42",
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self._new_admin_cl['res.company'].browse(1).website,
            'http://test.test')
        self.assertEqual(
            self._new_admin_cl['res.company'].browse(1).name,
            'My Company 42')

        self.assertEqual(
            self._new_admin_cl['res.users'].browse(ADMIN_USER_ID).login,
            'odoo')

    def test_15_db_configure_db_no_params(self):
        self.assertEqual(
            self._client['res.users'].browse(ADMIN_USER_ID).login, 'admin')

        response = requests.post(
            self.create_url('/saas/client/db/configure/db'),
            data={
                'token_hash': self._hash_token,
                'db': self._client.dbname,
            })
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            self._new_admin_cl['res.users'].browse(ADMIN_USER_ID).login,
            'odoo')

    def test_20_db_configure_update_admin_ok(self):
        self.assertEqual(
            self._client['res.users'].browse(ADMIN_USER_ID).login, 'admin')

        response = requests.post(
            self.create_url('/saas/client/db/configure/update-admin-user'),
            data={
                'token_hash': self._hash_token,
                'db': self._client.dbname,
                'email': 'test@test.test',
                'name': 'Test Admin',
                'phone': '12345678',
                'login': 'admin-s1',
                'password': 'my-password',
            })
        self.assertEqual(response.status_code, 200)

        admin_user = self._new_admin_cl['res.users'].browse(ADMIN_USER_ID)
        self.assertEqual(admin_user.login, 'admin-s1')
        self.assertEqual(admin_user.name, 'Test Admin')
        self.assertEqual(admin_user.phone, '12345678')
        self.assertEqual(admin_user.email, 'test@test.test')

        self.assertEqual(
            self._client.login(
                self._client.dbname, 'admin-s1', 'my-password').uid,
            ADMIN_USER_ID)

    def test_20_db_configure_update_admin_no_params(self):
        self.assertEqual(
            self._client['res.users'].browse(ADMIN_USER_ID).login, 'admin')

        response = requests.post(
            self.create_url('/saas/client/db/configure/update-admin-user'),
            data={
                'token_hash': self._hash_token,
                'db': self._client.dbname,
            })
        self.assertEqual(response.status_code, 200)

        # nothing have to be changed
        self.assertEqual(
            self._new_admin_cl['res.users'].browse(ADMIN_USER_ID).login,
            'admin')
