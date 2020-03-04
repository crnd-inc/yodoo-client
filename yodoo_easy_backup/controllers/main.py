import time
import logging
import tempfile

import werkzeug

from odoo import http, exceptions, tools
from odoo.service.db import dump_db

_logger = logging.getLogger(__name__)


class SAASClientDb(http.Controller):

    @http.route(
        '/yodoo_easy_backup/<token>',
        type='http',
        auth="public",
        methods=['GET'],
        csrf=True)
    def yodoo_easy_install(self, token, **params):
        Param = http.request.env['ir.config_parameter'].sudo()
        allow_public = Param.get_param(
            'yodoo_easy_backup.backup_allow_public', False)
        if not (allow_public or http.request.env.user._is_system()):
            raise werkzeug.exceptions.Forbidden()

        backup_token = Param.get_param(
            'yodoo_easy_backup.backup_token', False)

        if not backup_token:
            raise werkzeug.exceptions.Forbidden(
                description="Easy backup for this database disabled!")

        if backup_token != token:
            raise werkzeug.exceptions.Forbidden()

        backup_format = 'zip'
        filename = "%s-%s.%s" % (
            http.request.env.cr.dbname,
            time.strftime('%Y-%m-%d.%H:%M:%S'),
            backup_format)
        headers = [
            ('Content-Type', 'application/octet-stream; charset=binary'),
            ('Content-Disposition', http.content_disposition(filename)),
        ]

        old_list_db = tools.config['list_db']
        try:
            stream = tempfile.TemporaryFile()
            tools.config['list_db'] = True
            dump_db(http.request.env.cr.dbname, stream, backup_format)
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
        finally:
            tools.config['list_db'] = old_list_db
