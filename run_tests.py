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


class TestOdooInfrastructureAuthAuth(TestOdooInfrastructureClient):

    def setUp(self):
        self._url = create_url(
            self._odoo_host,
            self._odoo_port,
            '/odoo/infrastructure/auth/'
        )
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
        self.assertTrue(isinstance(data['token_password'], str))
        self.assertTrue(isinstance(data['token_user'], str))
        self.assertTrue(isinstance(data['expire'], str))
        self.assertTrue(isinstance(data['temp_url'], str))
        self.assertTrue(isinstance(data['token_temp'], str))

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
        self._data = {
            'token_hash': self._hash_token,
            'ttl': 300,
            'db': self._client.dbname
        }
        self._url = create_url(
            self._odoo_host,
            self._odoo_port,
            '/odoo/infrastructure/auth/'
        )
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


class TestOdooInfrastructureSaasClientVersionInfo(
        TestOdooInfrastructureClient):

    def setUp(self):
        self.incorrect_response_keys = {'error'}
        self._version_url = create_url(
            self._odoo_host,
            self._odoo_port,
            '/saas/client/version_info'
        )
        self._version_data = {
            'token_hash': self._hash_token,
        }

    def test_01_controller_odoo_infrastructure_saas_client_version(self):
        # test correct request
        response = requests.post(self._version_url, self._version_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(isinstance(data['odoo_version'], str))
        self.assertTrue(isinstance(data['odoo_version_info'], list))
        self.assertTrue(isinstance(data['odoo_serie'], str))
        self.assertTrue(isinstance(data['saas_client_version'], str))
        self.assertTrue(isinstance(data['saas_client_serie'], str))
        self.assertTrue(isinstance(data['saas_client_api_version'], int))
        self.assertTrue(isinstance(data['features_enabled'], dict))
        features_enabled = data['features_enabled']
        self.assertTrue(isinstance(features_enabled['admin_access_url'], bool))
        self.assertTrue(
            isinstance(features_enabled['admin_access_credentials'], bool))

    def test_02_controller_odoo_infrastructure_saas_client_version(self):
        # test incorrect request with bad token_hash
        data = dict(self._version_data, token_hash='abracadabra')

        response = requests.post(self._version_url, data)
        self.assertEqual(response.status_code, 403)


class TestOdooInfrastructureSaasClientDBStatistic(
        TestOdooInfrastructureClient):

    def setUp(self):
        self._db_statistic_url = create_url(
            self._odoo_host,
            self._odoo_port,
            '/saas/client/db/stat'
        )
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


class TestOdooInfrastructureSaasClientServerSlowStatistic(
        TestOdooInfrastructureClient):

    def setUp(self):
        self._server_slow_statistic_url = create_url(
            self._odoo_host,
            self._odoo_port,
            '/saas/client/server/slow/stat'
        )
        self._server_slow_statistic_data = {
            'token_hash': self._hash_token
        }

    def test_01_controller_odoo_infrastructure_server_slow_statistic(self):
        # test correct request
        response = requests.post(
            self._server_slow_statistic_url, self._server_slow_statistic_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(isinstance(data['used_disc_space'], int))
        self.assertTrue(isinstance(data['free_disc_space'], int))
        self.assertTrue(isinstance(data['total_disc_space'], int))
        self.assertTrue(isinstance(data['os_name'], str))
        self.assertTrue(isinstance(data['os_machine'], str))
        self.assertTrue(isinstance(data['os_version'], str))
        self.assertTrue(isinstance(data['os_node'], str))
        self.assertTrue(isinstance(data['db_count'], int))

    def test_02_controller_odoo_infrastructure_server_slow_statistic(self):
        # test incorrect request with bad token_hash
        data = dict(self._server_slow_statistic_data, token_hash='abracadabra')

        response = requests.post(self._server_slow_statistic_url, data)
        self.assertEqual(response.status_code, 403)


class TestOdooInfrastructureSaasClientServerFastStatistic(
        TestOdooInfrastructureClient):

    def setUp(self):
        self._server_fast_statistic_url = create_url(
            self._odoo_host,
            self._odoo_port,
            '/saas/client/server/fast/stat'
        )
        self._server_fast_statistic_data = {
            'token_hash': self._hash_token
        }

    def test_01_controller_odoo_infrastructure_server_fast_statistic(self):
        # test correct request
        NoneType = type(None)
        response = requests.post(
            self._server_fast_statistic_url, self._server_fast_statistic_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(isinstance(data['cpu_load_average_1'], float))
        self.assertTrue(isinstance(data['cpu_load_average_5'], float))
        self.assertTrue(isinstance(data['cpu_load_average_15'], float))
        self.assertTrue(isinstance(data['cpu_us'], float))
        self.assertTrue(isinstance(data['cpu_sy'], float))
        self.assertTrue(isinstance(data['cpu_id'], float))
        self.assertTrue(isinstance(data['cpu_ni'], (float, NoneType)))
        self.assertTrue(isinstance(data['cpu_wa'], (float, NoneType)))
        self.assertTrue(isinstance(data['cpu_hi'], (float, NoneType)))
        self.assertTrue(isinstance(data['cpu_si'], (float, NoneType)))
        self.assertTrue(isinstance(data['cpu_st'], (float, NoneType)))
        self.assertTrue(isinstance(data['mem_total'], int))
        self.assertTrue(isinstance(data['mem_free'], int))
        self.assertTrue(isinstance(data['mem_used'], int))
        self.assertTrue(isinstance(data['mem_buffers'], int))
        self.assertTrue(isinstance(data['mem_available'], int))
        self.assertTrue(isinstance(data['swap_total'], int))
        self.assertTrue(isinstance(data['swap_free'], int))
        self.assertTrue(isinstance(data['swap_used'], int))

    def test_02_controller_odoo_infrastructure_server_fast_statistic(self):
        # test incorrect request with bad token_hash
        data = dict(self._server_fast_statistic_data, token_hash='abracadabra')

        response = requests.post(self._server_fast_statistic_url, data)
        self.assertEqual(response.status_code, 403)


class TestOdooInfrastructureInstanceModuleInfo(TestOdooInfrastructureClient):
    def setUp(self):
        self._module_info_url = create_url(
            self._odoo_host,
            self._odoo_port,
            '/saas/client/module/info'
        )
        self._module_info_data = {
            'token_hash': self._hash_token
        }

    def test_01_controller_odoo_infrastructure_instance_module_info(self):
        response = requests.post(
            self._module_info_url, self._module_info_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) != 0)
        base_info = data.get('base', None)
        self.assertIsNotNone(base_info)
        self.assertTrue(isinstance(base_info, dict))
        self.assertTrue(isinstance(base_info['version'], str))
        self.assertTrue(isinstance(base_info['name'], str))
        self.assertTrue(isinstance(base_info['author'], str))
        self.assertTrue(isinstance(base_info['summary'], str))
        self.assertTrue(isinstance(base_info['license'], str))
        self.assertTrue(isinstance(base_info['application'], bool))
        self.assertTrue(isinstance(base_info['installable'], bool))
        self.assertTrue(isinstance(base_info['auto_install'], bool))
        self.assertTrue(isinstance(base_info['category'], str))
        self.assertTrue(isinstance(base_info['website'], str))
        self.assertTrue(isinstance(base_info['sequence'], int))

    def test_02_controller_odoo_infrastructure_instance_module_info(self):
        # test incorrect request with bad token_hash
        data = dict(self._module_info_data, token_hash='abracadabra')

        response = requests.post(self._module_info_url, data)
        self.assertEqual(response.status_code, 403)


class TestOdooInfrastructureDBModuleInfo(TestOdooInfrastructureClient):
    def setUp(self):
        self._db_info_url = create_url(
            self._odoo_host,
            self._odoo_port,
            '/saas/client/db/module/info'
        )
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
        self._user_info_url = create_url(
            self._odoo_host,
            self._odoo_port,
            '/saas/client/db/users/info'
        )
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


class TestOdooInfrastructureDBModuleInstall(TestOdooInfrastructureClient):
    def setUp(self):
        self._db_module_install_url = create_url(
            self._odoo_host,
            self._odoo_port,
            '/saas/client/db/module/install'
        )
        self._db_module_install_data = {
            'token_hash': self._hash_token,
            'db': self._client.dbname,
            'module_name': 'board'
        }

    def test_01_controller_odoo_infrastructure_db_module_install(self):
        # check if module is installed
        OdooInfrastructureClientAuth = self._client[
            'ir.module.module']
        board_module = OdooInfrastructureClientAuth.search_records(
            [('name', '=', 'board')])
        self.assertEqual('uninstalled', board_module[0].state)
        # install request
        response = requests.post(
            self._db_module_install_url, self._db_module_install_data)
        self.assertEqual(response.status_code, 200)
        # check if module is installed
        OdooInfrastructureClientAuth = self._client[
            'ir.module.module']
        board_module = OdooInfrastructureClientAuth.search_records(
            [('name', '=', 'board')])
        self.assertEqual('installed', board_module[0].state)

    def test_02_controller_odoo_infrastructure_db_module_install(self):
        # test incorrect request with bad token_hash
        data = dict(self._db_module_install_data, token_hash='abracadabra')

        response = requests.post(self._db_module_install_url, data)
        self.assertEqual(response.status_code, 403)

    def test_03_controller_odoo_infrastructure_db_module_install(self):
        # test incorrect request with bad db_name
        data = dict(self._db_module_install_data, db='abracadabra')

        response = requests.post(self._db_module_install_url, data)
        self.assertEqual(response.status_code, 404)

    def test_04_controller_odoo_infrastructure_db_module_install(self):
        # test incorrect request without module name
        data = dict(self._db_module_install_data)
        del data['module_name']

        response = requests.post(self._db_module_install_url, data)
        self.assertEqual(response.status_code, 404)

    def test_05_controller_odoo_infrastructure_db_module_install(self):
        # test incorrect request wit bad module name
        data = dict(self._db_module_install_data, module_name='abracadabra')

        response = requests.post(self._db_module_install_url, data)
        self.assertEqual(response.status_code, 404)


class TestOdooInfrastructureDBModuleUninstall(TestOdooInfrastructureClient):
    def setUp(self):
        self._db_module_install_url = create_url(
            self._odoo_host,
            self._odoo_port,
            '/saas/client/db/module/install'
        )
        self._db_module_uninstall_url = create_url(
            self._odoo_host,
            self._odoo_port,
            '/saas/client/db/module/uninstall'
        )
        self._db_module_uninstall_data = {
            'token_hash': self._hash_token,
            'db': self._client.dbname,
            'module_name': 'board'
        }

    def test_01_controller_odoo_infrastructure_db_module_uninstall(self):
        # check if module is installed
        OdooInfrastructureClientAuth = self._client[
            'ir.module.module']
        board_module = OdooInfrastructureClientAuth.search_records(
            [('name', '=', 'board')])
        self.assertEqual('uninstalled', board_module[0].state)
        # install request
        response = requests.post(
            self._db_module_install_url, self._db_module_uninstall_data)
        self.assertEqual(response.status_code, 200)
        # check if module is installed
        OdooInfrastructureClientAuth = self._client[
            'ir.module.module']
        board_module = OdooInfrastructureClientAuth.search_records(
            [('name', '=', 'board')])
        self.assertEqual('installed', board_module[0].state)
        # uninstall request
        response = requests.post(
            self._db_module_uninstall_url, self._db_module_uninstall_data)
        self.assertEqual(response.status_code, 200)
        # check if module is installed
        OdooInfrastructureClientAuth = self._client[
            'ir.module.module']
        board_module = OdooInfrastructureClientAuth.search_records(
            [('name', '=', 'board')])
        self.assertEqual('uninstalled', board_module[0].state)

    def test_02_controller_odoo_infrastructure_db_module_uninstall(self):
        # test incorrect request with bad token_hash
        data = dict(self._db_module_uninstall_data, token_hash='abracadabra')

        response = requests.post(self._db_module_uninstall_url, data)
        self.assertEqual(response.status_code, 403)

    def test_03_controller_odoo_infrastructure_db_module_uninstall(self):
        # test incorrect request with bad db_name
        data = dict(self._db_module_uninstall_data, db='abracadabra')

        response = requests.post(self._db_module_uninstall_url, data)
        self.assertEqual(response.status_code, 404)

    def test_04_controller_odoo_infrastructure_db_module_uninstall(self):
        # test incorrect request without module name
        data = dict(self._db_module_uninstall_data)
        del data['module_name']

        response = requests.post(self._db_module_uninstall_url, data)
        self.assertEqual(response.status_code, 404)

    def test_05_controller_odoo_infrastructure_db_module_uninstall(self):
        # test incorrect request wit bad module name
        data = dict(self._db_module_uninstall_data, module_name='abracadabra')

        response = requests.post(self._db_module_uninstall_url, data)
        self.assertEqual(response.status_code, 404)


class TestOdooInfrastructureDBModuleUpgrade(TestOdooInfrastructureClient):
    def setUp(self):
        self._db_module_upgrade_url = create_url(
            self._odoo_host,
            self._odoo_port,
            '/saas/client/db/module/upgrade'
        )
        self._db_module_upgrade_data = {
            'token_hash': self._hash_token,
            'db': self._client.dbname,
            'module_name': 'odoo_infrastructure_client'
        }

    def test_01_controller_odoo_infrastructure_db_module_upgrade(self):
        # upgrade request
        response = requests.post(
            self._db_module_upgrade_url, self._db_module_upgrade_data)
        self.assertEqual(response.status_code, 200)

    def test_02_controller_odoo_infrastructure_db_module_upgrade(self):
        # test incorrect request with bad token_hash
        data = dict(self._db_module_upgrade_data, token_hash='abracadabra')

        response = requests.post(self._db_module_upgrade_url, data)
        self.assertEqual(response.status_code, 403)

    def test_03_controller_odoo_infrastructure_db_module_upgrade(self):
        # test incorrect request with bad db_name
        data = dict(self._db_module_upgrade_data, db='abracadabra')

        response = requests.post(self._db_module_upgrade_url, data)
        self.assertEqual(response.status_code, 404)

    def test_04_controller_odoo_infrastructure_db_module_upgrade(self):
        # test incorrect request without module name
        data = dict(self._db_module_upgrade_data)
        del data['module_name']

        response = requests.post(self._db_module_upgrade_url, data)
        self.assertEqual(response.status_code, 404)

    def test_05_controller_odoo_infrastructure_db_module_upgrade(self):
        # test incorrect request wit bad module name
        data = dict(self._db_module_upgrade_data, module_name='abracadabra')

        response = requests.post(self._db_module_upgrade_url, data)
        self.assertEqual(response.status_code, 404)


class TestOdooInfrastructureCreateDB(TestOdooInfrastructureClient):
    def setUp(self):
        self._create_db_url = create_url(
            self._odoo_host,
            self._odoo_port,
            '/saas/client/db/create'
        )
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


if __name__ == '__main__':
    unittest.main()
