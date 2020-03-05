import os
import re
import json
import logging
import tempfile
from contextlib import closing

import werkzeug

import odoo
from odoo import http, api, registry, exceptions, SUPERUSER_ID
from odoo.sql_db import db_connect
from odoo.http import Response
from odoo.service import db as service_db
from odoo.modules import db as modules_db
from odoo.tools.misc import str2bool

from ..utils import (
    prepare_db_statistic_data,
    str_filter_falsy,
    get_yodoo_client_version,
)
from ..http_decorators import (
    require_saas_token,
    require_db_param,
)


_logger = logging.getLogger(__name__)


class SAASClientDb(http.Controller):

    @http.route(
        '/saas/client/db/exists',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_exists(self, db=None, **params):
        return Response(status=200)

    @http.route(
        '/saas/client/db/list',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    def client_db_list(self, **params):
        # TODO: do not use force here. Server have to be adapted
        databases = service_db.list_dbs(force=True)
        return Response(json.dumps(databases), status=200)

    @http.route(
        '/saas/client/db/create',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    def client_db_create(self, dbname=None, demo=False, lang='en_US',
                         user_password='admin', user_login='admin',
                         country_code=None, phone=None,
                         template_dbname=None, **params):
        demo = str2bool(demo, False)
        if not dbname:
            raise werkzeug.exceptions.BadRequest(
                description='Missing parameter: dbname')
        _logger.info("Create database: %s (demo=%r)", dbname, demo)
        try:
            service_db._create_empty_database(dbname)
        except service_db.DatabaseExists as bd_ex:
            raise werkzeug.exceptions.Conflict(
                description=str(bd_ex))

        service_db._initialize_db(
            id, dbname, demo, lang, user_password, user_login,
            country_code=str_filter_falsy(country_code),
            # phone=str_filter_falsy(phone),
        )
        db = db_connect(dbname)
        with closing(db.cursor()) as cr:
            db_init = modules_db.is_initialized(cr)
        if not db_init:
            raise werkzeug.exceptions.InternalServerError(
                description='Database not initialized.')
        return Response('OK', status=200)

    @http.route(
        '/saas/client/db/duplicate',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_duplicate(self, db=None, new_dbname=None, **params):
        if not new_dbname:
            raise werkzeug.exceptions.BadRequest(
                "New database name not specified")
        if service_db.exp_db_exist(new_dbname):
            raise werkzeug.exceptions.Conflict(
                description="Database %s already exists" % new_dbname)

        _logger.info("Duplicate database: %s -> %s", db, new_dbname)
        service_db.exp_duplicate_database(db, new_dbname)
        return Response('OK', status=200)

    @http.route(
        '/saas/client/db/rename',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_rename(self, db=None, new_dbname=None, **params):
        if not new_dbname:
            raise werkzeug.exceptions.BadRequest(
                "New database name not specified")
        if service_db.exp_db_exist(new_dbname):
            raise werkzeug.exceptions.Conflict(
                description="Database %s already exists" % new_dbname)

        _logger.info("Rename database: %s -> %s", db, new_dbname)
        service_db.exp_rename(db, new_dbname)
        return Response('OK', status=200)

    @http.route(
        '/saas/client/db/drop',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_drop(self, db=None, **params):
        if not service_db.exp_drop(db):
            raise werkzeug.exceptions.Forbidden(
                description="It is not allowed to drop databse %s" % db)
        return Response('OK', status=200)

    @http.route(
        '/saas/client/db/backup',
        type='http',
        auth="none",
        methods=['POST'],
        csrf=False)
    @require_saas_token
    @require_db_param
    def client_db_backup(self, db=None, backup_format='zip', **params):
        filename = "%s.%s" % (db, backup_format)
        headers = [
            ('Content-Type', 'application/octet-stream; charset=binary'),
            ('Content-Disposition', http.content_disposition(filename)),
        ]
        try:
            stream = tempfile.TemporaryFile()
            service_db.dump_db(db, stream, backup_format)
        except exceptions.AccessDenied as e:
            raise werkzeug.exceptions.Forbidden(
                description=str(e))
        except Exception as e:
            _logger.error("Cannot backup db %s", db, exc_info=True)
            raise werkzeug.exceptions.InternalServerError(
                description=str(e))
        else:
            stream.seek(0)
            response = werkzeug.wrappers.Response(
                stream,
                headers=headers,
                direct_passthrough=True)
            return response

    def _postprocess_restored_db(self, dbname):
        """ Do some postprocessing after DB restored from backup

            The reason for this method, is to ensure that yodoo_client
            is installed on database and if needed updated.
            Also, we check installed addons and compare them with
            thats are available on disk, and if needed run update for them.
        """
        to_update_modules = set()
        to_install_modules = set()
        modules_in_db = {}
        modules_on_disk = {
            mod: odoo.modules.module.load_information_from_description_file(
                mod)
            for mod in odoo.modules.module.get_modules()
        }
        auto_install_addons = odoo.tools.config.get(
            'yodoo_auto_install_addons', '')
        auto_install_addons = [
            a.strip() for a in auto_install_addons.split(',') if a.strip()]

        with closing(db_connect(dbname).cursor()) as cr:
            cr.execute("""
                SELECT name, latest_version
                FROM ir_module_module
                WHERE state = 'installed';
            """)
            modules_in_db = dict(cr.fetchall())

        if 'yodoo_client' not in modules_in_db:
            _logger.info(
                "yodoo_client not installed, adding to install list")
            to_install_modules.add('yodoo_client')
        elif modules_in_db['yodoo_client'] != get_yodoo_client_version():
            _logger.info(
                "yodoo_client not up to date (%s != %s), "
                "adding to update list",
                modules_in_db['yodoo_client'], get_yodoo_client_version())
            to_update_modules.add('yodoo_client')

        for module_name in auto_install_addons:
            if module_name not in modules_on_disk:
                continue
            if module_name not in modules_in_db:
                _logger.info(
                    "Module %s is mentioned in auto_install_addons list, "
                    "but is not installed in database. Installing.",
                    module_name
                )
                to_install_modules.add(module_name)

        for module_name, db_version in modules_in_db.items():
            if module_name not in modules_on_disk:
                continue
            if db_version != modules_on_disk[module_name]['version']:
                _logger.info(
                    "Module %s is not up to data, adding to update list.",
                    module_name)
                to_update_modules.add(module_name)

        if to_install_modules or to_update_modules:
            _logger.info(
                "There are addons to install %s and to update %s found.",
                tuple(to_install_modules), tuple(to_update_modules))
            with registry(dbname).cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, context={})
                env['ir.module.module'].update_list()
                if to_install_modules:
                    env['ir.module.module'].search(
                        [('name', 'in', list(to_install_modules)),
                         ('state', 'in', ('uninstalled', 'to_install'))]
                    ).button_immediate_install()
                if to_update_modules:
                    env['ir.module.module'].search(
                        [('name', 'in', list(to_update_modules)),
                         ('state', 'in', ('uninstalled', 'to_install'))]
                    ).button_immediate_upgrade()

    @http.route(
        '/saas/client/db/restore',
        type='http',
        auth="none",
        methods=['POST'],
        csrf=False)
    @require_saas_token
    def client_db_restore(self, db=None, backup_file=None,
                          copy=False, **params):
        if not db:
            raise werkzeug.exceptions.BadRequest("Database not specified")
        if service_db.exp_db_exist(db):
            raise werkzeug.exceptions.Conflict(
                description="Database %s already exists" % db)
        try:
            with tempfile.NamedTemporaryFile(delete=False) as data_file:
                backup_file.save(data_file)
            service_db.restore_db(db, data_file.name, str2bool(copy))
        except exceptions.AccessDenied as e:
            raise werkzeug.exceptions.Forbidden(
                description=str(e))
        except Exception as e:
            _logger.error("Cannot restore db %s", db, exc_info=True)
            raise werkzeug.exceptions.InternalServerError(
                "Cannot restore db (%s): %s" % (db, str(e)))
        else:
            self._postprocess_restored_db(db)
            return http.Response('OK', status=200)
        finally:
            os.unlink(data_file.name)

    @http.route(
        '/saas/client/db/configure/base_url',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_configure_base_url(self, db=None, base_url=None, **params):
        if not base_url:
            raise werkzeug.exceptions.BadRequest(
                description='Base URL not provided!')

        # TODO: it seems that this url have no sense
        m = re.match(
            r"(?:(?:http|https)://)?"
            r"(?P<host>([\w\d-]+\.?)+[\w\d-]+)(?:.*)?",
            base_url)
        if not m:
            raise werkzeug.exceptions.BadRequest(
                description='Wrong base URL')

        hostname = m.groupdict()['host']
        with registry(db).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, context={})
            env['ir.config_parameter'].set_param(
                'web.base.url', base_url)
            env['ir.config_parameter'].set_param(
                'mail.catchall.domain', hostname)
        return http.Response('OK', status=200)

    @http.route(
        '/saas/client/db/configure/mail',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_configure_mail(self, incoming, outgoing, db=None,
                                 test_and_confirm=False, **params):
        """ Configure mail servers for database

            :param dict incoming: dict with config of incoming mail server
            :param dict outgoing: dict with config of outgoing mail server
            :param bool test_and_confirm: if set to True, test if odoo can
                                          use specified mail servers

            :return: 200 OK if everythning is ok.
                     in case of errors, 500 code will be returned

            Required params for incoming mail server:
                - host
                - user
                - password

            Required params for outgoing mail server:
                - host
                - user
                - password
        """
        test_and_confirm = str2bool(test_and_confirm)
        incoming = json.loads(incoming)
        outgoing = json.loads(outgoing)
        incoming_data = {
            'name': 'Yodoo Incoming Mail',
            'type': 'imap',
            'is_ssl': True,
            'port': 993,
            'server': incoming['host'],
            'user': incoming['user'],
            'password': incoming['password'],
            'active': incoming.get('active', True),
            'state': 'draft',
        }

        outgoing_data = {
            'name': 'Yodoo Outgoing Mail',
            'smtp_encryption': 'starttls',
            'smtp_port': 587,
            'smtp_host': outgoing['host'],
            'smtp_user': outgoing['user'],
            'smtp_pass': outgoing['password'],
            'active': outgoing.get('active', True),
        }
        with registry(db).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, context={})
            incoming_srv = env.ref(
                'yodoo_client.yodoo_incoming_mail',
                raise_if_not_found=False)
            if incoming_srv:
                incoming_srv.write(incoming_data)
            else:
                incoming_srv = env['fetchmail.server'].create(incoming_data)
                env['ir.model.data'].create({
                    'name': 'yodoo_incoming_mail',
                    'module': 'yodoo_client',
                    'model': incoming_srv._name,
                    'res_id': incoming_srv.id,
                    'noupdate': True,
                })

            if test_and_confirm:
                incoming_srv.button_confirm_login()
                if incoming_srv.state != 'done':
                    raise werkzeug.exceptions.InternalServerError(
                        "Cannot configure incoming mail server")

            outgoing_srv = env.ref(
                'yodoo_client.yodoo_outgoing_mail',
                raise_if_not_found=False)
            if outgoing_srv:
                outgoing_srv.write(outgoing_data)
            else:
                outgoing_srv = env['ir.mail_server'].create(outgoing_data)
                env['ir.model.data'].create({
                    'name': 'yodoo_outgoing_mail',
                    'module': 'yodoo_client',
                    'model': outgoing_srv._name,
                    'res_id': outgoing_srv.id,
                    'noupdate': True,
                })

            if test_and_confirm:
                try:
                    smtp = outgoing_srv.connect(mail_server_id=outgoing_srv.id)
                except Exception:
                    _logger.error(
                        "Cannot configure outgoing mail server", exc_info=True)
                    raise werkzeug.exceptions.InternalServerError(
                        "Cannot configure outgoing mail server")
                finally:
                    try:
                        if smtp:
                            smtp.quit()
                    except Exception:  # pylint: disable=except-pass
                        # ignored, just a consequence of the previous exception
                        pass
        return http.Response('OK', status=200)

    @http.route(
        '/saas/client/db/configure/mail/delete',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False,
    )
    @require_saas_token
    @require_db_param
    def client_db_configure_mail_delete(self, db=None, **params):
        with registry(db).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, context={})
            incoming_srv = env.ref(
                'yodoo_client.yodoo_incoming_mail',
                raise_if_not_found=False)
            if incoming_srv:
                incoming_srv.unlink()

            outgoing_srv = env.ref(
                'yodoo_client.yodoo_outgoing_mail',
                raise_if_not_found=False)
            if outgoing_srv:
                outgoing_srv.unlink()
        return http.Response('OK', status=200)

    @http.route(
        '/saas/client/db/stat',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_statistic(self, db=None, **params):
        data = prepare_db_statistic_data(db)
        return Response(json.dumps(data), status=200)
