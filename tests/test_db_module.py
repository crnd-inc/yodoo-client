import requests

from .common import TestOdooInfrastructureClient


class TestOdooInfrastructureDBModuleInstall(TestOdooInfrastructureClient):
    def setUp(self):
        self._db_module_install_url = self.create_url(
            '/saas/client/db/module/install')
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
        self._db_module_install_url = self.create_url(
            '/saas/client/db/module/install')
        self._db_module_uninstall_url = self.create_url(
            '/saas/client/db/module/uninstall')
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
        self._db_module_upgrade_url = self.create_url(
            '/saas/client/db/module/upgrade')
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
