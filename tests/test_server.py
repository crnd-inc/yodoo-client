import six
import requests

from .common import TestOdooInfrastructureClient


class TestServerSlowStatistic(TestOdooInfrastructureClient):

    def setUp(self):
        self._server_slow_statistic_url = self.create_url(
            '/saas/client/server/slow/stat')
        self._server_slow_statistic_data = {
            'token_hash': self._hash_token
        }

    def test_01_controller_odoo_infrastructure_server_slow_statistic(self):
        # test correct request
        response = requests.post(
            self._server_slow_statistic_url, self._server_slow_statistic_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data['used_disk_space'], int)
        self.assertIsInstance(data['free_disk_space'], int)
        self.assertIsInstance(data['total_disk_space'], int)
        self.assertIsInstance(data['os_name'], six.string_types)
        self.assertIsInstance(data['os_machine'], six.string_types)
        self.assertIsInstance(data['os_version'], six.string_types)
        self.assertIsInstance(data['os_node'], six.string_types)
        self.assertIsInstance(data['db_count'], int)

    def test_02_controller_odoo_infrastructure_server_slow_statistic(self):
        # test incorrect request with bad token_hash
        data = dict(self._server_slow_statistic_data, token_hash='abracadabra')

        response = requests.post(self._server_slow_statistic_url, data)
        self.assertEqual(response.status_code, 403)


class TestServerFastStatistic(TestOdooInfrastructureClient):

    def setUp(self):
        self._server_fast_statistic_url = self.create_url(
            '/saas/client/server/fast/stat')
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
        self.assertIsInstance(data['cpu_load_average_1'], float)
        self.assertIsInstance(data['cpu_load_average_5'], float)
        self.assertIsInstance(data['cpu_load_average_15'], float)
        self.assertIsInstance(data['cpu_us'], float)
        self.assertIsInstance(data['cpu_sy'], float)
        self.assertIsInstance(data['cpu_id'], float)
        self.assertIsInstance(data['cpu_ni'], (float, NoneType))
        self.assertIsInstance(data['cpu_wa'], (float, NoneType))
        self.assertIsInstance(data['cpu_hi'], (float, NoneType))
        self.assertIsInstance(data['cpu_si'], (float, NoneType))
        self.assertIsInstance(data['cpu_st'], (float, NoneType))
        self.assertIsInstance(data['mem_total'], int)
        self.assertIsInstance(data['mem_free'], int)
        self.assertIsInstance(data['mem_used'], int)
        self.assertIsInstance(data['mem_buffers'], int)
        self.assertIsInstance(data['mem_available'], int)
        self.assertIsInstance(data['swap_total'], int)
        self.assertIsInstance(data['swap_free'], int)
        self.assertIsInstance(data['swap_used'], int)

    def test_02_controller_odoo_infrastructure_server_fast_statistic(self):
        # test incorrect request with bad token_hash
        data = dict(self._server_fast_statistic_data, token_hash='abracadabra')

        response = requests.post(self._server_fast_statistic_url, data)
        self.assertEqual(response.status_code, 403)


class TestServerModuleInfo(TestOdooInfrastructureClient):
    def setUp(self):
        self._module_info_url = self.create_url('/saas/client/module/info')
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
        self.assertIsInstance(base_info, dict)
        self.assertIsInstance(base_info['version'], six.string_types)
        self.assertIsInstance(base_info['name'], six.string_types)
        self.assertIsInstance(base_info['author'], six.string_types)
        self.assertIsInstance(base_info['summary'], six.string_types)
        self.assertIsInstance(base_info['license'], six.string_types)
        self.assertIsInstance(base_info['application'], bool)
        self.assertIsInstance(base_info['installable'], bool)
        self.assertIsInstance(base_info['auto_install'], bool)
        self.assertIsInstance(base_info['category'], six.string_types)
        self.assertIsInstance(base_info['website'], six.string_types)
        self.assertIsInstance(base_info['sequence'], int)

    def test_02_controller_odoo_infrastructure_instance_module_info(self):
        # test incorrect request with bad token_hash
        data = dict(self._module_info_data, token_hash='abracadabra')

        response = requests.post(self._module_info_url, data)
        self.assertEqual(response.status_code, 403)


class TestModuleInfoTokenInHeader(TestOdooInfrastructureClient):
    def setUp(self):
        self._module_info_url = self.create_url('/saas/client/module/info')
        self._module_info_data = {}

    def test_01_controller_odoo_infrastructure_instance_module_info(self):
        response = requests.post(
            self._module_info_url, self._module_info_data,
            headers={'X-YODOO-TOKEN': self._hash_token})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) != 0)
        base_info = data.get('base', None)
        self.assertIsNotNone(base_info)
