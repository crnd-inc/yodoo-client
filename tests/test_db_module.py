import requests

from .common import TestOdooInfrastructureClient


class TestDBModuleInstallUpgradeUninstall(TestOdooInfrastructureClient):
    def setUp(self):
        self._db_module_install_url = self.create_url(
            '/saas/client/db/module/install')
        self._db_module_uninstall_url = self.create_url(
            '/saas/client/db/module/uninstall')
        self._db_module_upgrade_url = self.create_url(
            '/saas/client/db/module/upgrade')

        self._db_module_module = 'board'
        self._db_module_modules = ['contacts', 'calendar']

        self._db_module_data_single = {
            'token_hash': self._hash_token,
            'db': self._client.dbname,
            'module_name': self._db_module_module,
        }
        self._db_module_data_multi = {
            'token_hash': self._hash_token,
            'db': self._client.dbname,
            'module_names': ", ".join(
                self._db_module_modules),
        }

    def _get_rpc_single_module(self):
        IrModule = self._client['ir.module.module']
        modules = IrModule.search_records(
            [('name', '=', self._db_module_module)])
        self.assertEqual(len(modules), 1)
        return modules[0]

    def _get_rpc_multi_modules(self):
        IrModule = self._client['ir.module.module']
        modules = IrModule.search_records(
            [('name', 'in', self._db_module_modules)])
        self.assertEqual(len(modules), 2)
        return modules

    def assertMultiModulesState(self, state):
        self.assertTrue(
            all(m.state == state for m in self._get_rpc_multi_modules()))

    def test_01_controller_db_module_single(self):
        # check if module is installed
        self.assertEqual(self._get_rpc_single_module().state, 'uninstalled')

        # install module
        response = requests.post(
            self._db_module_install_url, self._db_module_data_single)
        self.assertEqual(response.status_code, 200)

        # check if module is installed
        self.assertEqual(self._get_rpc_single_module().state, 'installed')

        # Upgrade module
        response = requests.post(
            self._db_module_upgrade_url, self._db_module_data_single)
        self.assertEqual(response.status_code, 200)

        # check if module is installed
        self.assertEqual(self._get_rpc_single_module().state, 'installed')

        # Uninstall module
        response = requests.post(
            self._db_module_uninstall_url, self._db_module_data_single)
        self.assertEqual(response.status_code, 200)

        # check if module is installed
        self.assertEqual(self._get_rpc_single_module().state, 'uninstalled')

    def test_01_controller_db_module_multi(self):
        # check if module is installed
        self.assertMultiModulesState('uninstalled')

        # install request
        response = requests.post(
            self._db_module_install_url, self._db_module_data_multi)
        self.assertEqual(response.status_code, 200)

        # check if module is installed
        self.assertMultiModulesState('installed')

        # Upgrade module
        response = requests.post(
            self._db_module_upgrade_url, self._db_module_data_multi)
        self.assertEqual(response.status_code, 200)

        # check if module is installed
        self.assertMultiModulesState('installed')

        # Uninstall module
        response = requests.post(
            self._db_module_uninstall_url, self._db_module_data_multi)
        self.assertEqual(response.status_code, 200)

        # check if module is installed
        self.assertMultiModulesState('uninstalled')

    def test_02_controller_db_module_bad_token(self):
        # install-single
        response = requests.post(
            self._db_module_install_url,
            dict(self._db_module_data_single, token_hash='abracadabra'))
        self.assertEqual(response.status_code, 403)

        # upgrade-single
        response = requests.post(
            self._db_module_upgrade_url,
            dict(self._db_module_data_single, token_hash='abracadabra'))
        self.assertEqual(response.status_code, 403)

        # uninstall-single
        response = requests.post(
            self._db_module_uninstall_url,
            dict(self._db_module_data_single, token_hash='abracadabra'))
        self.assertEqual(response.status_code, 403)

        # install-multi
        response = requests.post(
            self._db_module_install_url,
            dict(self._db_module_data_multi, token_hash='abracadabra'))
        self.assertEqual(response.status_code, 403)

        # upgrade-multi
        response = requests.post(
            self._db_module_upgrade_url,
            dict(self._db_module_data_multi, token_hash='abracadabra'))
        self.assertEqual(response.status_code, 403)

        # uninstall-multi
        response = requests.post(
            self._db_module_uninstall_url,
            dict(self._db_module_data_multi, token_hash='abracadabra'))
        self.assertEqual(response.status_code, 403)

    def test_03_controller_db_module_bad_db(self):
        # install-single
        response = requests.post(
            self._db_module_install_url,
            dict(self._db_module_data_single, db='abracadabra'))
        self.assertEqual(response.status_code, 440)

        # upgrade-single
        response = requests.post(
            self._db_module_upgrade_url,
            dict(self._db_module_data_single, db='abracadabra'))
        self.assertEqual(response.status_code, 440)

        # uninstall-single
        response = requests.post(
            self._db_module_uninstall_url,
            dict(self._db_module_data_single, db='abracadabra'))
        self.assertEqual(response.status_code, 440)

        # install-multi
        response = requests.post(
            self._db_module_install_url,
            dict(self._db_module_data_multi, db='abracadabra'))
        self.assertEqual(response.status_code, 440)

        # upgrade-multi
        response = requests.post(
            self._db_module_upgrade_url,
            dict(self._db_module_data_multi, db='abracadabra'))
        self.assertEqual(response.status_code, 440)

        # uninstall-multi
        response = requests.post(
            self._db_module_uninstall_url,
            dict(self._db_module_data_multi, db='abracadabra'))
        self.assertEqual(response.status_code, 440)

    def test_04_controller_db_module_no_module_name(self):
        self._db_module_data_single.pop('module_name')
        self._db_module_data_multi.pop('module_names')

        # install-single
        response = requests.post(
            self._db_module_install_url,
            self._db_module_data_single)
        self.assertEqual(response.status_code, 200)

        # upgrade-single
        response = requests.post(
            self._db_module_upgrade_url,
            self._db_module_data_single)
        self.assertEqual(response.status_code, 200)

        # uninstall-single
        response = requests.post(
            self._db_module_uninstall_url,
            self._db_module_data_single)
        self.assertEqual(response.status_code, 200)

        # install-multi
        response = requests.post(
            self._db_module_install_url,
            self._db_module_data_multi)
        self.assertEqual(response.status_code, 200)

        # upgrade-multi
        response = requests.post(
            self._db_module_upgrade_url,
            self._db_module_data_multi)
        self.assertEqual(response.status_code, 200)

        # uninstall-multi
        response = requests.post(
            self._db_module_uninstall_url,
            self._db_module_data_multi)
        self.assertEqual(response.status_code, 200)

    def test_05_controller_db_module_incorrect_module(self):
        self._db_module_data_single['module_name'] = 'foobar'
        self._db_module_data_multi['module_names'] = 'foo, bar, zeta'

        # install-single
        response = requests.post(
            self._db_module_install_url,
            self._db_module_data_single)
        self.assertEqual(response.status_code, 200)

        # upgrade-single
        response = requests.post(
            self._db_module_upgrade_url,
            self._db_module_data_single)
        self.assertEqual(response.status_code, 200)

        # uninstall-single
        response = requests.post(
            self._db_module_uninstall_url,
            self._db_module_data_single)
        self.assertEqual(response.status_code, 200)

        # install-multi
        response = requests.post(
            self._db_module_install_url,
            self._db_module_data_multi)
        self.assertEqual(response.status_code, 200)

        # upgrade-multi
        response = requests.post(
            self._db_module_upgrade_url,
            self._db_module_data_multi)
        self.assertEqual(response.status_code, 200)

        # uninstall-multi
        response = requests.post(
            self._db_module_uninstall_url,
            self._db_module_data_multi)
        self.assertEqual(response.status_code, 200)
