import io
import zipfile
import requests
from requests_toolbelt import MultipartEncoder

from .common import TestOdooInfrastructureClient


class TestDBManagement(TestOdooInfrastructureClient):
    def setUp(self):
        self._data_base = {
            'token_hash': self._hash_token,
        }
        self._create_db_url = self.create_url(
            '/saas/client/db/create')
        self._create_db_data = dict(
            self._data_base,
            dbname='test_db',
            user_login='test_user',
            user_password='test_password',
        )
        self._exists_db_url = self.create_url(
            '/saas/client/db/exists')
        self._exists_db_data = dict(
            self._data_base,
            db='test_db',
        )
        self._list_db_url = self.create_url(
            '/saas/client/db/list')
        self._list_db_data = dict(self._data_base)
        self._duplicate_db_url = self.create_url(
            '/saas/client/db/duplicate')
        self._duplicate_db_data = dict(
            self._data_base,
            db='test_db',
            new_dbname='test_db_copy',
        )
        self._rename_db_url = self.create_url(
            '/saas/client/db/rename')
        self._rename_db_data = dict(
            self._data_base,
            db='test_db',
            new_dbname='test_db_renamed',
        )
        self._drop_db_url = self.create_url(
            '/saas/client/db/drop')
        self._drop_db_data = dict(
            self._data_base,
            db='test_db',
        )
        self._backup_db_url = self.create_url(
            '/saas/client/db/backup')
        self._backup_db_data = dict(
            self._data_base,
            db='test_db',
        )
        self._restore_db_url = self.create_url(
            '/saas/client/db/restore')
        self._restore_db_data = dict(
            self._data_base,
            db='test_db',
            backup_file="test",
        )

    def test_01_controller_create_db_no_demo(self):
        # Ensure database does not exists
        response = requests.post(
            self._exists_db_url, self._exists_db_data)
        self.assertEqual(response.status_code, 440)

        # List databases and check there is no database 'test_db' in list
        response = requests.post(
            self._list_db_url, self._list_db_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('test_db', response.json())

        # Create database without demo data
        response = requests.post(
            self._create_db_url, dict(self._create_db_data, demo=False))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._odoo_instance.services.db.db_exist('test_db'))

        # Check that database exists
        response = requests.post(
            self._exists_db_url, self._exists_db_data)
        self.assertEqual(response.status_code, 200)

        # List databases and check that database 'test_db' in that list
        response = requests.post(
            self._list_db_url, self._list_db_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('test_db', response.json())

        # Ensure created database is without demo data
        self.assertFalse(
            self._client.login(
                'test_db', 'test_user', 'test_password'
            )['ir.model.data'].xmlid_to_res_id('base.user_demo'))

        # Duplicate database
        response = requests.post(
            self._duplicate_db_url, self._duplicate_db_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._odoo_instance.services.db.db_exist('test_db'))
        self.assertTrue(
            self._odoo_instance.services.db.db_exist('test_db_copy'))

        # Duplicate database again and see conflict (such db already exists)
        response = requests.post(
            self._duplicate_db_url, self._duplicate_db_data)
        self.assertEqual(response.status_code, 409)

        # Rename copied database to test_db and see conflict
        response = requests.post(
            self._rename_db_url,
            dict(self._rename_db_data,
                 db='test_db_copy',
                 new_dbname='test_db'))
        self.assertEqual(response.status_code, 409)

        # Rename copied database to test_db_copy_2
        response = requests.post(
            self._rename_db_url,
            dict(self._rename_db_data,
                 db='test_db_copy',
                 new_dbname='test_db_copy_2'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._odoo_instance.services.db.db_exist('test_db'))
        self.assertFalse(
            self._odoo_instance.services.db.db_exist('test_db_copy'))
        self.assertTrue(
            self._odoo_instance.services.db.db_exist('test_db_copy_2'))

        # Drop copied DB
        response = requests.post(
            self._drop_db_url, dict(
                self._drop_db_data,
                db='test_db_copy_2'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._odoo_instance.services.db.db_exist('test_db'))
        self.assertFalse(
            self._odoo_instance.services.db.db_exist('test_db_copy'))
        self.assertFalse(
            self._odoo_instance.services.db.db_exist('test_db_copy_2'))

        # Drop database
        self._odoo_instance.services.db.drop_db(
            self._odoo_admin_pass, 'test_db')
        self.assertFalse(self._odoo_instance.services.db.db_exist('test_db'))

    def test_01_controller_create_db_demo(self):
        response = requests.post(
            self._create_db_url, dict(self._create_db_data, demo=True))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._odoo_instance.services.db.db_exist('test_db'))

        # Ensure created database is without demo data
        self.assertTrue(
            self._client.login(
                'test_db', 'test_user', 'test_password'
            )['ir.model.data'].xmlid_to_res_id('base.user_demo'))

        # Backup database
        response = requests.post(self._backup_db_url, self._backup_db_data)
        self.assertEqual(response.status_code, 200)
        backup_data = response.content
        self.assertTrue(zipfile.is_zipfile(io.BytesIO(backup_data)))

        # Try restore database and see conflict (database already exists)
        data = MultipartEncoder(
            fields=dict(
                self._restore_db_data,
                backup_file=(
                    'filename',
                    io.BytesIO(backup_data),
                    'application/octet-stream'),
            )
        )
        response = requests.post(
            self._restore_db_url,
            data=data,
            headers={'Content-Type': data.content_type},
        )
        self.assertEqual(response.status_code, 409)

        # Drop database
        self._odoo_instance.services.db.drop_db(
            self._odoo_admin_pass, 'test_db')
        self.assertFalse(self._odoo_instance.services.db.db_exist('test_db'))

        # Restore database
        data = MultipartEncoder(
            fields=dict(
                self._restore_db_data,
                backup_file=(
                    'filename',
                    io.BytesIO(backup_data),
                    'application/octet-stream'),
            )
        )
        response = requests.post(
            self._restore_db_url,
            data=data,
            headers={'Content-Type': data.content_type},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._odoo_instance.services.db.db_exist('test_db'))

        # Drop database
        self._odoo_instance.services.db.drop_db(
            self._odoo_admin_pass, 'test_db')
        self.assertFalse(self._odoo_instance.services.db.db_exist('test_db'))

    def test_01_controller_create_db_demo_contry_code_none(self):
        response = requests.post(
            self._create_db_url,
            dict(self._create_db_data, demo=True, contry_code=None))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._odoo_instance.services.db.db_exist('test_db'))

        # Ensure created database is with demo data
        self.assertTrue(
            self._client.login(
                'test_db', 'test_user', 'test_password'
            )['ir.model.data'].xmlid_to_res_id('base.user_demo'))

        # Drop database
        self._odoo_instance.services.db.drop_db(
            self._odoo_admin_pass, 'test_db')
        self.assertFalse(self._odoo_instance.services.db.db_exist('test_db'))

    def test_01_controller_create_db_demo_contry_code_none_str(self):
        response = requests.post(
            self._create_db_url,
            dict(self._create_db_data, demo=True, contry_code='None'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._odoo_instance.services.db.db_exist('test_db'))

        # Ensure created database is with demo data
        self.assertTrue(
            self._client.login(
                'test_db', 'test_user', 'test_password'
            )['ir.model.data'].xmlid_to_res_id('base.user_demo'))

        # Drop database
        self._odoo_instance.services.db.drop_db(
            self._odoo_admin_pass, 'test_db')
        self.assertFalse(self._odoo_instance.services.db.db_exist('test_db'))

    def test_01_controller_create_db_demo_contry_code_ua(self):
        response = requests.post(
            self._create_db_url,
            dict(self._create_db_data, demo=True, contry_code='UA'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._odoo_instance.services.db.db_exist('test_db'))

        # Ensure created database is with demo data
        self.assertTrue(
            self._client.login(
                'test_db', 'test_user', 'test_password'
            )['ir.model.data'].xmlid_to_res_id('base.user_demo'))

        # Drop database
        self._odoo_instance.services.db.drop_db(
            self._odoo_admin_pass, 'test_db')
        self.assertFalse(self._odoo_instance.services.db.db_exist('test_db'))

    def test_02_controller_create_db_bad_token(self):
        # test incorrect request with bad token_hash
        data = dict(self._create_db_data, token_hash='abracadabra')

        response = requests.post(self._create_db_url, data)
        self.assertEqual(response.status_code, 403)

    def test_03_controller_create_db_existing_database(self):
        # test request with existing dbname
        data = dict(self._create_db_data, dbname=self._client.dbname)

        response = requests.post(self._create_db_url, data)
        self.assertEqual(response.status_code, 409)

    def test_04_controller_create_db_no_dbname(self):
        # test request without dbname
        data = dict(self._create_db_data, dbname=None)

        response = requests.post(self._create_db_url, data)
        self.assertEqual(response.status_code, 400)

    def test_03_controller_db_exists_bad_token(self):
        # test incorrect request with bad token_hash
        data = dict(self._exists_db_data, token_hash='abracadabra')

        response = requests.post(self._exists_db_url, data)
        self.assertEqual(response.status_code, 403)

    def test_04_controller_db_exists_no_dbname(self):
        # test request without dbname
        data = dict(self._exists_db_data, db=None)

        response = requests.post(self._exists_db_url, data)
        self.assertEqual(response.status_code, 400)

    def test_03_controller_db_list_bad_token(self):
        # test incorrect request with bad token_hash
        data = dict(self._list_db_data, token_hash='abracadabra')

        response = requests.post(self._list_db_url, data)
        self.assertEqual(response.status_code, 403)

    def test_03_controller_db_duplicate_bad_token(self):
        # test incorrect request with bad token_hash
        data = dict(self._duplicate_db_data, token_hash='abracadabra')

        response = requests.post(self._duplicate_db_url, data)
        self.assertEqual(response.status_code, 403)

    def test_04_controller_db_duplicate_no_dbname(self):
        # test request without dbname
        data = dict(self._duplicate_db_data, db=None)

        response = requests.post(self._duplicate_db_url, data)
        self.assertEqual(response.status_code, 400)

    def test_04_controller_db_duplicate_bad_dbname(self):
        # test request with bad dbname
        data = dict(self._duplicate_db_data, db='abracadabra')

        response = requests.post(self._duplicate_db_url, data)
        self.assertEqual(response.status_code, 440)

    def test_04_controller_db_duplicate_no_new_dbname(self):
        # test request without dbname
        data = dict(
            self._duplicate_db_data,
            db=self._client.dbname, new_dbname=None)

        response = requests.post(self._duplicate_db_url, data)
        self.assertEqual(response.status_code, 400)

    def test_03_controller_db_rename_bad_token(self):
        # test incorrect request with bad token_hash
        data = dict(self._rename_db_data, token_hash='abracadabra')

        response = requests.post(self._rename_db_url, data)
        self.assertEqual(response.status_code, 403)

    def test_04_controller_db_rename_no_dbname(self):
        # test request without dbname
        data = dict(self._rename_db_data, db=None)

        response = requests.post(self._rename_db_url, data)
        self.assertEqual(response.status_code, 400)

    def test_04_controller_db_rename_bad_dbname(self):
        # test request with bad dbname
        data = dict(self._rename_db_data, db='abracadabra')

        response = requests.post(self._rename_db_url, data)
        self.assertEqual(response.status_code, 440)

    def test_04_controller_db_rename_no_new_dbname(self):
        # test request without dbname
        data = dict(
            self._rename_db_data,
            db=self._client.dbname,
            new_dbname=None)

        response = requests.post(self._rename_db_url, data)
        self.assertEqual(response.status_code, 400)

    def test_03_controller_db_drop_bad_token(self):
        # test incorrect request with bad token_hash
        data = dict(self._drop_db_data, token_hash='abracadabra')

        response = requests.post(self._drop_db_url, data)
        self.assertEqual(response.status_code, 403)

    def test_04_controller_db_drop_no_dbname(self):
        # test request without dbname
        data = dict(self._drop_db_data, db=None)

        response = requests.post(self._drop_db_url, data)
        self.assertEqual(response.status_code, 400)

    def test_04_controller_db_drop_bad_dbname(self):
        # test request with bad dbname
        data = dict(self._drop_db_data, db='abracadabra')

        response = requests.post(self._drop_db_url, data)
        self.assertEqual(response.status_code, 440)

    def test_03_controller_db_backup_bad_token(self):
        # test incorrect request with bad token_hash
        data = dict(self._backup_db_data, token_hash='abracadabra')

        response = requests.post(self._backup_db_url, data)
        self.assertEqual(response.status_code, 403)

    def test_04_controller_db_backup_no_dbname(self):
        # test request without dbname
        data = dict(self._backup_db_data, db=None)

        response = requests.post(self._backup_db_url, data)
        self.assertEqual(response.status_code, 400)

    def test_04_controller_db_backup_bad_dbname(self):
        # test request with bad dbname
        data = dict(self._backup_db_data, db='abracadabra')

        response = requests.post(self._backup_db_url, data)
        self.assertEqual(response.status_code, 440)

    def test_03_controller_db_restore_bad_token(self):
        # test incorrect request with bad token_hash
        data = dict(self._restore_db_data, token_hash='abracadabra')

        response = requests.post(self._restore_db_url, data)
        self.assertEqual(response.status_code, 403)

    def test_04_controller_db_restore_no_dbname(self):
        # test request without dbname
        data = dict(self._restore_db_data, db=None)

        response = requests.post(self._restore_db_url, data)
        self.assertEqual(response.status_code, 400)
