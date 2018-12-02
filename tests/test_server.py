import requests

from .common import TestOdooInfrastructureClient


class TestOdooInfrastructureSaasClientServerSlowStatistic(
        TestOdooInfrastructureClient):

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
