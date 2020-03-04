import os
import time
import json
import shutil
import logging
import tempfile

import werkzeug

import odoo
from odoo import http, exceptions

_logger = logging.getLogger(__name__)


class YodooEasyBackup(http.Controller):

    def _yodoo_easy_backup_manifest(self, cr):
        """ Just copy of odoo.service.db.dump_db_manifest
            implemented here to avoid access error if db_list is False
        """
        pg_version = "%d.%d" % divmod(
            cr._obj.connection.server_version / 100, 100)
        cr.execute("""
            select name, latest_version
            from ir_module_module
            where state = 'installed';
        """)
        modules = dict(cr.fetchall())
        manifest = {
            'odoo_dump': '1',
            'db_name': cr.dbname,
            'version': odoo.release.version,
            'version_info': odoo.release.version_info,
            'major_version': odoo.release.major_version,
            'pg_version': pg_version,
            'modules': modules,
        }
        return manifest

    def _yodoo_easy_backup_dump(self, db_name, stream, backup_format='zip'):
        """ Just copy of odoo.service.db.dump_db
            implemented here to avoid access error if db_list is False

            Dump database `db` into file-like object `stream` if stream is None
            return a file object with the dump
        """

        _logger.info('DUMP DB: %s format %s', db_name, backup_format)

        cmd = ['pg_dump', '--no-owner']
        cmd.append(db_name)

        if backup_format == 'zip':
            with odoo.tools.osutil.tempdir() as dump_dir:
                filestore = odoo.tools.config.filestore(db_name)
                if os.path.exists(filestore):
                    shutil.copytree(
                        filestore, os.path.join(dump_dir, 'filestore'))
                with open(os.path.join(dump_dir, 'manifest.json'), 'w') as fh:
                    db = odoo.sql_db.db_connect(db_name)
                    with db.cursor() as cr:
                        json.dump(
                            self._yodoo_easy_backup_manifest(cr), fh, indent=4)
                cmd.insert(-1, '--file=' + os.path.join(dump_dir, 'dump.sql'))
                odoo.tools.exec_pg_command(*cmd)
                if stream:
                    odoo.tools.osutil.zip_dir(
                        dump_dir, stream, include_dir=False,
                        fnct_sort=lambda file_name: file_name != 'dump.sql')
                else:
                    t = tempfile.TemporaryFile()
                    odoo.tools.osutil.zip_dir(
                        dump_dir, t, include_dir=False,
                        fnct_sort=lambda file_name: file_name != 'dump.sql')
                    t.seek(0)
                    return t
        else:
            cmd.insert(-1, '--format=c')
            __, stdout = odoo.tools.exec_pg_command_pipe(*cmd)
            if stream:
                shutil.copyfileobj(stdout, stream)
            else:
                return stdout

    @http.route(
        '/yodoo_easy_backup/<token>',
        type='http',
        auth="public",
        methods=['GET'],
        csrf=True)
    def yodoo_easy_backu(self, token, **params):
        Param = http.request.env['ir.config_parameter'].sudo()
        allow_public = Param.get_param(
            'yodoo_easy_backup.backup_allow_public', False)
        if not (allow_public or http.request.env.user._is_system()):
            raise werkzeug.exceptions.Forbidden()

        backup_token = Param.get_param(
            'yodoo_easy_backup.backup_token', False)

        if not backup_token:
            raise werkzeug.exceptions.Forbidden(
                description="Easy backup for this database is disabled!")

        if backup_token != token:
            raise werkzeug.exceptions.Forbidden()

        backup_format = 'zip'
        filename = "%s-%s.%s" % (
            http.request.env.cr.dbname,
            time.strftime('%Y-%m-%d--%H-%M-%S'),
            backup_format)
        headers = [
            ('Content-Type', 'application/octet-stream; charset=binary'),
            ('Content-Disposition', http.content_disposition(filename)),
        ]

        try:
            stream = tempfile.TemporaryFile()
            self._yodoo_easy_backup_dump(
                http.request.env.cr.dbname, stream, backup_format)
        except exceptions.AccessDenied as e:
            _logger.error(
                "Cannot backup db %s",
                http.request.env.cr.dbname, exc_info=True)
            raise werkzeug.exceptions.Forbidden(
                description=str(e))
        except Exception as e:
            _logger.error(
                "Cannot backup db %s",
                http.request.env.cr.dbname, exc_info=True)
            raise werkzeug.exceptions.InternalServerError(
                description=str(e))
        else:
            stream.seek(0)
            response = werkzeug.wrappers.Response(
                stream,
                headers=headers,
                direct_passthrough=True)
            return response
